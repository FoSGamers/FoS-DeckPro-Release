from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
import threading
import time
import logging
import json
from pathlib import Path
import psutil
import gc
import sys
import tracemalloc
import weakref
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor
import signal
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class MemoryThreshold(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MemoryUsage:
    total: int
    used: int
    free: int
    percent: float
    timestamp: datetime

@dataclass
class MemoryLeak:
    object_id: int
    object_type: str
    size: int
    reference_count: int
    creation_time: datetime
    stack_trace: str

class MemoryManager(QObject):
    memory_warning = Signal(MemoryThreshold)  # threshold
    memory_leak_detected = Signal(MemoryLeak)  # leak_info
    memory_optimized = Signal()  # optimization_complete
    
    def __init__(self):
        super().__init__()
        self.log_dir = Path("logs")
        self.memory_log = self.log_dir / "memory.log"
        
        # Memory thresholds
        self.thresholds = {
            MemoryThreshold.LOW: 0.5,      # 50%
            MemoryThreshold.MEDIUM: 0.7,   # 70%
            MemoryThreshold.HIGH: 0.85,    # 85%
            MemoryThreshold.CRITICAL: 0.95 # 95%
        }
        
        # Memory monitoring
        self.monitor_interval = 60  # 1 minute
        self.optimization_interval = 300  # 5 minutes
        self.leak_detection_interval = 600  # 10 minutes
        
        # Memory tracking
        self.memory_history: List[MemoryUsage] = []
        self.memory_leaks: List[MemoryLeak] = []
        self.object_tracker: Dict[int, Any] = {}
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._start_memory_monitoring()
        self._start_memory_optimization()
        self._start_leak_detection()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("memory")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        self.log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(self.memory_log)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.log_dir.mkdir(exist_ok=True)
        
    def _start_memory_monitoring(self):
        """Start memory monitoring"""
        def monitor():
            while True:
                self._check_memory_usage()
                time.sleep(self.monitor_interval)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def _start_memory_optimization(self):
        """Start memory optimization"""
        def optimize():
            while True:
                self._optimize_memory()
                time.sleep(self.optimization_interval)
                
        self.optimization_thread = threading.Thread(target=optimize, daemon=True)
        self.optimization_thread.start()
        
    def _start_leak_detection(self):
        """Start memory leak detection"""
        def detect():
            while True:
                self._detect_memory_leaks()
                time.sleep(self.leak_detection_interval)
                
        self.leak_detection_thread = threading.Thread(target=detect, daemon=True)
        self.leak_detection_thread.start()
        
    def _check_memory_usage(self):
        """Check current memory usage"""
        try:
            memory = psutil.virtual_memory()
            usage = MemoryUsage(
                total=memory.total,
                used=memory.used,
                free=memory.free,
                percent=memory.percent,
                timestamp=datetime.now()
            )
            
            self.memory_history.append(usage)
            self._log_memory_usage(usage)
            
            # Check thresholds
            for threshold, value in self.thresholds.items():
                if memory.percent >= value * 100:
                    self.memory_warning.emit(threshold)
                    break
                    
        except Exception as e:
            self.logger.error(f"Error checking memory usage: {e}")
            
    def _optimize_memory(self):
        """Optimize memory usage"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clear memory caches
            self._clear_memory_caches()
            
            # Optimize memory allocation
            self._optimize_memory_allocation()
            
            # Emit signal
            self.memory_optimized.emit()
            
        except Exception as e:
            self.logger.error(f"Error optimizing memory: {e}")
            
    def _detect_memory_leaks(self):
        """Detect memory leaks"""
        try:
            # Start memory tracking
            tracemalloc.start()
            
            # Take snapshot
            snapshot = tracemalloc.take_snapshot()
            
            # Analyze snapshot
            for stat in snapshot.statistics('lineno'):
                if stat.count > 1:  # Potential leak
                    leak = MemoryLeak(
                        object_id=id(stat.traceback),
                        object_type=str(stat.traceback),
                        size=stat.size,
                        reference_count=stat.count,
                        creation_time=datetime.now(),
                        stack_trace=str(stat.traceback)
                    )
                    
                    self.memory_leaks.append(leak)
                    self.memory_leak_detected.emit(leak)
                    
            # Stop memory tracking
            tracemalloc.stop()
            
        except Exception as e:
            self.logger.error(f"Error detecting memory leaks: {e}")
            
    def _clear_memory_caches(self):
        """Clear memory caches"""
        try:
            # Clear Python's internal caches
            gc.collect()
            
            # Clear application caches
            if hasattr(self, 'cache_manager'):
                self.cache_manager.clear(CacheType.MEMORY)
                
        except Exception as e:
            self.logger.error(f"Error clearing memory caches: {e}")
            
    def _optimize_memory_allocation(self):
        """Optimize memory allocation"""
        try:
            # Get current memory usage
            memory = psutil.virtual_memory()
            
            # If memory usage is high, try to free some memory
            if memory.percent > self.thresholds[MemoryThreshold.HIGH] * 100:
                # Force garbage collection
                gc.collect()
                
                # Clear memory caches
                self._clear_memory_caches()
                
                # Reduce memory usage of large objects
                self._reduce_large_object_memory()
                
        except Exception as e:
            self.logger.error(f"Error optimizing memory allocation: {e}")
            
    def _reduce_large_object_memory(self):
        """Reduce memory usage of large objects"""
        try:
            # Get list of large objects
            large_objects = []
            for obj in gc.get_objects():
                try:
                    if sys.getsizeof(obj) > 1024 * 1024:  # 1MB
                        large_objects.append(obj)
                except:
                    continue
                    
            # Try to reduce memory usage
            for obj in large_objects:
                if hasattr(obj, 'clear'):
                    obj.clear()
                elif hasattr(obj, 'close'):
                    obj.close()
                    
        except Exception as e:
            self.logger.error(f"Error reducing large object memory: {e}")
            
    def _log_memory_usage(self, usage: MemoryUsage):
        """Log memory usage"""
        try:
            log_entry = {
                "timestamp": usage.timestamp.isoformat(),
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }
            
            with open(self.memory_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error logging memory usage: {e}")
            
    def get_memory_usage(self) -> MemoryUsage:
        """Get current memory usage"""
        memory = psutil.virtual_memory()
        return MemoryUsage(
            total=memory.total,
            used=memory.used,
            free=memory.free,
            percent=memory.percent,
            timestamp=datetime.now()
        )
        
    def get_memory_history(self) -> List[MemoryUsage]:
        """Get memory usage history"""
        return self.memory_history
        
    def get_memory_leaks(self) -> List[MemoryLeak]:
        """Get detected memory leaks"""
        return self.memory_leaks
        
    def set_memory_threshold(self, threshold: MemoryThreshold, value: float):
        """Set memory threshold"""
        if 0 <= value <= 1:
            self.thresholds[threshold] = value
            
    def get_memory_threshold(self, threshold: MemoryThreshold) -> float:
        """Get memory threshold"""
        return self.thresholds[threshold]
        
    def register_object(self, obj: Any):
        """Register object for memory tracking"""
        self.object_tracker[id(obj)] = weakref.ref(obj)
        
    def unregister_object(self, obj: Any):
        """Unregister object from memory tracking"""
        if id(obj) in self.object_tracker:
            del self.object_tracker[id(obj)] 