# This file makes the command_manager directory a Python package 

from typing import Dict, Any, Optional
import os
import logging
import customtkinter as ctk
from core.plugin_interface import PluginInterface
from .main import CommandManager
from .gui import CommandManagerApp

__all__ = ['CommandManager', 'CommandManagerApp']

logger = logging.getLogger(__name__)

class CommandManager(PluginInterface):
    """Command manager plugin"""
    
    def __init__(self, plugin_manager):
        super().__init__(plugin_manager)
        self.window = None
        self.app = None
        self.base_dir = os.path.join("plugins", "command_manager")
        
    def start(self) -> bool:
        """Start the command manager"""
        try:
            logger.info("Starting CommandManager plugin")
            
            # Create main window
            self.window = ctk.CTk()
            self.window.title("Command Manager")
            self.window.geometry("800x600")
            
            # Create the app
            self.app = CommandManagerApp(self.window, self.base_dir)
            
            # Start the window
            self.window.mainloop()
            
            logger.info("CommandManager plugin started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start CommandManager plugin: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the command manager"""
        try:
            logger.info("Stopping CommandManager plugin")
            
            if self.window:
                self.window.destroy()
                self.window = None
                self.app = None
                
            logger.info("CommandManager plugin stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop CommandManager plugin: {str(e)}")
            return False
    
    def get_name(self) -> str:
        return "command_manager"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "Command manager plugin for handling custom commands"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the command manager plugin",
                    "default": True
                },
                "auto_start": {
                    "type": "boolean",
                    "description": "Automatically start the plugin",
                    "default": True
                }
            }
        }
    
    def handle_event(self, event_name: str, data: Any) -> Optional[Any]:
        """Handle events from other plugins"""
        if event_name == "get_command_manager":
            return self
        return None 