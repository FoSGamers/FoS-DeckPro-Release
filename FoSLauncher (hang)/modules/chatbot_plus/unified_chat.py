import tkinter as tk
import customtkinter as ctk
import json
import os
import logging
import asyncio
import websockets
import threading
import queue
import time
from datetime import datetime
from modules.youtube_login.youtube_client import YouTubeClient
from typing import Dict, Optional, Any
from .command_manager import CommandManager
from modules.logger import FoSLogger

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

class UnifiedChatInterface:
    def __init__(self, base_dir: str, parent: Optional[ctk.CTk] = None, youtube_client: Optional[Any] = None, logger: FoSLogger = None):
        """Initialize the unified chat interface"""
        self.base_dir = base_dir
        self.parent = parent
        self.youtube_client = youtube_client
        self.ws_client = None
        self.ws_connected = False
        self.ws_task = None
        
        # Set up logging
        self.logger = logger or FoSLogger()
        self.logger.info("UnifiedChatInterface initialized")
        
        # Create GUI
        self.create_chat_interface()
        
        # Start WebSocket client
        self.start_websocket_client()
        
    def create_chat_interface(self):
        """Create the chat interface GUI"""
        try:
            # Create main frame
            self.main_frame = ctk.CTkFrame(self.parent)
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create chat display
            self.chat_display = ctk.CTkTextbox(self.main_frame)
            self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
            self.chat_display.configure(state="disabled")
            
            # Create input frame
            self.input_frame = ctk.CTkFrame(self.main_frame)
            self.input_frame.pack(fill="x", padx=5, pady=5)
            
            # Create message entry
            self.message_entry = ctk.CTkEntry(self.input_frame)
            self.message_entry.pack(side="left", fill="x", expand=True, padx=5)
            self.message_entry.bind("<Return>", self.send_message)
            
            # Create send button
            self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message)
            self.send_button.pack(side="right", padx=5)
            
            self.logger.debug("Chat interface created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating chat interface: {e}")
            raise
            
    def start_websocket_client(self):
        """Start the WebSocket client"""
        try:
            self.ws_task = asyncio.create_task(self._ws_client_loop())
            self.logger.debug("WebSocket client started")
        except Exception as e:
            self.logger.error(f"Error starting WebSocket client: {e}")
            
    async def _ws_client_loop(self):
        """WebSocket client main loop"""
        while True:
            try:
                if not self.ws_connected:
                    await self._ws_connect()
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in WebSocket client loop: {e}")
                self.ws_connected = False
                await asyncio.sleep(5)  # Wait before reconnecting
                
    async def _ws_connect(self):
        """Connect to the WebSocket server"""
        try:
            self.ws_client = await websockets.connect("ws://localhost:8001")
            self.ws_connected = True
            self.logger.info("Connected to WebSocket server")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            self.logger.error(f"Error connecting to WebSocket server: {e}")
            self.ws_connected = False
            
    async def _listen_for_messages(self):
        """Listen for messages from the WebSocket server"""
        try:
            while self.ws_connected:
                try:
                    message = await self.ws_client.recv()
                    await self.process_message(message)
                except websockets.exceptions.ConnectionClosed:
                    self.logger.warning("WebSocket connection closed")
                    self.ws_connected = False
                    break
                except Exception as e:
                    self.logger.error(f"Error receiving message: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in message listener: {e}")
            self.ws_connected = False
            
    def send_message(self, event=None):
        """Send a message through the WebSocket"""
        try:
            message = self.message_entry.get().strip()
            if not message:
                return
                
            # Clear the input
            self.message_entry.delete(0, "end")
            
            # Display the message
            self.display_message("You", message)
            
            # Send through WebSocket
            if self.ws_connected:
                asyncio.create_task(self._send_ws_message(message))
                
            # Send to YouTube if connected
            if self.youtube_client and self.youtube_client.is_connected():
                self.youtube_client.send_message(message)
                
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            
    async def _send_ws_message(self, message: str):
        """Send a message through the WebSocket"""
        try:
            if not self.ws_connected or not self.ws_client:
                self.logger.warning("WebSocket not connected")
                return
                
            await self.ws_client.send(json.dumps({
                "type": "chat",
                "content": message
            }))
            
        except Exception as e:
            self.logger.error(f"Error sending WebSocket message: {e}")
            self.ws_connected = False
            
    def display_message(self, sender: str, message: str):
        """Display a message in the chat display"""
        try:
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", f"{sender}: {message}\n")
            self.chat_display.see("end")
            self.chat_display.configure(state="disabled")
        except Exception as e:
            self.logger.error(f"Error displaying message: {e}")
            
    async def process_message(self, message: str) -> str:
        """Process a received message"""
        try:
            # Parse the message
            data = json.loads(message)
            message_type = data.get("type")
            content = data.get("content")
            
            if message_type == "chat":
                # Display the message
                self.display_message("Bot", content)
                return content
                
            elif message_type == "error":
                self.logger.error(f"Received error message: {content}")
                return f"Error: {content}"
                
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                return f"Unknown message type: {message_type}"
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"Error processing message: {str(e)}"
            
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.ws_client:
                asyncio.create_task(self.ws_client.close())
            if self.ws_task:
                self.ws_task.cancel()
            self.logger.debug("Chat interface cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def handle_youtube_command(self, command: str, args: list) -> str:
        """Handle YouTube-specific commands"""
        try:
            if not self.youtube_client:
                return "YouTube client not initialized"
                
            if not isinstance(command, str) or not isinstance(args, list):
                return "Invalid command format"
                
            if command == 'auth':
                if self.youtube_client.authenticate():
                    return "Successfully authenticated with YouTube"
                return "Failed to authenticate with YouTube"
                
            elif command == 'list':
                streams = self.youtube_client.list_available_streams()
                if isinstance(streams, list):
                    if not streams:
                        return "No active streams found"
                    return "Available streams:\n" + "\n".join(f"- {s['title']} (ID: {s['id']})" for s in streams)
                return str(streams)
                
            elif command == 'connect':
                if not args:
                    return "Please specify a stream ID to connect to"
                if not isinstance(args[0], str):
                    return "Invalid stream ID format"
                if self.youtube_client.connect_to_stream(args[0]):
                    return f"Connected to stream {args[0]}"
                return f"Failed to connect to stream {args[0]}"
                
            elif command == 'disconnect':
                self.youtube_client.disconnect()
                return "Disconnected from stream"
                
            return f"Unknown YouTube command: {command}"
                
        except Exception as e:
            self.logger.error(f"Error handling YouTube command: {e}")
            return f"Error executing YouTube command: {str(e)}"
            
    def run(self) -> None:
        """Run the chat interface"""
        pass

    def has_permission(self, permission_type):
        """Check if the user has a specific permission"""
        if permission_type == "master":
            return "master" in self.permissions
        elif permission_type == "premium":
            return "use_premium_features" in self.permissions or "master" in self.permissions
        return permission_type in self.permissions 

    async def process_message(self, content: str) -> str:
        """Process a chat message and return a response"""
        try:
            if not isinstance(content, str):
                return "Invalid message format"
                
            # Check if it's a command
            if content.startswith('!'):
                return await self.handle_command(content)
            
            # Process regular message
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {content}\n"
            self.display_message(formatted_message)
            
            # Send to YouTube if connected
            if self.youtube_client and self.youtube_client.is_connected():
                try:
                    self.youtube_client.send_message(content)
                    self.logger.debug(f"Message sent to YouTube: {content}")
                except Exception as e:
                    self.logger.error(f"Error sending message to YouTube: {e}")
                    self.display_message(f"Error sending message to YouTube: {str(e)}\n")
            
            return "Message processed successfully"
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"Error processing message: {str(e)}"
            
    async def handle_command(self, message: str) -> str:
        """Handle a command"""
        try:
            parts = message.split()
            if not parts:
                return "Invalid command format"
                
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # Check if it's a YouTube command
            if command.startswith('yt_'):
                return self.handle_youtube_command(command[3:], args)
                
            # Check if it's a built-in command
            if command == 'help':
                return "Available commands: !help, !yt_auth, !yt_connect, !yt_disconnect, !yt_status"
                
            return f"Unknown command: {command}"
            
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            return f"Error: {str(e)}"

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming chat messages from any platform"""
        try:
            platform = message.get("platform")
            if not platform:
                self.logger.error("No platform specified in message")
                return {"error": "No platform specified"}
                
            if platform == "youtube":
                return await self.handle_youtube_message(message)
            else:
                self.logger.warning(f"Unsupported platform: {platform}")
                return {"error": f"Unsupported platform: {platform}"}
                
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
            return {"error": str(e)}
            
    async def handle_youtube_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle YouTube-specific chat messages"""
        try:
            # Extract message content
            content = message.get("content")
            if not content:
                self.logger.error("No content in YouTube message")
                return {"error": "No message content"}
                
            # Process message using YouTube client
            self.logger.debug(f"Processing YouTube message: {content}")
            response = await self.youtube_client.process_message(content)
            
            return {"success": True, "response": response}
            
        except Exception as e:
            self.logger.error(f"Error handling YouTube message: {str(e)}")
            return {"error": str(e)} 