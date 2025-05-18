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
import tkinter.messagebox as messagebox
import tkinter as tk
from modules.logger import FoSLogger

from .unified_chat import UnifiedChatInterface
from .status_manager import StatusManager
from modules.youtube_login.youtube_client import YouTubeClient

# Initialize FoSLogger
logger = FoSLogger()

class ChatbotPlus:
    def __init__(self):
        logger.info("Initializing ChatbotPlus")
        self.app = None
        self.server = None
        self.connected_clients = set()
        self.chat_interface = None
        self.status_manager = None
        self.youtube_client = None
        self.project_root = None

    def start(self, project_root: str):
        """Start the Chatbot+ module"""
        logger.info("Starting Chatbot+ module")
        self.project_root = project_root
        
        try:
            # Initialize components
            self.initialize_components()
            
            # Create FastAPI app
            self.app = FastAPI()
            
            # Add CORS middleware
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Add WebSocket endpoint
            @self.app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                await websocket.accept()
                self.connected_clients.add(websocket)
                try:
                    while True:
                        data = await websocket.receive_text()
                        await self.process_chat_message(data)
                except Exception as e:
                    logger.error(f"WebSocket error: {str(e)}")
                finally:
                    self.connected_clients.remove(websocket)
            
            # Start the server in a separate thread
            self.server = threading.Thread(target=self.run_fastapi)
            self.server.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Chatbot+ module: {str(e)}")
            return False

    def stop(self):
        """Stop the Chatbot+ module"""
        logger.info("Stopping Chatbot+ module")
        if self.server:
            # Stop the FastAPI server
            self.server.join(timeout=1)
            self.server = None
        
        # Cleanup components
        self.cleanup()

    def initialize_components(self):
        """Initialize all required components"""
        logger.info("Initializing components")
        try:
            # Initialize YouTube client
            client_secrets_path = os.path.join(self.project_root, "modules", "chatbot_plus", "client_secrets.json")
            if not os.path.exists(client_secrets_path):
                logger.error(f"Client secrets file not found at: {client_secrets_path}")
                raise FileNotFoundError("YouTube API credentials not found")
            
            self.youtube_client = YouTubeClient(client_secrets_path, logger)
            
            # Authenticate with YouTube
            logger.debug("Attempting YouTube authentication")
            if not self.youtube_client.authenticate():
                logger.error("YouTube authentication failed")
                raise Exception("Failed to authenticate with YouTube")
            
            logger.info("Successfully authenticated with YouTube")
            
            # Initialize other components
            self.chat_interface = UnifiedChatInterface(self.youtube_client, logger)
            self.status_manager = StatusManager()
            
            logger.info("Components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise

    def cleanup(self):
        """Cleanup all components"""
        logger.info("Cleaning up components")
        if self.youtube_client:
            self.youtube_client.stop()
        if self.status_manager:
            self.status_manager.stop_status_checks()
        if self.chat_interface:
            self.chat_interface.cleanup()

    async def process_chat_message(self, message: str):
        """Process incoming chat messages"""
        try:
            # Process the message through the chat interface
            response = await self.chat_interface.process_message(message)
            
            # Broadcast the response to all connected clients
            await self.broadcast_message(response)
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")

    async def broadcast_message(self, message: str):
        """Broadcast a message to all connected clients"""
        for client in self.connected_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {str(e)}")

    def run_fastapi(self):
        """Run the FastAPI server"""
        try:
            uvicorn.run(self.app, host="0.0.0.0", port=8000)
        except Exception as e:
            logger.error(f"Error running FastAPI server: {str(e)}")

def main(project_root: str) -> bool:
    """Main function to start the Chatbot+ module"""
    app = ChatbotPlus()
    return app.start(project_root)

if __name__ == "__main__":
    main(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
