import sys
import traceback
from datetime import datetime
import json
import os
import psutil
from typing import Dict

class ErrorRecovery:
    def __init__(self):
        self.error_log = "error_log.json"
        self.state_file = "app_state.json"
        self.max_retries = 3
        
    def handle_error(self, error: Exception, context: Dict = None):
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        self._log_error(error_info)
        self._save_state()
        
        if self._should_retry(error_info):
            self._attempt_recovery(error_info)
            
    def _log_error(self, error_info: Dict):
        try:
            if os.path.exists(self.error_log):
                with open(self.error_log, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
                
            errors.append(error_info)
            
            with open(self.error_log, 'w') as f:
                json.dump(errors, f)
        except Exception as e:
            print(f"Error logging error: {e}")
            
    def _save_state(self):
        try:
            # Save current application state
            state = {
                "timestamp": datetime.now().isoformat(),
                "memory_usage": psutil.Process().memory_info().rss,
                "open_files": len(psutil.Process().open_files())
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
        except Exception as e:
            print(f"Error saving state: {e}") 