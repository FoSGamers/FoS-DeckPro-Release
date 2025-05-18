from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
import threading
import time
import logging
import json
from pathlib import Path
import psutil
import signal
import sys
import os
import subprocess
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class ProcessState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    TERMINATED = "terminated"

class ProcessPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ProcessInfo:
    pid: int
    name: str
    state: ProcessState
    priority: ProcessPriority
    start_time: datetime
    cpu_percent: float
    memory_percent: float
    command: str
    arguments: List[str]
    working_dir: str
    environment: Dict[str, str]
    parent_pid: Optional[int] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None

class ProcessManager(QObject):
    process_started = Signal(ProcessInfo)  # process_info
    process_stopped = Signal(ProcessInfo)  # process_info
    process_error = Signal(ProcessInfo)  # process_info
    process_state_changed = Signal(ProcessInfo, ProcessState)  # process_info, new_state
    
    def __init__(self):
        super().__init__()
        self.log_dir = Path("logs")
        self.process_log = self.log_dir / "process.log"
        
        # Process tracking
        self.processes: Dict[int, ProcessInfo] = {}
        self.process_history: List[ProcessInfo] = []
        self.process_queue = queue.PriorityQueue()
        
        # Process settings
        self.max_processes = 10
        self.process_timeout = 300  # 5 minutes
        self.cleanup_interval = 60  # 1 minute
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._start_process_monitoring()
        self._start_process_cleanup()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("process")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        self.log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(self.process_log)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.log_dir.mkdir(exist_ok=True)
        
    def _start_process_monitoring(self):
        """Start process monitoring"""
        def monitor():
            while True:
                self._check_processes()
                time.sleep(1)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def _start_process_cleanup(self):
        """Start process cleanup"""
        def cleanup():
            while True:
                self._cleanup_processes()
                time.sleep(self.cleanup_interval)
                
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()
        
    def start_process(self, command: str, arguments: List[str] = None,
                     working_dir: str = None, environment: Dict[str, str] = None,
                     priority: ProcessPriority = ProcessPriority.NORMAL) -> Optional[int]:
        """Start a new process"""
        try:
            # Create process
            process = subprocess.Popen(
                [command] + (arguments or []),
                cwd=working_dir,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Create process info
            process_info = ProcessInfo(
                pid=process.pid,
                name=command,
                state=ProcessState.INITIALIZING,
                priority=priority,
                start_time=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                command=command,
                arguments=arguments or [],
                working_dir=working_dir or os.getcwd(),
                environment=environment or {},
                parent_pid=os.getpid()
            )
            
            # Add to tracking
            self.processes[process.pid] = process_info
            self.process_history.append(process_info)
            
            # Emit signal
            self.process_started.emit(process_info)
            
            return process.pid
            
        except Exception as e:
            self.logger.error(f"Error starting process: {e}")
            return None
            
    def stop_process(self, pid: int, force: bool = False) -> bool:
        """Stop a process"""
        try:
            if pid in self.processes:
                process_info = self.processes[pid]
                
                # Get process
                process = psutil.Process(pid)
                
                # Stop process
                if force:
                    process.kill()
                else:
                    process.terminate()
                    
                # Update process info
                process_info.state = ProcessState.STOPPED
                process_info.exit_code = process.wait()
                
                # Emit signal
                self.process_stopped.emit(process_info)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error stopping process: {e}")
            
        return False
        
    def pause_process(self, pid: int) -> bool:
        """Pause a process"""
        try:
            if pid in self.processes:
                process_info = self.processes[pid]
                
                # Get process
                process = psutil.Process(pid)
                
                # Pause process
                process.suspend()
                
                # Update process info
                process_info.state = ProcessState.PAUSED
                
                # Emit signal
                self.process_state_changed.emit(process_info, ProcessState.PAUSED)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error pausing process: {e}")
            
        return False
        
    def resume_process(self, pid: int) -> bool:
        """Resume a process"""
        try:
            if pid in self.processes:
                process_info = self.processes[pid]
                
                # Get process
                process = psutil.Process(pid)
                
                # Resume process
                process.resume()
                
                # Update process info
                process_info.state = ProcessState.RUNNING
                
                # Emit signal
                self.process_state_changed.emit(process_info, ProcessState.RUNNING)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error resuming process: {e}")
            
        return False
        
    def _check_processes(self):
        """Check running processes"""
        try:
            for pid, process_info in list(self.processes.items()):
                try:
                    # Get process
                    process = psutil.Process(pid)
                    
                    # Update process info
                    process_info.cpu_percent = process.cpu_percent()
                    process_info.memory_percent = process.memory_percent()
                    
                    # Check if process is still running
                    if process.status() == psutil.STATUS_ZOMBIE:
                        process_info.state = ProcessState.TERMINATED
                        process_info.exit_code = process.wait()
                        self.process_stopped.emit(process_info)
                        
                except psutil.NoSuchProcess:
                    process_info.state = ProcessState.TERMINATED
                    self.process_stopped.emit(process_info)
                    
        except Exception as e:
            self.logger.error(f"Error checking processes: {e}")
            
    def _cleanup_processes(self):
        """Clean up terminated processes"""
        try:
            for pid, process_info in list(self.processes.items()):
                if process_info.state in [ProcessState.TERMINATED, ProcessState.STOPPED]:
                    del self.processes[pid]
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up processes: {e}")
            
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get process information"""
        return self.processes.get(pid)
        
    def get_process_list(self) -> List[ProcessInfo]:
        """Get list of all processes"""
        return list(self.processes.values())
        
    def get_process_history(self) -> List[ProcessInfo]:
        """Get process history"""
        return self.process_history
        
    def set_process_priority(self, pid: int, priority: ProcessPriority) -> bool:
        """Set process priority"""
        try:
            if pid in self.processes:
                process_info = self.processes[pid]
                
                # Get process
                process = psutil.Process(pid)
                
                # Set priority
                if priority == ProcessPriority.LOW:
                    process.nice(10)
                elif priority == ProcessPriority.NORMAL:
                    process.nice(0)
                elif priority == ProcessPriority.HIGH:
                    process.nice(-10)
                elif priority == ProcessPriority.CRITICAL:
                    process.nice(-20)
                    
                # Update process info
                process_info.priority = priority
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting process priority: {e}")
            
        return False 