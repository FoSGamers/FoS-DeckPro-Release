import os
import sys
import customtkinter as ctk
from core.utils.logging_config import setup_logging, get_logger
from core.launcher import Launcher

def main():
    # Setup logging
    setup_logging()
    logger = get_logger("main")
    logger.info("Starting FoS Launcher")
    
    try:
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create and start launcher
        launcher = Launcher()
        if not launcher.start():
            logger.error("Failed to start launcher")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 