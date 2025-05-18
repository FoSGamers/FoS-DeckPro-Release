import os
import logging
from typing import Optional

class FoSLogger:
    """Simplified logger for FoSLauncher"""
    
    def __init__(self, name: str = "FoSLauncher"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            # Set up console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            
            # Simple formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Set up file handler if logs directory exists
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
            if os.path.exists(log_dir):
                file_handler = logging.FileHandler(
                    os.path.join(log_dir, "foslauncher.log")
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            
            self.logger.setLevel(logging.DEBUG)

    def debug(self, message: str, exc_info: bool = False) -> None:
        self.logger.debug(message, exc_info=exc_info)

    def info(self, message: str, exc_info: bool = False) -> None:
        self.logger.info(message, exc_info=exc_info)

    def warning(self, message: str, exc_info: bool = False) -> None:
        self.logger.warning(message, exc_info=exc_info)

    def error(self, message: str, exc_info: bool = False) -> None:
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        self.logger.critical(message, exc_info=exc_info)

# Create a single instance
logger = FoSLogger() 