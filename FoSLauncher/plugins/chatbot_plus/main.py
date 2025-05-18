# File: modules/chatbot_plus/main.py

import os
import sys
import json
import asyncio
import threading
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import websockets
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from .unified_chat import UnifiedChatInterface
from .status_manager import StatusManager
from plugins.youtube_login.youtube_client import YouTubeClient
from plugins.command_manager import CommandManager

# Initialize logger
logger = logging.getLogger("chatbot_plus")

class ChatbotPlus:
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ChatbotPlus module"""
        self.logger = logging.getLogger("chatbot_plus")
        self.config = config
        self.window = None
        self.app = None
        self.server = None
        self.project_root = None
        self.connected_clients = set()
        self.chat_interface = None
        self.status_manager = None
        self.youtube_client = None
        self.loop = None
        self.command_manager = None
        
        # Initialize YouTube client if enabled
        if self.config.get("settings", {}).get("feature_flags", {}).get("youtube", False):
            # Try to get the existing YouTube client from the module loader
            from modules.module_loader.module_loader import ModuleLoader
            module_loader = ModuleLoader()
            youtube_login = module_loader.get_module("youtube_login")
            if youtube_login and hasattr(youtube_login, 'client'):
                self.youtube_client = youtube_login.client
                self.logger.info("Using existing YouTube client")
            else:
                # Fallback to creating a new client if needed
                client_secrets_path = os.path.join("modules", "youtube_login", "client_secrets.json")
                credentials_path = os.path.join("modules", "youtube_login", "credentials.json")
                self.youtube_client = YouTubeClient(client_secrets_path, credentials_path)
                self.logger.info("Created new YouTube client")

    def create_gui(self):
        """Create the GUI for the chatbot"""
        try:
            self.logger.info("Creating GUI for ChatbotPlus")
            
            # Create main window
            self.window = ctk.CTk()
            self.window.title("Chatbot+")
            self.window.geometry("800x600")
            
            # Create chat interface with proper command manager initialization
            self.chat_interface = UnifiedChatInterface(
                youtube_client=self.youtube_client,
                parent_window=self.window,
                base_dir=os.path.join("plugins", "command_manager")
            )
            
            self.logger.info("GUI created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create GUI: {str(e)}")
            raise

    def start(self):
        """Start the chatbot"""
        try:
            self.logger.info("Starting ChatbotPlus")
            
            # Create GUI
            self.create_gui()
            
            # Start the main loop
            self.window.mainloop()
            
            self.logger.info("ChatbotPlus started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting ChatbotPlus: {str(e)}")
            raise

    def stop(self):
        """Stop the chatbot"""
        try:
            self.logger.info("Stopping ChatbotPlus")
            
            # Cleanup chat interface first
            if hasattr(self, 'chat_interface'):
                self.chat_interface.cleanup()
            
            # Cleanup windows
            if hasattr(self, 'window') and self.window:
                try:
                    # Get all windows before we start destroying them
                    windows = [(w, w.tk.call('after', 'info')) for w in self.window.winfo_children() 
                             if isinstance(w, (ctk.CTkToplevel, tk.Toplevel))]
                    windows.append((self.window, self.window.tk.call('after', 'info')))
                    
                    # Cancel callbacks and destroy windows in reverse order
                    for window, after_ids in reversed(windows):
                        try:
                            # Cancel any pending after callbacks
                            for after_id in after_ids:
                                try:
                                    window.after_cancel(after_id)
                                except Exception:
                                    pass
                            # Destroy the window
                            window.destroy()
                        except Exception:
                            pass
                    
                    self.window = None
                    
                except Exception as e:
                    self.logger.warning(f"Non-critical error during window cleanup: {str(e)}")
            
            self.logger.info("ChatbotPlus stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping ChatbotPlus: {str(e)}")
            raise

    def launch(self):
        """Launch the chatbot plus module"""
        self.start()

    async def initialize_components(self):
        """Initialize all required components"""
        self.logger.info("Initializing components")
        try:
            # Authenticate with YouTube if auto_join is enabled
            if self.config.get("settings", {}).get("youtube", {}).get("auto_join", True):
                self.logger.debug("Attempting YouTube authentication")
                if not await self.youtube_client.authenticate():
                    self.logger.warning("YouTube authentication failed, YouTube features will be disabled")
                    return
                    
                self.logger.info("Successfully authenticated with YouTube")
            
            # Initialize other components
            self.chat_interface = UnifiedChatInterface(self.youtube_client, self.window)
            self.status_manager = StatusManager()
            
            self.logger.info("Components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {str(e)}")
            raise

    def cleanup(self):
        """Cleanup all components"""
        self.logger.info("Cleaning up components")
        if self.youtube_client:
            self.youtube_client.stop()
        if self.status_manager:
            self.status_manager.stop_status_checks()
        if self.chat_interface:
            self.chat_interface.cleanup()
        if self.loop:
            self.loop.close()

    async def process_chat_message(self, message: str):
        """Process incoming chat messages"""
        try:
            # Process the message through the chat interface
            response = await self.chat_interface.process_message(message)
            
            # Broadcast the response to all connected clients
            await self.broadcast_message(response)
            
        except Exception as e:
            self.logger.error(f"Error processing chat message: {str(e)}")

    async def broadcast_message(self, message: str):
        """Broadcast a message to all connected clients"""
        for client in self.connected_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting message: {str(e)}")

    def run_fastapi(self):
        """Run the FastAPI server"""
        try:
            uvicorn.run(self.app, host="0.0.0.0", port=8000)
        except Exception as e:
            self.logger.error(f"Error running FastAPI server: {str(e)}")

def main(project_root: str) -> bool:
    """Main function to start the Chatbot+ module"""
    app = ChatbotPlus(config={
        "name": "Chatbot Plus",
        "version": "1.0.0",
        "settings": {
            "auto_connect": True,
            "max_messages": 1000,
            "message_delay": 1.0,
            "youtube": {
                "enabled": True,
                "auto_join": True
            }
        },
        "permissions": {
            "default": ["chat", "view"],
            "premium": ["chat", "view", "moderate", "use_premium_features"],
            "master": ["chat", "view", "moderate", "use_premium_features", "admin"]
        }
    })
    return app.start()

if __name__ == "__main__":
    main(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
