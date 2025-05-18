import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import os
import json
import sys
from typing import Dict, Any
from logger import SimpleLogger

# Initialize logger
logger = SimpleLogger()

class SimpleLauncher:
    def __init__(self):
        logger.info("Initializing SimpleLauncher")
        self.root = None
        self.config = None
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the SimpleLauncher application"""
        if self._initialized:
            logger.info("SimpleLauncher already initialized")
            return

        try:
            self.root = ctk.CTk()
            self.root.title("Simple Launcher")
            self.root.geometry("800x600")
            
            self.load_config()
            self.create_widgets()
            
            self._initialized = True
            logger.info("SimpleLauncher initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}", exc_info=True)
            messagebox.showerror("Initialization Error", str(e))
            sys.exit(1)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    logger.info("Configuration loaded successfully")
            else:
                self.config = {}
                logger.warning("No configuration file found, using defaults")
            return self.config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}", exc_info=True)
            return {}

    def create_widgets(self) -> None:
        """Create the main GUI widgets"""
        try:
            # Main frame
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Title label
            title_label = ctk.CTkLabel(
                main_frame,
                text="Simple Launcher",
                font=("Helvetica", 24, "bold")
            )
            title_label.pack(pady=20)
            
            # Status label
            self.status_label = ctk.CTkLabel(
                main_frame,
                text="Ready",
                font=("Helvetica", 12)
            )
            self.status_label.pack(pady=10)
            
            logger.info("GUI widgets created successfully")
            
        except Exception as e:
            logger.error(f"Error creating widgets: {str(e)}", exc_info=True)
            raise

    def run(self) -> None:
        """Run the SimpleLauncher application"""
        try:
            self.initialize()
            self.root.mainloop()
        except Exception as e:
            logger.error("Fatal error in SimpleLauncher", exc_info=True)
            messagebox.showerror("Fatal Error", f"SimpleLauncher encountered a fatal error: {str(e)}")
            sys.exit(1)

def main():
    """Main entry point for SimpleLauncher"""
    try:
        app = SimpleLauncher()
        app.run()
    except Exception as e:
        logger.error("Fatal error in main", exc_info=True)
        messagebox.showerror("Fatal Error", f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 