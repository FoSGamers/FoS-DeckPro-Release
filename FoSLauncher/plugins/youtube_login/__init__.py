# This file makes the youtube_login directory a Python package 

from typing import Dict, Any, Optional
from core.plugin_interface import PluginInterface
from .youtube_client import YouTubeClient
from .main import YouTubeLogin, StreamSelector
import os
import logging
import tkinter as tk
import threading
import traceback
import sys
from .youtube_login import YouTubeLoginPlugin
from .gui import YouTubeLoginApp

__all__ = ['YouTubeLoginPlugin', 'YouTubeClient', 'YouTubeLoginApp']

class YoutubeLogin(PluginInterface):
    """YouTube login plugin"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.login_gui = None
        self.logger = logging.getLogger("youtube_login")
        self.root = None
        self._is_running = False
        
    def start(self) -> bool:
        """Start the YouTube client"""
        if self._is_running:
            self.logger.warning("Plugin is already running")
            return True
            
        try:
            self.logger.info("Starting YouTube login plugin")
            client_secrets_path = os.path.join("plugins", "youtube_login", "client_secrets.json")
            token_path = os.path.join("config", "modules", "youtube_login", "token.pickle")
            
            # Initialize the YouTube client
            self.client = YouTubeClient(client_secrets_path, token_path)
            
            # Get the main application window
            from core.gui_launcher import GUILauncher
            main_window = GUILauncher.get_main_window()
            
            if not main_window:
                self.logger.error("Could not get main application window")
                return False
                
            self.root = main_window
            
            if self.client.load_credentials():
                # If we have valid credentials, show stream selector directly
                self.logger.info("Using existing credentials")
                try:
                    self.logger.debug("Creating stream selector")
                    selector = StreamSelector(self.root, self.client)
                    self.logger.debug("Waiting for stream selector window")
                    selector.wait_window()  # Wait for the selector to close
                except Exception as e:
                    self.logger.error(f"Error showing stream selector: {str(e)}")
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
            else:
                # If no valid credentials, show login GUI
                self.logger.info("No valid credentials, showing login GUI")
                try:
                    self.login_gui = YouTubeLogin()
                    # Run the login GUI in a separate thread to avoid blocking
                    def run_login():
                        try:
                            self.login_gui.start(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), parent=self.root)
                        except Exception as e:
                            self.logger.error(f"Error in login thread: {str(e)}")
                            self.logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    login_thread = threading.Thread(target=run_login, daemon=True)
                    login_thread.start()
                    
                except Exception as e:
                    self.logger.error(f"Error showing login GUI: {str(e)}")
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            self._is_running = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start YouTube client: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.stop()
            return False
    
    def stop(self) -> bool:
        """Stop the YouTube client"""
        if not self._is_running:
            return True
            
        try:
            self.logger.info("Stopping YouTube login plugin")
            if self.login_gui:
                try:
                    self.logger.debug("Stopping login GUI")
                    self.login_gui.stop()
                except Exception as e:
                    self.logger.debug(f"Non-critical error stopping login GUI: {str(e)}")
                self.login_gui = None
                
            if self.client:
                try:
                    self.logger.debug("Closing YouTube client")
                    if hasattr(self.client, 'close'):
                        self.client.close()
                except Exception as e:
                    self.logger.debug(f"Non-critical error closing client: {str(e)}")
                self.client = None
                
            self.root = None
            self._is_running = False
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop YouTube client: {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def get_name(self) -> str:
        return "youtube_login"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "YouTube login and authentication plugin"
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the YouTube login plugin",
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
        if event_name == "get_youtube_client":
            return self.client
        return None 