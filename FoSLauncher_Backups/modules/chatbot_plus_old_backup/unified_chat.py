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
from modules.chatbot_plus.stream_clients.youtube_client import YouTubeChatClient
from typing import Dict, Optional
from .command_manager import CommandManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FoSLauncher")

class UnifiedChatInterface:
    def __init__(self, base_dir: str, parent=None, youtube_client=None):
        self.base_dir = base_dir
        self.root = parent if parent else ctk.CTk()
        self.root.title("Unified Chat Interface")
        self.root.geometry("800x600")
        
        self.command_manager = CommandManager(base_dir)
        self.youtube_client = youtube_client  # Use provided YouTube client
        self.ws_connected = False
        self.ws_thread = None
        self.ws_client = None
        self.running = True
        self.permissions = set()
        
        self.create_chat_interface()
        self.start_websocket_client()
        
    def create_chat_interface(self) -> None:
        """Create the chat interface"""
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Chat display area
        self.chat_display = ctk.CTkTextbox(self.main_frame, wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.chat_display.configure(state='disabled')
        
        # Input area
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.message_input = ctk.CTkEntry(input_frame)
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.message_input.bind('<Return>', lambda e: self.send_message())
        
        send_button = ctk.CTkButton(input_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.RIGHT)
        
    def stop(self) -> None:
        """Stop the chat interface and clean up resources"""
        try:
            self.running = False
            if self.ws_client:
                asyncio.run(self.ws_client.close())
            if self.ws_thread:
                self.ws_thread.join(timeout=5)
            if self.youtube_client:
                self.youtube_client.disconnect()
            if self.root:
                self.root.quit()
        except Exception as e:
            logger.error(f"Error during stop: {e}")
            
    def cleanup(self) -> None:
        """Clean up resources (alias for stop)"""
        self.stop()
        
    def start_websocket_client(self) -> None:
        """Start the WebSocket client in a separate thread"""
        self.ws_thread = threading.Thread(target=self._ws_client_loop)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
    def _ws_client_loop(self) -> None:
        """WebSocket client loop"""
        while self.running:
            try:
                asyncio.run(self._ws_connect())
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.ws_connected = False
                if self.running:
                    time.sleep(5)  # Wait before reconnecting
            finally:
                if self.ws_client:
                    try:
                        asyncio.run(self.ws_client.close())
                    except Exception:
                        pass
                    self.ws_client = None
                    
    async def _ws_connect(self) -> None:
        """Connect to the WebSocket server"""
        max_retries = 3
        retry_count = 0
        retry_delay = 5  # seconds
        
        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect('ws://localhost:8001', ping_interval=30, ping_timeout=10) as websocket:
                    self.ws_client = websocket
                    self.ws_connected = True
                    self.display_message("Connected to chat server\n")
                    
                    while self.running:
                        try:
                            message = await websocket.recv()
                            if message:
                                self.display_message(f"{message}\n")
                        except websockets.exceptions.ConnectionClosed as e:
                            logger.warning(f"WebSocket connection closed: {e}")
                            break
                        except Exception as e:
                            logger.error(f"Error receiving message: {e}")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                self.ws_connected = False
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying WebSocket connection (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    
    def send_message(self, message: Optional[str] = None) -> None:
        """Send a message to the chat"""
        try:
            if message is None:
                message = self.message_input.get().strip()
                if not message:
                    return
                self.message_input.delete(0, tk.END)
                
            # Format and display the message
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            self.display_message(formatted_message)
            
            # Send to YouTube if connected
            if self.youtube_client and self.youtube_client.is_connected():
                try:
                    self.youtube_client.send_message(message)
                except Exception as e:
                    logger.error(f"Error sending message to YouTube: {e}")
                    self.display_message(f"Error sending message to YouTube: {str(e)}\n")
                    
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            self.display_message(f"Error sending message: {str(e)}\n")
            
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
            logger.error(f"Error handling YouTube command: {e}")
            return f"Error executing YouTube command: {str(e)}"
            
    def display_message(self, message: str) -> None:
        """Display a message in the chat"""
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, message)
        self.chat_display.see(tk.END)
        self.chat_display.configure(state='disabled')
        
    def run(self) -> None:
        """Run the chat interface"""
        # No need to call mainloop here as we're using the parent window's mainloop
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
                except Exception as e:
                    logger.error(f"Error sending message to YouTube: {e}")
                    self.display_message(f"Error sending message to YouTube: {str(e)}\n")
            
            return "Message processed successfully"
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error processing message: {str(e)}"
            
    async def handle_command(self, message: str) -> str:
        """Handle chat commands asynchronously"""
        try:
            if not isinstance(message, str) or not message.startswith('!'):
                return "Invalid command format"
                
            # Remove the ! prefix and split into parts
            parts = message[1:].split()
            if not parts:
                return "Invalid command format"
                
            # Get command category and name
            if len(parts) > 1:
                category = parts[0].lower()
                name = parts[1].lower()
            else:
                category = 'general'
                name = parts[0].lower()
                
            # Validate command format
            if not category or not name:
                return "Invalid command format"
                
            # Check if command exists
            command = self.command_manager.get_command(category, name)
            if not command:
                return "Unknown command. Type !help for available commands."
                
            # Check if command is enabled
            if not self.command_manager.is_command_enabled(category, name):
                return "This command is currently disabled."
                
            # Handle YouTube commands
            if category == 'youtube':
                return self.handle_youtube_command(name, parts[2:] if len(parts) > 2 else [])
                
            return f"Executing command: {category} {name}"
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return f"Error executing command: {str(e)}" 