import os
import logging
from typing import Dict, Any, List
from core.plugins.plugin_interface import PluginInterface, PluginDependency
import customtkinter as ctk
from .youtube_client import YouTubeClient
from .gui import YouTubeLoginApp

class YouTubeLoginPlugin(PluginInterface):
    """YouTube Login plugin for FoSLauncher"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_dir = config.get('base_dir', "plugins/youtube_login")
        self.app = None
        self.window = None
        self.logger = logging.getLogger("youtube_login")
        self.logger.info("YouTube login plugin initialized")

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[PluginDependency]:
        return []

    def get_name(self) -> str:
        return "youtube_login"

    def is_running(self) -> bool:
        return self._running

    def get_config_schema(self) -> Dict[str, Any]:
        """Get the plugin's configuration schema"""
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the YouTube login plugin",
                    "default": True
                },
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for plugin files",
                    "default": "plugins/youtube_login"
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
                        "client_secrets_path": {
                            "type": "string",
                            "description": "Path to the client secrets JSON file",
                            "default": "client_secrets.json"
                        },
                        "token_path": {
                            "type": "string",
                            "description": "Path to store the OAuth token",
                            "default": "token.pickle"
                        }
                    },
                    "required": ["client_secrets_path", "token_path"],
                    "additionalProperties": false
                }
            },
            "required": ["enabled", "base_dir", "settings"],
            "additionalProperties": false
        }

    def start(self) -> bool:
        """Start the YouTube Login GUI"""
        try:
            self.logger.info("Starting YouTube Login plugin")
            
            if self._running:
                self.logger.warning("YouTube login is already running")
                return False

            # Create GUI window
            self.window = ctk.CTkToplevel()
            self.window.title("YouTube Login")
            self.window.geometry("400x300")
            self.window.configure(fg_color="#1a1a1a")
            
            # Disable X button
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Create app instance
            self.app = YouTubeLoginApp(self.window, self.base_dir)
            self.app.start()
            
            # Bring window to front
            self.window.lift()
            self.window.focus_force()
            
            self._running = True
            self.logger.info("YouTube login GUI started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start YouTube Login plugin: {str(e)}")
            return False
            
    def stop(self) -> bool:
        """Stop the YouTube Login GUI"""
        try:
            self.logger.info("Stopping YouTube Login plugin")
            
            if not self._running:
                self.logger.warning("YouTube login is not running")
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
                    self.logger.info("YouTube login stopped")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Non-critical error during window cleanup: {str(e)}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop YouTube Login plugin: {str(e)}")
            return False 