from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
import threading
import time
import logging
import json
from pathlib import Path
import socket
import traceback
import sys
import os
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject, Signal, Slot, QTimer
import pandas as pd
import numpy as np
from collections import defaultdict

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    USER = "user"
    SECURITY = "security"
    PERFORMANCE = "performance"
    NETWORK = "network"
    DATABASE = "database"
    UI = "ui"
    ANALYTICS = "analytics"
    AUDIT = "audit"

@dataclass
class LogEntry:
    id: str
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    source: str
    details: Dict[str, Any]
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class AnalyticsMetric:
    name: str
    value: float
    timestamp: datetime
    category: str
    tags: Dict[str, str]
    metadata: Dict[str, Any]

class LoggingManager(QObject):
    log_entry_added = Signal(LogEntry)  # log_entry
    metric_recorded = Signal(AnalyticsMetric)  # metric
    alert_triggered = Signal(str, LogLevel)  # message, level
    
    def __init__(self):
        super().__init__()
        self.log_dir = Path("logs")
        self.analytics_dir = Path("analytics")
        
        # Logging configuration
        self.log_levels = {
            LogCategory.SYSTEM: LogLevel.INFO,
            LogCategory.APPLICATION: LogLevel.INFO,
            LogCategory.USER: LogLevel.INFO,
            LogCategory.SECURITY: LogLevel.WARNING,
            LogCategory.PERFORMANCE: LogLevel.INFO,
            LogCategory.NETWORK: LogLevel.INFO,
            LogCategory.DATABASE: LogLevel.INFO,
            LogCategory.UI: LogLevel.INFO,
            LogCategory.ANALYTICS: LogLevel.INFO,
            LogCategory.AUDIT: LogLevel.INFO
        }
        
        # Logging tracking
        self.log_entries: List[LogEntry] = []
        self.log_history: Dict[LogCategory, List[LogEntry]] = defaultdict(list)
        self.log_queue = queue.Queue()
        
        # Analytics tracking
        self.metrics: Dict[str, List[AnalyticsMetric]] = defaultdict(list)
        self.metric_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.analytics_queue = queue.Queue()
        
        # Logging settings
        self.max_log_entries = 10000
        self.log_retention = timedelta(days=30)
        self.rotation_size = 10 * 1024 * 1024  # 10MB
        self.compression_enabled = True
        
        # Analytics settings
        self.metrics_retention = timedelta(days=90)
        self.aggregation_interval = 3600  # 1 hour
        self.alert_thresholds = {}
        
        # Thread control
        self._running = True
        self._cleanup_timer = None
        self._log_thread = None
        self._analytics_thread = None
        
        # Setup
        self._setup_directories()
        self._setup_logging()
        self._start_log_processing()
        self._start_analytics_processing()
        self._start_cleanup()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create formatters
        self.file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Setup root logger
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.INFO)
        
        # Add handlers
        self._add_file_handlers()
        self._add_console_handler()
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.log_dir.mkdir(exist_ok=True)
        self.analytics_dir.mkdir(exist_ok=True)
        
    def _add_file_handlers(self):
        """Add file handlers for different categories"""
        for category in LogCategory:
            log_file = self.log_dir / f"{category.value}.log"
            handler = logging.FileHandler(log_file)
            handler.setFormatter(self.file_formatter)
            handler.setLevel(self.log_levels[category].value.upper())
            self.root_logger.addHandler(handler)
            
    def _add_console_handler(self):
        """Add console handler"""
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.console_formatter)
        console_handler.setLevel(logging.INFO)
        self.root_logger.addHandler(console_handler)
        
    def _start_log_processing(self):
        """Start log processing thread"""
        def process_logs():
            while self._running:
                try:
                    entry = self.log_queue.get(timeout=1)  # Add timeout to allow checking _running
                    if not self._running:
                        break
                    self._process_log_entry(entry)
                    self.log_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Error processing log entry: {e}")
                    
        self._log_thread = threading.Thread(target=process_logs, daemon=True)
        self._log_thread.start()
        
    def _start_analytics_processing(self):
        """Start analytics processing thread"""
        def process_analytics():
            while self._running:
                try:
                    metric = self.analytics_queue.get(timeout=1)
                    if not self._running:
                        break
                    self._process_metric(metric)
                    self.analytics_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Error processing analytics: {e}")
                    
        self._analytics_thread = threading.Thread(target=process_analytics, daemon=True)
        self._analytics_thread.start()
        
    def _start_cleanup(self):
        """Start cleanup timer"""
        # Use a regular threading.Timer instead of QTimer
        def cleanup_wrapper():
            self._cleanup_old_data()
            # Schedule next cleanup
            self._cleanup_timer = threading.Timer(3600, cleanup_wrapper)  # 1 hour
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()
        
        self._cleanup_timer = threading.Timer(3600, cleanup_wrapper)
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()
        
    def log(self, level: LogLevel, category: LogCategory, message: str,
            source: str, details: Dict[str, Any] = None, stack_trace: str = None,
            user_id: str = None, session_id: str = None):
        """Log an entry"""
        try:
            # Create log entry
            entry = LogEntry(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                level=level,
                category=category,
                message=message,
                source=source,
                details=details or {},
                stack_trace=stack_trace,
                user_id=user_id,
                session_id=session_id
            )
            
            # Add to queue
            self.log_queue.put(entry)
            
            # Emit signal
            self.log_entry_added.emit(entry)
            
        except Exception as e:
            print(f"Error logging entry: {e}")
            
    def record_metric(self, name: str, value: float, category: str,
                     tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record an analytics metric"""
        try:
            # Create metric
            metric = AnalyticsMetric(
                name=name,
                value=value,
                timestamp=datetime.now(),
                category=category,
                tags=tags or {},
                metadata=metadata or {}
            )
            
            # Add to queue
            self.analytics_queue.put(metric)
            
            # Emit signal
            self.metric_recorded.emit(metric)
            
        except Exception as e:
            print(f"Error recording metric: {e}")
            
    def _process_log_entry(self, entry: LogEntry):
        """Process a log entry"""
        try:
            # Add to in-memory storage
            self.log_entries.append(entry)
            self.log_history[entry.category].append(entry)
            
            # Trim if needed
            if len(self.log_entries) > self.max_log_entries:
                self.log_entries = self.log_entries[-self.max_log_entries:]
            
            # Emit signal in the main thread
            if self._running and hasattr(self, 'log_entry_added'):
                QTimer.singleShot(0, lambda: self.log_entry_added.emit(entry))
            
            # Check for alerts
            self._check_alerts(entry)
            
        except Exception as e:
            print(f"Error processing log entry: {e}")
            
    def _process_metric(self, metric: AnalyticsMetric):
        """Process an analytics metric"""
        try:
            # Add to in-memory storage
            self.metrics[metric.name].append(metric)
            self.metric_history[metric.name].append((metric.timestamp, metric.value))
            
            # Emit signal in the main thread
            if self._running and hasattr(self, 'metric_recorded'):
                QTimer.singleShot(0, lambda: self.metric_recorded.emit(metric))
            
        except Exception as e:
            print(f"Error processing metric: {e}")
            
    def _check_alerts(self, entry: LogEntry):
        """Check for log-based alerts"""
        if entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.alert_triggered.emit(entry.message, entry.level)
            
    def _check_metric_alerts(self, metric: AnalyticsMetric):
        """Check for metric-based alerts"""
        if metric.name in self.alert_thresholds:
            threshold = self.alert_thresholds[metric.name]
            if metric.value >= threshold:
                self.alert_triggered.emit(
                    f"Metric {metric.name} exceeded threshold: {metric.value}",
                    LogLevel.WARNING
                )
                
    def _cleanup_old_data(self):
        """Clean up old log entries and metrics"""
        try:
            # Clean up logs
            cutoff_time = datetime.now() - self.log_retention
            self.log_entries = [
                entry for entry in self.log_entries
                if entry.timestamp > cutoff_time
            ]
            
            for category in self.log_history:
                self.log_history[category] = [
                    entry for entry in self.log_history[category]
                    if entry.timestamp > cutoff_time
                ]
                
            # Clean up metrics
            cutoff_time = datetime.now() - self.metrics_retention
            for name in self.metrics:
                self.metrics[name] = [
                    metric for metric in self.metrics[name]
                    if metric.timestamp > cutoff_time
                ]
                
            for name in self.metric_history:
                self.metric_history[name] = [
                    (timestamp, value) for timestamp, value in self.metric_history[name]
                    if timestamp > cutoff_time
                ]
                
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            
    def get_log_entries(self, category: Optional[LogCategory] = None,
                       level: Optional[LogLevel] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[LogEntry]:
        """Get filtered log entries"""
        entries = self.log_entries
        
        if category:
            entries = [e for e in entries if e.category == category]
        if level:
            entries = [e for e in entries if e.level == level]
        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]
            
        return entries
        
    def get_metrics(self, name: str, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> List[AnalyticsMetric]:
        """Get filtered metrics"""
        metrics = self.metrics.get(name, [])
        
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
            
        return metrics
        
    def get_metric_statistics(self, name: str, start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None) -> Dict[str, float]:
        """Get metric statistics"""
        metrics = self.get_metrics(name, start_time, end_time)
        values = [m.value for m in metrics]
        
        if not values:
            return {}
            
        return {
            "count": len(values),
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "median": np.median(values)
        }
        
    def set_alert_threshold(self, metric_name: str, threshold: float):
        """Set alert threshold for a metric"""
        self.alert_thresholds[metric_name] = threshold
        
    def export_logs(self, format: str = "json", category: Optional[LogCategory] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None) -> str:
        """Export logs in specified format"""
        entries = self.get_log_entries(category, None, start_time, end_time)
        
        if format == "json":
            return json.dumps([{
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "level": e.level.value,
                "category": e.category.value,
                "message": e.message,
                "source": e.source,
                "details": e.details,
                "stack_trace": e.stack_trace,
                "user_id": e.user_id,
                "session_id": e.session_id
            } for e in entries], indent=2)
        elif format == "csv":
            df = pd.DataFrame([{
                "timestamp": e.timestamp,
                "level": e.level.value,
                "category": e.category.value,
                "message": e.message,
                "source": e.source,
                "user_id": e.user_id,
                "session_id": e.session_id
            } for e in entries])
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def export_metrics(self, format: str = "json", name: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> str:
        """Export metrics in specified format"""
        if name:
            metrics = self.get_metrics(name, start_time, end_time)
        else:
            metrics = []
            for name in self.metrics:
                metrics.extend(self.get_metrics(name, start_time, end_time))
                
        if format == "json":
            return json.dumps([{
                "name": m.name,
                "value": m.value,
                "timestamp": m.timestamp.isoformat(),
                "category": m.category,
                "tags": m.tags,
                "metadata": m.metadata
            } for m in metrics], indent=2)
        elif format == "csv":
            df = pd.DataFrame([{
                "name": m.name,
                "value": m.value,
                "timestamp": m.timestamp,
                "category": m.category,
                "tags": json.dumps(m.tags),
                "metadata": json.dumps(m.metadata)
            } for m in metrics])
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def cleanup(self):
        """Cleanup resources"""
        self._running = False
        
        # Stop cleanup timer
        if self._cleanup_timer:
            self._cleanup_timer.cancel()
            self._cleanup_timer = None
        
        # Wait for threads to finish
        if self._log_thread and self._log_thread.is_alive():
            self._log_thread.join(timeout=5)
        if self._analytics_thread and self._analytics_thread.is_alive():
            self._analytics_thread.join(timeout=5)
        
        # Wait for queues to be processed
        try:
            self.log_queue.join(timeout=5)
            self.analytics_queue.join(timeout=5)
        except Exception:
            pass
        
        # Clear queues
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
                self.log_queue.task_done()
            except queue.Empty:
                break
                
        while not self.analytics_queue.empty():
            try:
                self.analytics_queue.get_nowait()
                self.analytics_queue.task_done()
            except queue.Empty:
                break
        
        # Clear in-memory storage
        self.log_entries.clear()
        self.log_history.clear()
        self.metrics.clear()
        self.metric_history.clear() 
            raise ValueError(f"Unsupported export format: {format}") 