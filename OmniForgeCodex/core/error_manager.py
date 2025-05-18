import sys
import traceback
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import psutil
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue
import socket
import platform

class ErrorSeverity(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class ErrorCategory(Enum):
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    FILE = "file"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER = "user"
    UNKNOWN = "unknown"

class ErrorManager:
    def __init__(self):
        self.log_dir = Path("logs")
        self.error_log = self.log_dir / "error_log.json"
        self.state_file = self.log_dir / "app_state.json"
        self.max_retries = 3
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.max_log_files = 5
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self.error_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._setup_logging()
        self._setup_error_handlers()
        self._setup_recovery_strategies()
        self._start_error_processor()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "app.log"),
                logging.StreamHandler()
            ]
        )
        
        # Create error logger
        self.error_logger = logging.getLogger("error")
        self.error_logger.setLevel(logging.ERROR)
        
        # Add handlers
        error_handler = logging.FileHandler(self.log_dir / "errors.log")
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.error_logger.addHandler(error_handler)
        
    def _setup_error_handlers(self):
        """Setup error handlers for different categories"""
        self.error_handlers = {
            ErrorCategory.SYSTEM: [
                self._handle_system_error,
                self._log_system_error
            ],
            ErrorCategory.NETWORK: [
                self._handle_network_error,
                self._log_network_error
            ],
            ErrorCategory.DATABASE: [
                self._handle_database_error,
                self._log_database_error
            ],
            ErrorCategory.FILE: [
                self._handle_file_error,
                self._log_file_error
            ],
            ErrorCategory.VALIDATION: [
                self._handle_validation_error,
                self._log_validation_error
            ],
            ErrorCategory.CONFIGURATION: [
                self._handle_configuration_error,
                self._log_configuration_error
            ],
            ErrorCategory.SECURITY: [
                self._handle_security_error,
                self._log_security_error
            ],
            ErrorCategory.PERFORMANCE: [
                self._handle_performance_error,
                self._log_performance_error
            ],
            ErrorCategory.USER: [
                self._handle_user_error,
                self._log_user_error
            ],
            ErrorCategory.UNKNOWN: [
                self._handle_unknown_error,
                self._log_unknown_error
            ]
        }
        
    def _setup_recovery_strategies(self):
        """Setup recovery strategies for different error categories"""
        self.recovery_strategies = {
            ErrorCategory.SYSTEM: [
                self._recover_system_state,
                self._restart_affected_components
            ],
            ErrorCategory.NETWORK: [
                self._retry_network_operation,
                self._fallback_to_cached_data
            ],
            ErrorCategory.DATABASE: [
                self._reconnect_database,
                self._restore_from_backup
            ],
            ErrorCategory.FILE: [
                self._recover_file_operation,
                self._restore_from_backup
            ],
            ErrorCategory.VALIDATION: [
                self._fix_validation_errors,
                self._use_default_values
            ],
            ErrorCategory.CONFIGURATION: [
                self._reload_configuration,
                self._use_default_configuration
            ],
            ErrorCategory.SECURITY: [
                self._handle_security_breach,
                self._revoke_affected_access
            ],
            ErrorCategory.PERFORMANCE: [
                self._optimize_performance,
                self._reduce_workload
            ],
            ErrorCategory.USER: [
                self._handle_user_mistake,
                self._provide_user_guidance
            ],
            ErrorCategory.UNKNOWN: [
                self._log_unknown_error,
                self._notify_administrator
            ]
        }
        
    def _start_error_processor(self):
        """Start the error processing thread"""
        def process_errors():
            while True:
                error_info = self.error_queue.get()
                if error_info is None:
                    break
                self._process_error(error_info)
                
        self.error_processor = threading.Thread(target=process_errors, daemon=True)
        self.error_processor.start()
        
    def handle_error(self, error: Exception, category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.ERROR, context: Dict[str, Any] = None):
        """Handle an error with the appropriate handlers and recovery strategies"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "category": category.value,
            "severity": severity.value,
            "context": context or {},
            "system_info": self._get_system_info()
        }
        
        # Add to queue for processing
        self.error_queue.put(error_info)
        
        # Execute handlers immediately for critical errors
        if severity == ErrorSeverity.CRITICAL:
            self._process_error(error_info)
            
    def _process_error(self, error_info: Dict[str, Any]):
        """Process an error with handlers and recovery strategies"""
        category = ErrorCategory(error_info["category"])
        severity = ErrorSeverity(error_info["severity"])
        
        # Execute error handlers
        for handler in self.error_handlers.get(category, []):
            try:
                handler(error_info)
            except Exception as e:
                self.error_logger.error(f"Error in handler {handler.__name__}: {e}")
                
        # Execute recovery strategies if needed
        if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            for strategy in self.recovery_strategies.get(category, []):
                try:
                    strategy(error_info)
                except Exception as e:
                    self.error_logger.error(f"Error in recovery strategy {strategy.__name__}: {e}")
                    
        # Log error
        self._log_error(error_info)
        
        # Save state
        self._save_state(error_info)
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for error context"""
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "hostname": socket.gethostname(),
            "memory_usage": psutil.Process().memory_info().rss,
            "cpu_percent": psutil.Process().cpu_percent(),
            "open_files": len(psutil.Process().open_files()),
            "threads": threading.active_count()
        }
        
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error to file"""
        try:
            if self.error_log.exists():
                with open(self.error_log, 'r') as f:
                    errors = json.load(f)
            else:
                errors = []
                
            errors.append(error_info)
            
            # Rotate logs if needed
            if self.error_log.stat().st_size > self.max_log_size:
                self._rotate_logs()
                
            with open(self.error_log, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            self.error_logger.error(f"Error logging error: {e}")
            
    def _rotate_logs(self):
        """Rotate log files"""
        for i in range(self.max_log_files - 1, 0, -1):
            old_file = self.log_dir / f"error_log_{i}.json"
            new_file = self.log_dir / f"error_log_{i + 1}.json"
            if old_file.exists():
                if i == self.max_log_files - 1:
                    old_file.unlink()
                else:
                    old_file.rename(new_file)
                    
        self.error_log.rename(self.log_dir / "error_log_1.json")
        
    def _save_state(self, error_info: Dict[str, Any]):
        """Save application state"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "error_info": error_info,
                "memory_usage": psutil.Process().memory_info().rss,
                "open_files": len(psutil.Process().open_files()),
                "threads": threading.active_count()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            self.error_logger.error(f"Error saving state: {e}")
            
    # Error Handlers
    def _handle_system_error(self, error_info: Dict[str, Any]):
        """Handle system errors"""
        self.error_logger.error(f"System error: {error_info['message']}")
        
    def _handle_network_error(self, error_info: Dict[str, Any]):
        """Handle network errors"""
        self.error_logger.error(f"Network error: {error_info['message']}")
        
    def _handle_database_error(self, error_info: Dict[str, Any]):
        """Handle database errors"""
        self.error_logger.error(f"Database error: {error_info['message']}")
        
    def _handle_file_error(self, error_info: Dict[str, Any]):
        """Handle file errors"""
        self.error_logger.error(f"File error: {error_info['message']}")
        
    def _handle_validation_error(self, error_info: Dict[str, Any]):
        """Handle validation errors"""
        self.error_logger.error(f"Validation error: {error_info['message']}")
        
    def _handle_configuration_error(self, error_info: Dict[str, Any]):
        """Handle configuration errors"""
        self.error_logger.error(f"Configuration error: {error_info['message']}")
        
    def _handle_security_error(self, error_info: Dict[str, Any]):
        """Handle security errors"""
        self.error_logger.error(f"Security error: {error_info['message']}")
        
    def _handle_performance_error(self, error_info: Dict[str, Any]):
        """Handle performance errors"""
        self.error_logger.error(f"Performance error: {error_info['message']}")
        
    def _handle_user_error(self, error_info: Dict[str, Any]):
        """Handle user errors"""
        self.error_logger.error(f"User error: {error_info['message']}")
        
    def _handle_unknown_error(self, error_info: Dict[str, Any]):
        """Handle unknown errors"""
        self.error_logger.error(f"Unknown error: {error_info['message']}")
        
    # Recovery Strategies
    def _recover_system_state(self, error_info: Dict[str, Any]):
        """Recover from system errors"""
        pass
        
    def _restart_affected_components(self, error_info: Dict[str, Any]):
        """Restart affected components"""
        pass
        
    def _retry_network_operation(self, error_info: Dict[str, Any]):
        """Retry failed network operations"""
        pass
        
    def _fallback_to_cached_data(self, error_info: Dict[str, Any]):
        """Fall back to cached data"""
        pass
        
    def _reconnect_database(self, error_info: Dict[str, Any]):
        """Reconnect to database"""
        pass
        
    def _restore_from_backup(self, error_info: Dict[str, Any]):
        """Restore from backup"""
        pass
        
    def _recover_file_operation(self, error_info: Dict[str, Any]):
        """Recover from file operation errors"""
        pass
        
    def _fix_validation_errors(self, error_info: Dict[str, Any]):
        """Fix validation errors"""
        pass
        
    def _use_default_values(self, error_info: Dict[str, Any]):
        """Use default values"""
        pass
        
    def _reload_configuration(self, error_info: Dict[str, Any]):
        """Reload configuration"""
        pass
        
    def _use_default_configuration(self, error_info: Dict[str, Any]):
        """Use default configuration"""
        pass
        
    def _handle_security_breach(self, error_info: Dict[str, Any]):
        """Handle security breaches"""
        pass
        
    def _revoke_affected_access(self, error_info: Dict[str, Any]):
        """Revoke affected access"""
        pass
        
    def _optimize_performance(self, error_info: Dict[str, Any]):
        """Optimize performance"""
        pass
        
    def _reduce_workload(self, error_info: Dict[str, Any]):
        """Reduce workload"""
        pass
        
    def _handle_user_mistake(self, error_info: Dict[str, Any]):
        """Handle user mistakes"""
        pass
        
    def _provide_user_guidance(self, error_info: Dict[str, Any]):
        """Provide user guidance"""
        pass
        
    def _notify_administrator(self, error_info: Dict[str, Any]):
        """Notify administrator"""
        pass
        
    def cleanup(self):
        """Clean up resources"""
        self.error_queue.put(None)  # Signal thread to stop
        self.error_processor.join()
        self.executor.shutdown(wait=False) 