from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from pathlib import Path
import json
import shutil
import zipfile
import logging
import threading
from datetime import datetime, timedelta
import hashlib
import os
import tempfile
import yaml
import jsonschema
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil
import sqlite3
import tarfile
import gzip
import bz2
import lzma
from concurrent.futures import ThreadPoolExecutor
import schedule
import time
import uuid
import queue
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"

class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    RESTORED = "restored"

@dataclass
class BackupInfo:
    id: str
    type: BackupType
    status: BackupStatus
    timestamp: datetime
    size: int
    checksum: str
    source_path: Path
    backup_path: Path
    metadata: Dict[str, Any]
    error_message: Optional[str] = None

class BackupManager(QObject):
    backup_started = Signal(BackupInfo)  # backup_info
    backup_completed = Signal(BackupInfo)  # backup_info
    backup_failed = Signal(str, str)  # backup_id, error_message
    restore_started = Signal(BackupInfo)  # backup_info
    restore_completed = Signal(BackupInfo)  # backup_info
    restore_failed = Signal(str, str)  # backup_id, error_message
    
    def __init__(self):
        super().__init__()
        self.backup_dir = Path("backups")
        self.config_dir = Path("config") / "backups"
        self.backups: Dict[str, BackupInfo] = {}
        self.backup_queue = queue.PriorityQueue()
        self.restore_queue = queue.PriorityQueue()
        
        # Backup settings
        self.max_backups = 10
        self.backup_interval = timedelta(hours=24)
        self.retention_period = timedelta(days=30)
        self.compression_level = 9
        self.verify_backups = True
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._load_backups()
        self._start_backup_processor()
        self._start_restore_processor()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("backup")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "backups.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.backup_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
    def _load_backups(self):
        """Load backup information"""
        try:
            # Load backup configurations
            for config_file in self.config_dir.glob("*.json"):
                with open(config_file, 'r') as f:
                    backup_data = json.load(f)
                    backup_info = self._create_backup_info(backup_data)
                    self.backups[backup_info.id] = backup_info
                    
        except Exception as e:
            self.logger.error(f"Error loading backups: {e}")
            
    def _start_backup_processor(self):
        """Start backup processing thread"""
        def process_backups():
            while True:
                try:
                    backup_id = self.backup_queue.get()
                    self._process_backup(backup_id)
                    self.backup_queue.task_done()
                except Exception as e:
                    self.logger.error(f"Error processing backup: {e}")
                    
        self.backup_thread = threading.Thread(target=process_backups, daemon=True)
        self.backup_thread.start()
        
    def _start_restore_processor(self):
        """Start restore processing thread"""
        def process_restores():
            while True:
                try:
                    backup_id = self.restore_queue.get()
                    self._process_restore(backup_id)
                    self.restore_queue.task_done()
                except Exception as e:
                    self.logger.error(f"Error processing restore: {e}")
                    
        self.restore_thread = threading.Thread(target=process_restores, daemon=True)
        self.restore_thread.start()
        
    def create_backup(self, source_path: Union[str, Path], backup_type: BackupType = BackupType.FULL,
                     metadata: Dict[str, Any] = None) -> Optional[BackupInfo]:
        """Create a new backup"""
        try:
            source_path = Path(source_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Source path not found: {source_path}")
                
            # Create backup info
            backup_id = str(uuid.uuid4())
            backup_info = BackupInfo(
                id=backup_id,
                type=backup_type,
                status=BackupStatus.PENDING,
                timestamp=datetime.now(),
                size=0,
                checksum="",
                source_path=source_path,
                backup_path=self.backup_dir / f"{backup_id}.tar.gz",
                metadata=metadata or {},
                error_message=None
            )
            
            # Add to backups
            self.backups[backup_id] = backup_info
            
            # Save configuration
            self._save_backup_config(backup_info)
            
            # Add to queue
            self.backup_queue.put(backup_id)
            
            # Emit signal
            self.backup_started.emit(backup_info)
            
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return None
            
    def restore_backup(self, backup_id: str, target_path: Optional[Union[str, Path]] = None) -> bool:
        """Restore a backup"""
        try:
            if backup_id not in self.backups:
                raise KeyError(f"Backup not found: {backup_id}")
                
            backup_info = self.backups[backup_id]
            if backup_info.status != BackupStatus.COMPLETED:
                raise ValueError(f"Backup not completed: {backup_id}")
                
            # Update status
            backup_info.status = BackupStatus.IN_PROGRESS
            self._save_backup_config(backup_info)
            
            # Add to queue
            self.restore_queue.put(backup_id)
            
            # Emit signal
            self.restore_started.emit(backup_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            return False
            
    def _process_backup(self, backup_id: str):
        """Process a backup"""
        try:
            backup_info = self.backups[backup_id]
            backup_info.status = BackupStatus.IN_PROGRESS
            self._save_backup_config(backup_info)
            
            # Create backup archive
            with tarfile.open(backup_info.backup_path, f"w:gz", compresslevel=self.compression_level) as tar:
                tar.add(backup_info.source_path, arcname=backup_info.source_path.name)
                
            # Calculate size and checksum
            backup_info.size = backup_info.backup_path.stat().st_size
            backup_info.checksum = self._calculate_checksum(backup_info.backup_path)
            
            # Verify backup if enabled
            if self.verify_backups:
                if not self._verify_backup(backup_info):
                    raise ValueError("Backup verification failed")
                backup_info.status = BackupStatus.VERIFIED
            else:
                backup_info.status = BackupStatus.COMPLETED
                
            # Save configuration
            self._save_backup_config(backup_info)
            
            # Emit signal
            self.backup_completed.emit(backup_info)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            self.logger.error(f"Error processing backup: {e}")
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            self._save_backup_config(backup_info)
            self.backup_failed.emit(backup_id, str(e))
            
    def _process_restore(self, backup_id: str):
        """Process a restore"""
        try:
            backup_info = self.backups[backup_id]
            
            # Extract backup archive
            with tarfile.open(backup_info.backup_path, "r:gz") as tar:
                tar.extractall(path=backup_info.source_path.parent)
                
            # Verify restore
            if not self._verify_restore(backup_info):
                raise ValueError("Restore verification failed")
                
            # Update status
            backup_info.status = BackupStatus.RESTORED
            self._save_backup_config(backup_info)
            
            # Emit signal
            self.restore_completed.emit(backup_info)
            
        except Exception as e:
            self.logger.error(f"Error processing restore: {e}")
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            self._save_backup_config(backup_info)
            self.restore_failed.emit(backup_id, str(e))
            
    def _verify_backup(self, backup_info: BackupInfo) -> bool:
        """Verify a backup"""
        try:
            # Verify archive integrity
            with tarfile.open(backup_info.backup_path, "r:gz") as tar:
                tar.getmembers()
                
            # Verify checksum
            current_checksum = self._calculate_checksum(backup_info.backup_path)
            if current_checksum != backup_info.checksum:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying backup: {e}")
            return False
            
    def _verify_restore(self, backup_info: BackupInfo) -> bool:
        """Verify a restore"""
        try:
            # Verify restored files
            for root, dirs, files in os.walk(backup_info.source_path):
                for file in files:
                    file_path = Path(root) / file
                    if not file_path.exists():
                        return False
                        
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying restore: {e}")
            return False
            
    def _cleanup_old_backups(self):
        """Cleanup old backups"""
        try:
            # Get backups sorted by timestamp
            sorted_backups = sorted(
                self.backups.values(),
                key=lambda x: x.timestamp,
                reverse=True
            )
            
            # Remove excess backups
            for backup_info in sorted_backups[self.max_backups:]:
                self._remove_backup(backup_info.id)
                
            # Remove expired backups
            cutoff_date = datetime.now() - self.retention_period
            for backup_info in sorted_backups:
                if backup_info.timestamp < cutoff_date:
                    self._remove_backup(backup_info.id)
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
            
    def _remove_backup(self, backup_id: str):
        """Remove a backup"""
        try:
            backup_info = self.backups[backup_id]
            
            # Remove backup file
            if backup_info.backup_path.exists():
                backup_info.backup_path.unlink()
                
            # Remove configuration
            config_file = self.config_dir / f"{backup_id}.json"
            if config_file.exists():
                config_file.unlink()
                
            # Remove from backups
            del self.backups[backup_id]
            
        except Exception as e:
            self.logger.error(f"Error removing backup: {e}")
            
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def _create_backup_info(self, backup_data: Dict[str, Any]) -> BackupInfo:
        """Create backup info from data"""
        return BackupInfo(
            id=backup_data["id"],
            type=BackupType(backup_data["type"]),
            status=BackupStatus(backup_data["status"]),
            timestamp=datetime.fromisoformat(backup_data["timestamp"]),
            size=backup_data["size"],
            checksum=backup_data["checksum"],
            source_path=Path(backup_data["source_path"]),
            backup_path=Path(backup_data["backup_path"]),
            metadata=backup_data["metadata"],
            error_message=backup_data.get("error_message")
        )
        
    def _save_backup_config(self, backup_info: BackupInfo):
        """Save backup configuration"""
        config_file = self.config_dir / f"{backup_info.id}.json"
        config_data = {
            "id": backup_info.id,
            "type": backup_info.type.value,
            "status": backup_info.status.value,
            "timestamp": backup_info.timestamp.isoformat(),
            "size": backup_info.size,
            "checksum": backup_info.checksum,
            "source_path": str(backup_info.source_path),
            "backup_path": str(backup_info.backup_path),
            "metadata": backup_info.metadata,
            "error_message": backup_info.error_message
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
            
    def get_backup(self, backup_id: str) -> Optional[BackupInfo]:
        """Get backup info"""
        return self.backups.get(backup_id)
        
    def get_backups(self, backup_type: Optional[BackupType] = None,
                   status: Optional[BackupStatus] = None) -> List[BackupInfo]:
        """Get filtered backups"""
        backups = list(self.backups.values())
        
        if backup_type:
            backups = [b for b in backups if b.type == backup_type]
        if status:
            backups = [b for b in backups if b.status == status]
            
        return backups 