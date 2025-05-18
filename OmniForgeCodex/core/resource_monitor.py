import psutil
import os
from typing import Dict
from datetime import datetime

class ResourceMonitor:
    def __init__(self):
        self.log_file = "resource_usage.log"
        self.warning_thresholds = {
            "memory_percent": 80,
            "cpu_percent": 80,
            "disk_percent": 80
        }
        
    def check_resources(self) -> Dict:
        usage = {
            "timestamp": datetime.now().isoformat(),
            "memory": self._check_memory(),
            "cpu": self._check_cpu(),
            "disk": self._check_disk(),
            "network": self._check_network()
        }
        
        self._log_usage(usage)
        self._check_warnings(usage)
        
        return usage
        
    def _check_memory(self) -> Dict:
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent
        }
        
    def _check_cpu(self) -> Dict:
        return {
            "percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count()
        }
        
    def _check_disk(self) -> Dict:
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "free": disk.free,
            "percent": disk.percent
        }
        
    def _log_usage(self, usage: Dict):
        try:
            with open(self.log_file, 'a') as f:
                f.write(f"{json.dumps(usage)}\n")
        except Exception as e:
            print(f"Error logging resource usage: {e}") 