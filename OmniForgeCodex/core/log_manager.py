import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

class LogManager:
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level)
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'app.log'),
                logging.StreamHandler()
            ]
        )
        
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(name)
        
    def set_level(self, level: str):
        """Set the logging level"""
        self.log_level = getattr(logging, level)
        logging.getLogger().setLevel(self.log_level)
        
    def rotate_logs(self, max_size: int = 10 * 1024 * 1024):  # 10MB
        """Rotate log files if they exceed max_size"""
        log_file = self.log_dir / 'app.log'
        if log_file.exists() and log_file.stat().st_size > max_size:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.log_dir / f'app_{timestamp}.log'
            log_file.rename(backup_file)
            self.setup_logging() 