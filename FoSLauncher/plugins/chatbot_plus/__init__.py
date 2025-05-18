# This file makes the chatbot_plus directory a Python package 

from typing import Dict, Any, Optional
import os
import logging
import customtkinter as ctk
from core.plugin_interface import PluginInterface
from .unified_chat import UnifiedChatInterface

class ChatbotPlus(PluginInterface):
    """Chatbot+ plugin"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.launcher = config.get("launcher")  # Store launcher reference
        self.logger = logging.getLogger("chatbot_plus")
        self.window = None
        self.chat_interface = None
        self.command_manager = None
        self.youtube_client = None
        self.base_dir = os.path.join("plugins", "chatbot_plus")
        
    def start(self) -> bool:
        """Start the Chatbot+ plugin"""
        try:
            self.logger.info("Starting Chatbot+ plugin")
            
            # Create main window
            self.window = ctk.CTk()
            self.window.title("Chatbot+")
            self.window.geometry("800x600")
            
            # Get YouTube client from other plugins
            if self.launcher:
                youtube_plugin = self.launcher.get_plugin("youtube_login")
                if youtube_plugin:
                    self.youtube_client = youtube_plugin.client
                    self.logger.info("Connected to YouTube client")
                
                command_manager_plugin = self.launcher.get_plugin("command_manager")
                if command_manager_plugin:
                    self.command_manager = command_manager_plugin
                    self.logger.info("Connected to Command Manager")
            else:
                self.logger.warning("No launcher reference available")
            
            # Create chat interface
            self.chat_interface = UnifiedChatInterface(
                youtube_client=self.youtube_client,
                parent_window=self.window,
                base_dir=self.base_dir
            )
            
            # Start the window
            self.window.mainloop()
            
            self.logger.info("Chatbot+ plugin started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Chatbot+: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the Chatbot+ plugin"""
        try:
            self.logger.info("Stopping Chatbot+ plugin")
            
            if self.chat_interface:
                self.chat_interface.cleanup()
                self.chat_interface = None
                
            if self.command_manager:
                self.command_manager = None
                
            if self.window:
                self.window.destroy()
                self.window = None
                
            self.logger.info("Chatbot+ plugin stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop Chatbot+: {str(e)}")
            return False
    
    def get_name(self) -> str:
        return "chatbot_plus"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "Enhanced chatbot with YouTube integration and command management"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the Chatbot+ plugin",
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
        if event_name == "get_chat_interface":
            return self.chat_interface
        return None 