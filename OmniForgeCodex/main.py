import sys
import argparse
import logging
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTranslator, QLocale
from ui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.logging_manager import LoggingManager, LogLevel, LogCategory
from core.security_manager import SecurityManager
import traceback

class Application:
    def __init__(self):
        self.setup_argparse()
        self.setup_logging()
        self.setup_config()
        self.setup_security()
        self.setup_translations()
        
    def setup_argparse(self):
        parser = argparse.ArgumentParser(description='OmniForgeCodex')
        parser.add_argument('--config', help='Path to config file')
        parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                          default='INFO', help='Set logging level')
        parser.add_argument('--no-gui', action='store_true', help='Run without GUI')
        self.args = parser.parse_args()
        
    def setup_logging(self):
        """Setup logging using LoggingManager"""
        self.logger = LoggingManager()
        
        # Set log levels based on command line argument
        log_level = LogLevel[self.args.log_level]
        for category in LogCategory:
            self.logger.log_levels[category] = log_level
            
        # Log application startup
        self.logger.log(
            LogLevel.INFO,
            LogCategory.APPLICATION,
            "Application starting",
            "Application",
            {"version": "1.0.0", "args": vars(self.args)}
        )
        
    def setup_config(self):
        self.config = ConfigManager()
        if self.args.config:
            self.config.load(self.args.config)
            self.logger.log(
                LogLevel.INFO,
                LogCategory.APPLICATION,
                f"Loaded config from {self.args.config}",
                "ConfigManager"
            )
        else:
            self.config.load_default()
            self.logger.log(
                LogLevel.INFO,
                LogCategory.APPLICATION,
                "Loaded default config",
                "ConfigManager"
            )
            
    def setup_security(self):
        self.security = SecurityManager()
        self.security.initialize()
        self.logger.log(
            LogLevel.INFO,
            LogCategory.SECURITY,
            "Security manager initialized",
            "SecurityManager"
        )
        
    def setup_translations(self):
        self.translator = QTranslator()
        locale = QLocale.system().name()
        if self.translator.load(f":/translations/{locale}"):
            QApplication.installTranslator(self.translator)
            self.logger.log(
                LogLevel.INFO,
                LogCategory.APPLICATION,
                f"Loaded translations for locale: {locale}",
                "TranslationManager"
            )
            
    def run(self):
        try:
            app = QApplication(sys.argv)
            app.setApplicationName("OmniForgeCodex")
            app.setOrganizationName("OmniForge")
            
            if not self.args.no_gui:
                window = MainWindow(self.config, self.security)
                window.show()
                self.logger.log(
                    LogLevel.INFO,
                    LogCategory.UI,
                    "Main window displayed",
                    "Application"
                )
                
            return app.exec()
        except Exception as e:
            self.logger.log(
                LogLevel.ERROR,
                LogCategory.APPLICATION,
                f"Application error: {str(e)}",
                "Application",
                stack_trace=traceback.format_exc()
            )
            return 1
        finally:
            self.cleanup()
            
    def cleanup(self):
        self.logger.log(
            LogLevel.INFO,
            LogCategory.APPLICATION,
            "Cleaning up application...",
            "Application"
        )
        # Implement cleanup logic

if __name__ == '__main__':
    app = Application()
    sys.exit(app.run())
