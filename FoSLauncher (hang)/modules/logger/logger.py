import os
import sys
import logging
import traceback
import json
from typing import Optional, Dict, Any
from datetime import datetime
from logging.handlers import RotatingFileHandler

class FoSLogger:
    """Centralized logging system for FoSLauncher"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FoSLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self) -> None:
        """Initialize the logger with comprehensive configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        
        # Create logger
        self._logger = logging.getLogger("FoSLauncher")
        self._logger.setLevel(logging.DEBUG)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            'logs/foslauncher.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Add handlers
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)
        
        # Log initialization
        self._logger.info("Logger initialized")
        self._logger.debug(f"Log file: {os.path.abspath('logs/foslauncher.log')}")
    
    def debug(self, message: str, exc_info: bool = False) -> None:
        """Log debug message"""
        self._logger.debug(message, exc_info=exc_info)
    
    def info(self, message: str, exc_info: bool = False) -> None:
        """Log info message"""
        self._logger.info(message, exc_info=exc_info)
    
    def warning(self, message: str, exc_info: bool = False) -> None:
        """Log warning message"""
        self._logger.warning(message, exc_info=exc_info)
    
    def error(self, message: str, exc_info: bool = True) -> None:
        """Log error message"""
        self._logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = True) -> None:
        """Log critical message"""
        self._logger.critical(message, exc_info=exc_info)
    
    def log_user_action(self, action: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log user actions with details"""
        message = f"User Action: {action}"
        if details:
            message += f" - Details: {json.dumps(details)}"
        self._logger.info(message)
    
    def log_module_event(self, module: str, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log module-specific events"""
        message = f"Module [{module}] - {event}"
        if details:
            message += f" - Details: {json.dumps(details)}"
        self._logger.debug(message)
    
    def log_config_change(self, config_key: str, old_value: Any, new_value: Any) -> None:
        """Log configuration changes"""
        self._logger.info(f"Config Change - {config_key}: {old_value} -> {new_value}")
    
    def log_error_with_context(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with additional context"""
        message = f"Error: {str(error)}"
        if context:
            message += f" - Context: {json.dumps(context)}"
        self._logger.error(message, exc_info=True)
    
    def get_log_file_path(self) -> str:
        """Get the path to the current log file"""
        return os.path.abspath('logs/foslauncher.log')
    
    def get_recent_logs(self, lines: int = 100) -> str:
        """Get recent log entries"""
        try:
            with open(self.get_log_file_path(), 'r') as f:
                return ''.join(f.readlines()[-lines:])
        except Exception as e:
            self._logger.error(f"Failed to read recent logs: {e}")
            return "Failed to read log file"

    def log_module_start(self, module: str, config: Dict[str, Any]) -> None:
        """Log module startup information"""
        self._logger.info(f"Starting {module} module")
        self._logger.debug(f"Module configuration: {config}")
        
    def log_module_stop(self, module: str) -> None:
        """Log module shutdown information"""
        self._logger.info(f"Stopping {module} module")
        
    def log_access(self, user: str, action: str, success: bool) -> None:
        """Log access control events"""
        status = "success" if success else "failed"
        self._logger.info(f"Access {status} - User: {user}, Action: {action}")
        
    def log_error(self, module: str, error: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log error information"""
        if details:
            self._logger.error(f"{error} - Details: {details}")
        else:
            self._logger.error(error)
            
    def log_warning(self, module: str, warning: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log warning information"""
        if details:
            self._logger.warning(f"{warning} - Details: {details}")
        else:
            self._logger.warning(warning)
            
    def log_info(self, module: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log information"""
        if details:
            self._logger.info(f"{message} - Details: {details}")
        else:
            self._logger.info(message)
            
    def log_debug(self, module: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log debug information"""
        if details:
            self._logger.debug(f"{message} - Details: {details}")
        else:
            self._logger.debug(message) 