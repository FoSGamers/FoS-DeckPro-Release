import os
import logging
from typing import Dict, Any, List
from core.plugins.plugin_interface import PluginInterface, PluginDependency
import customtkinter as ctk
from .gui import ChatSplitterApp

class ChatSplitterPlugin(PluginInterface):
    """Chat Splitter plugin for FoSLauncher"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_dir = config.get('base_dir', "plugins/chatsplitter")
        self.app = None
        self.window = None
        self.logger = logging.getLogger("chatsplitter")
        self.logger.info("Chat splitter plugin initialized")

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[PluginDependency]:
        return []

    def get_name(self) -> str:
        return "chatsplitter"

    def is_running(self) -> bool:
        return self._running

    def get_config_schema(self) -> Dict[str, Any]:
        """Get the plugin's configuration schema"""
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the chat splitter plugin",
                    "default": True
                },
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for plugin files",
                    "default": "plugins/chatsplitter"
                },
                "requires_code": {
                    "type": "boolean",
                    "description": "Whether the plugin requires a code to run",
                    "default": True
                },
                "access_level": {
                    "type": "string",
                    "enum": ["none", "basic", "advanced", "master"],
                    "description": "Required access level to use the plugin",
                    "default": "basic"
                },
                "settings": {
                    "type": "object",
                    "properties": {
                        "default_output_dir": {
                            "type": "string",
                            "description": "Default directory for output files",
                            "default": "output"
                        },
                        "default_image_dir": {
                            "type": "string",
                            "description": "Default directory for image files",
                            "default": "images"
                        },
                        "max_file_size_mb": {
                            "type": "integer",
                            "description": "Maximum file size in MB",
                            "default": 25
                        }
                    },
                    "required": ["default_output_dir", "default_image_dir", "max_file_size_mb"],
                    "additionalProperties": false
                }
            },
            "required": ["enabled", "base_dir", "settings"],
            "additionalProperties": false
        }

    def start(self) -> bool:
        """Start the Chat Splitter GUI"""
        try:
            self.logger.info("Starting Chat Splitter plugin")
            
            if self._running:
                self.logger.warning("Chat splitter is already running")
                return False

            # Create GUI window
            self.window = ctk.CTkToplevel()
            self.window.title("Chat Splitter")
            self.window.geometry("600x400")
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable X button
            
            # Create app instance
            self.app = ChatSplitterApp(self.window, self.base_dir)
            self.app.start()
            
            self._running = True
            self.logger.info("Chat splitter GUI started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Chat Splitter plugin: {str(e)}")
            return False
            
    def stop(self) -> bool:
        """Stop the Chat Splitter GUI"""
        try:
            self.logger.info("Stopping Chat Splitter plugin")
            
            if not self._running:
                self.logger.warning("Chat splitter is not running")
                return False

            if self.window:
                try:
                    # Cleanup app first
                    if self.app:
                        self.app.stop()
                        self.app = None
                    
                    # Destroy the window
                    self.window.destroy()
                    self.window = None
                    
                    self._running = False
                    self.logger.info("Chat splitter stopped")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Non-critical error during window cleanup: {str(e)}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop Chat Splitter plugin: {str(e)}")
            return False