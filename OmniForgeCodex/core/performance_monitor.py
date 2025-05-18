import time
from collections import deque
from typing import Dict, List, Deque, Any, Optional, Union, Tuple
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
import psutil
import json
import logging
from pathlib import Path
from collections import defaultdict
import numpy as np
from enum import Enum
import gc
import tracemalloc
import line_profiler
import memory_profiler
import cProfile
import pstats

class PerformanceMetric(Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    RESPONSE_TIME = "response_time"
    THREAD_COUNT = "thread_count"
    GC_COLLECTIONS = "gc_collections"
    CACHE_HITS = "cache_hits"
    CACHE_MISSES = "cache_misses"
    API_CALLS = "api_calls"
    DATABASE_QUERIES = "database_queries"
    UI_RENDER_TIME = "ui_render_time"

@dataclass
class PerformanceThreshold:
    metric: PerformanceMetric
    warning_threshold: float
    critical_threshold: float
    duration: timedelta = timedelta(minutes=5)

@dataclass
class PerformanceAlert:
    metric: PerformanceMetric
    value: float
    threshold: float
    timestamp: datetime
    severity: str

class PerformanceMonitor:
    def __init__(self):
        self.metrics_dir = Path("metrics")
        self.alerts_dir = self.metrics_dir / "alerts"
        self.profiles_dir = self.metrics_dir / "profiles"
        
        # Performance tracking
        self._metrics_history: Dict[PerformanceMetric, List[Tuple[datetime, float]]] = defaultdict(list)
        self._current_metrics: Dict[PerformanceMetric, float] = {}
        self._alerts: List[PerformanceAlert] = []
        self._thresholds: Dict[PerformanceMetric, PerformanceThreshold] = {}
        
        # Profiling
        self._profiler = cProfile.Profile()
        self._line_profiler = line_profiler.LineProfiler()
        self._memory_profiler = memory_profiler.profile
        self._tracemalloc = tracemalloc
        
        # Monitoring
        self.monitor_thread = None
        self.monitor_interval = 60  # 1 minute
        self.history_retention = timedelta(days=7)
        
        # Setup
        self.setup_directories()
        self.setup_default_thresholds()
        self.start_monitoring()
        
    def setup_directories(self):
        """Setup required directories"""
        self.metrics_dir.mkdir(exist_ok=True)
        self.alerts_dir.mkdir(exist_ok=True)
        self.profiles_dir.mkdir(exist_ok=True)
        
    def setup_default_thresholds(self):
        """Setup default performance thresholds"""
        self._thresholds = {
            PerformanceMetric.CPU_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.CPU_USAGE,
                warning_threshold=70.0,
                critical_threshold=90.0
            ),
            PerformanceMetric.MEMORY_USAGE: PerformanceThreshold(
                metric=PerformanceMetric.MEMORY_USAGE,
                warning_threshold=80.0,
                critical_threshold=95.0
            ),
            PerformanceMetric.RESPONSE_TIME: PerformanceThreshold(
                metric=PerformanceMetric.RESPONSE_TIME,
                warning_threshold=1.0,  # seconds
                critical_threshold=3.0
            ),
            PerformanceMetric.THREAD_COUNT: PerformanceThreshold(
                metric=PerformanceMetric.THREAD_COUNT,
                warning_threshold=50,
                critical_threshold=100
            )
        }
        
    def start_monitoring(self):
        """Start performance monitoring"""
        def monitor():
            while True:
                self._collect_metrics()
                self._check_thresholds()
                self._cleanup_old_metrics()
                time.sleep(self.monitor_interval)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def _collect_metrics(self):
        """Collect current performance metrics"""
        process = psutil.Process()
        
        self._current_metrics = {
            PerformanceMetric.CPU_USAGE: process.cpu_percent(),
            PerformanceMetric.MEMORY_USAGE: process.memory_percent(),
            PerformanceMetric.THREAD_COUNT: process.num_threads(),
            PerformanceMetric.DISK_IO: process.io_counters().read_bytes + process.io_counters().write_bytes,
            PerformanceMetric.NETWORK_IO: sum(conn.bytes_sent + conn.bytes_recv for conn in process.connections()),
            PerformanceMetric.GC_COLLECTIONS: gc.get_count()[0]  # Generation 0 collections
        }
        
        # Update history
        timestamp = datetime.now()
        for metric, value in self._current_metrics.items():
            self._metrics_history[metric].append((timestamp, value))
            
    def _check_thresholds(self):
        """Check metrics against thresholds"""
        for metric, threshold in self._thresholds.items():
            current_value = self._current_metrics.get(metric)
            if current_value is None:
                continue
                
            if current_value >= threshold.critical_threshold:
                self._create_alert(metric, current_value, threshold, "critical")
            elif current_value >= threshold.warning_threshold:
                self._create_alert(metric, current_value, threshold, "warning")
                
    def _create_alert(self, metric: PerformanceMetric, value: float,
                     threshold: PerformanceThreshold, severity: str):
        """Create a performance alert"""
        alert = PerformanceAlert(
            metric=metric,
            value=value,
            threshold=threshold.critical_threshold if severity == "critical" else threshold.warning_threshold,
            timestamp=datetime.now(),
            severity=severity
        )
        
        self._alerts.append(alert)
        self._save_alert(alert)
        
    def _save_alert(self, alert: PerformanceAlert):
        """Save alert to file"""
        alert_file = self.alerts_dir / f"alert_{alert.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        alert_data = {
            "metric": alert.metric.value,
            "value": alert.value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity
        }
        
        with open(alert_file, 'w') as f:
            json.dump(alert_data, f, indent=2)
            
    def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        cutoff_time = datetime.now() - self.history_retention
        
        for metric in self._metrics_history:
            self._metrics_history[metric] = [
                (timestamp, value) for timestamp, value in self._metrics_history[metric]
                if timestamp > cutoff_time
            ]
            
    def start_profiling(self, name: str):
        """Start profiling a specific component"""
        self._profiler.enable()
        self._tracemalloc.start()
        
    def stop_profiling(self, name: str):
        """Stop profiling and save results"""
        self._profiler.disable()
        self._tracemalloc.stop()
        
        # Save CPU profile
        stats = pstats.Stats(self._profiler)
        profile_file = self.profiles_dir / f"{name}_cpu.prof"
        stats.dump_stats(str(profile_file))
        
        # Save memory profile
        snapshot = self._tracemalloc.take_snapshot()
        memory_file = self.profiles_dir / f"{name}_memory.prof"
        snapshot.dump(str(memory_file))
        
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": {
                metric.value: value for metric, value in self._current_metrics.items()
            },
            "alerts": [
                {
                    "metric": alert.metric.value,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat(),
                    "severity": alert.severity
                }
                for alert in self._alerts[-10:]  # Last 10 alerts
            ],
            "trends": self._calculate_trends(),
            "recommendations": self._generate_recommendations()
        }
        
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends"""
        trends = {}
        for metric, history in self._metrics_history.items():
            if len(history) < 2:
                continue
                
            values = [value for _, value in history]
            trends[metric.value] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "trend": np.polyfit(range(len(values)), values, 1)[0]
            }
        return trends
        
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # CPU recommendations
        cpu_trend = self._metrics_history.get(PerformanceMetric.CPU_USAGE, [])
        if cpu_trend and np.mean([v for _, v in cpu_trend]) > 50:
            recommendations.append("Consider optimizing CPU-intensive operations")
            
        # Memory recommendations
        memory_trend = self._metrics_history.get(PerformanceMetric.MEMORY_USAGE, [])
        if memory_trend and np.mean([v for _, v in memory_trend]) > 70:
            recommendations.append("Consider implementing memory optimization strategies")
            
        # Response time recommendations
        response_trend = self._metrics_history.get(PerformanceMetric.RESPONSE_TIME, [])
        if response_trend and np.mean([v for _, v in response_trend]) > 1.0:
            recommendations.append("Consider optimizing slow operations")
            
        return recommendations
        
    def optimize_performance(self):
        """Apply performance optimizations"""
        # Memory optimization
        if self._current_metrics.get(PerformanceMetric.MEMORY_USAGE, 0) > 80:
            gc.collect()
            
        # CPU optimization
        if self._current_metrics.get(PerformanceMetric.CPU_USAGE, 0) > 80:
            self._optimize_cpu_usage()
            
        # Cache optimization
        if self._current_metrics.get(PerformanceMetric.CACHE_MISSES, 0) > 1000:
            self._optimize_cache()
            
    def _optimize_cpu_usage(self):
        """Optimize CPU usage"""
        # Implement CPU optimization strategies
        pass
        
    def _optimize_cache(self):
        """Optimize cache usage"""
        # Implement cache optimization strategies
        pass 