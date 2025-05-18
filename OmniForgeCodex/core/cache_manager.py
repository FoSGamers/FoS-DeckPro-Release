from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
import threading
import time
import logging
import json
from pathlib import Path
import hashlib
import pickle
import zlib
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor
import psutil
import signal
import sys
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class CacheType(Enum):
    MEMORY = "memory"
    DISK = "disk"
    DISTRIBUTED = "distributed"

class CachePolicy(Enum):
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"   # Time To Live

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size: int
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

class CacheManager(QObject):
    cache_updated = Signal(str, Any)  # key, value
    cache_cleared = Signal()
    cache_error = Signal(str, str)  # key, error_message
    
    def __init__(self):
        super().__init__()
        self.cache_dir = Path("cache")
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.disk_cache: Dict[str, CacheEntry] = {}
        self.distributed_cache: Dict[str, CacheEntry] = {}
        
        # Cache settings
        self.max_memory_size = 100 * 1024 * 1024  # 100MB
        self.max_disk_size = 1024 * 1024 * 1024  # 1GB
        self.default_ttl = timedelta(hours=1)
        self.cleanup_interval = 300  # 5 minutes
        
        # Cache policies
        self.memory_policy = CachePolicy.LRU
        self.disk_policy = CachePolicy.TTL
        self.distributed_policy = CachePolicy.LFU
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._load_cache()
        self._start_cleanup_timer()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("cache")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "cache.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup cache directories"""
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "memory").mkdir(exist_ok=True)
        (self.cache_dir / "disk").mkdir(exist_ok=True)
        (self.cache_dir / "distributed").mkdir(exist_ok=True)
        
    def _load_cache(self):
        """Load cache from disk"""
        try:
            # Load memory cache
            memory_cache_file = self.cache_dir / "memory" / "cache.json"
            if memory_cache_file.exists():
                with open(memory_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    for key, entry_data in cache_data.items():
                        entry = self._create_entry_from_data(entry_data)
                        self.memory_cache[key] = entry
                        
            # Load disk cache
            disk_cache_file = self.cache_dir / "disk" / "cache.json"
            if disk_cache_file.exists():
                with open(disk_cache_file, 'r') as f:
                    cache_data = json.load(f)
                    for key, entry_data in cache_data.items():
                        entry = self._create_entry_from_data(entry_data)
                        self.disk_cache[key] = entry
                        
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            
    def _save_cache(self):
        """Save cache to disk"""
        try:
            # Save memory cache
            memory_cache_file = self.cache_dir / "memory" / "cache.json"
            cache_data = {}
            for key, entry in self.memory_cache.items():
                cache_data[key] = self._create_data_from_entry(entry)
            with open(memory_cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            # Save disk cache
            disk_cache_file = self.cache_dir / "disk" / "cache.json"
            cache_data = {}
            for key, entry in self.disk_cache.items():
                cache_data[key] = self._create_data_from_entry(entry)
            with open(disk_cache_file, 'w') as f:
                json.dump(cache_data, f)
                
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
            
    def _start_cleanup_timer(self):
        """Start cache cleanup timer"""
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._cleanup_cache)
        self.cleanup_timer.start(self.cleanup_interval * 1000)
        
    def get(self, key: str, cache_type: CacheType = CacheType.MEMORY) -> Optional[Any]:
        """Get value from cache"""
        try:
            if cache_type == CacheType.MEMORY:
                entry = self.memory_cache.get(key)
            elif cache_type == CacheType.DISK:
                entry = self.disk_cache.get(key)
            else:
                entry = self.distributed_cache.get(key)
                
            if entry:
                # Check if expired
                if entry.expires_at and datetime.now() > entry.expires_at:
                    self.delete(key, cache_type)
                    return None
                    
                # Update access info
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                
                return entry.value
                
        except Exception as e:
            self.logger.error(f"Error getting from cache: {e}")
            self.cache_error.emit(key, str(e))
            
        return None
        
    def set(self, key: str, value: Any, cache_type: CacheType = CacheType.MEMORY,
            ttl: Optional[timedelta] = None, metadata: Dict[str, Any] = None) -> bool:
        """Set value in cache"""
        try:
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=0,
                size=self._get_value_size(value),
                expires_at=datetime.now() + (ttl or self.default_ttl),
                metadata=metadata or {}
            )
            
            # Store in appropriate cache
            if cache_type == CacheType.MEMORY:
                self._store_in_memory(key, entry)
            elif cache_type == CacheType.DISK:
                self._store_in_disk(key, entry)
            else:
                self._store_in_distributed(key, entry)
                
            # Emit signal
            self.cache_updated.emit(key, value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache: {e}")
            self.cache_error.emit(key, str(e))
            return False
            
    def delete(self, key: str, cache_type: CacheType = CacheType.MEMORY) -> bool:
        """Delete value from cache"""
        try:
            if cache_type == CacheType.MEMORY:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            elif cache_type == CacheType.DISK:
                if key in self.disk_cache:
                    del self.disk_cache[key]
            else:
                if key in self.distributed_cache:
                    del self.distributed_cache[key]
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting from cache: {e}")
            self.cache_error.emit(key, str(e))
            return False
            
    def clear(self, cache_type: CacheType = None):
        """Clear cache"""
        try:
            if cache_type == CacheType.MEMORY or cache_type is None:
                self.memory_cache.clear()
            if cache_type == CacheType.DISK or cache_type is None:
                self.disk_cache.clear()
            if cache_type == CacheType.DISTRIBUTED or cache_type is None:
                self.distributed_cache.clear()
                
            self.cache_cleared.emit()
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            
    def _cleanup_cache(self):
        """Clean up expired and oversized cache entries"""
        try:
            # Clean memory cache
            self._cleanup_memory_cache()
            
            # Clean disk cache
            self._cleanup_disk_cache()
            
            # Clean distributed cache
            self._cleanup_distributed_cache()
            
        except Exception as e:
            self.logger.error(f"Error cleaning cache: {e}")
            
    def _cleanup_memory_cache(self):
        """Clean up memory cache"""
        current_time = datetime.now()
        total_size = 0
        
        # Remove expired entries
        expired_keys = []
        for key, entry in self.memory_cache.items():
            if entry.expires_at and current_time > entry.expires_at:
                expired_keys.append(key)
            else:
                total_size += entry.size
                
        for key in expired_keys:
            del self.memory_cache[key]
            
        # Remove entries if over size limit
        if total_size > self.max_memory_size:
            if self.memory_policy == CachePolicy.LRU:
                self._remove_lru_entries(self.memory_cache, total_size - self.max_memory_size)
            elif self.memory_policy == CachePolicy.LFU:
                self._remove_lfu_entries(self.memory_cache, total_size - self.max_memory_size)
            else:
                self._remove_fifo_entries(self.memory_cache, total_size - self.max_memory_size)
                
    def _cleanup_disk_cache(self):
        """Clean up disk cache"""
        current_time = datetime.now()
        total_size = 0
        
        # Remove expired entries
        expired_keys = []
        for key, entry in self.disk_cache.items():
            if entry.expires_at and current_time > entry.expires_at:
                expired_keys.append(key)
            else:
                total_size += entry.size
                
        for key in expired_keys:
            del self.disk_cache[key]
            
        # Remove entries if over size limit
        if total_size > self.max_disk_size:
            if self.disk_policy == CachePolicy.LRU:
                self._remove_lru_entries(self.disk_cache, total_size - self.max_disk_size)
            elif self.disk_policy == CachePolicy.LFU:
                self._remove_lfu_entries(self.disk_cache, total_size - self.max_disk_size)
            else:
                self._remove_fifo_entries(self.disk_cache, total_size - self.max_disk_size)
                
    def _cleanup_distributed_cache(self):
        """Clean up distributed cache"""
        current_time = datetime.now()
        
        # Remove expired entries
        expired_keys = []
        for key, entry in self.distributed_cache.items():
            if entry.expires_at and current_time > entry.expires_at:
                expired_keys.append(key)
                
        for key in expired_keys:
            del self.distributed_cache[key]
            
    def _remove_lru_entries(self, cache: Dict[str, CacheEntry], size_to_remove: int):
        """Remove least recently used entries"""
        entries = sorted(cache.items(), key=lambda x: x[1].last_accessed)
        removed_size = 0
        
        for key, entry in entries:
            if removed_size >= size_to_remove:
                break
            del cache[key]
            removed_size += entry.size
            
    def _remove_lfu_entries(self, cache: Dict[str, CacheEntry], size_to_remove: int):
        """Remove least frequently used entries"""
        entries = sorted(cache.items(), key=lambda x: x[1].access_count)
        removed_size = 0
        
        for key, entry in entries:
            if removed_size >= size_to_remove:
                break
            del cache[key]
            removed_size += entry.size
            
    def _remove_fifo_entries(self, cache: Dict[str, CacheEntry], size_to_remove: int):
        """Remove first in first out entries"""
        entries = sorted(cache.items(), key=lambda x: x[1].created_at)
        removed_size = 0
        
        for key, entry in entries:
            if removed_size >= size_to_remove:
                break
            del cache[key]
            removed_size += entry.size
            
    def _get_value_size(self, value: Any) -> int:
        """Get size of value in bytes"""
        try:
            return len(pickle.dumps(value))
        except:
            return sys.getsizeof(value)
            
    def _create_entry_from_data(self, data: Dict[str, Any]) -> CacheEntry:
        """Create cache entry from saved data"""
        return CacheEntry(
            key=data["key"],
            value=data["value"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            size=data["size"],
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            metadata=data["metadata"]
        )
        
    def _create_data_from_entry(self, entry: CacheEntry) -> Dict[str, Any]:
        """Create data from cache entry"""
        return {
            "key": entry.key,
            "value": entry.value,
            "created_at": entry.created_at.isoformat(),
            "last_accessed": entry.last_accessed.isoformat(),
            "access_count": entry.access_count,
            "size": entry.size,
            "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
            "metadata": entry.metadata
        } 