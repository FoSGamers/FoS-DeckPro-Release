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
from plugins.youtube_login.youtube_client import YouTubeClient
from typing import Dict, Optional, Any
from .command_manager import CommandManager
from modules.logger import FoSLogger

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

class UnifiedChatInterface:
    def __init__(self, youtube_client: YouTubeClient, parent_window, base_dir):
        self.youtube_client = youtube_client
        self.parent = parent_window
        self.base_dir = base_dir
        self.logger = logging.getLogger("unified_chat")
        
        # Initialize command manager with proper path
        self.commands_file = os.path.join(self.base_dir, "commands.json")
        self.command_manager = CommandManager({"base_dir": self.base_dir})
        
        self.current_stream_id = None
        self.connected = False
        self.message_queue = queue.Queue()
        self.message_thread = None
        self.running = True
        self.processed_messages = set()  # Track processed messages
        
        # Create chat interface
        self.create_chat_interface()
        
        # Set up connection state sync
        if self.youtube_client:
            self.youtube_client.connection_callback = self._handle_connection_change
            if self.youtube_client.current_chat_id:
                self._handle_connection_change(True, self.youtube_client.current_stream_id)
        
        # Start message processing thread
        self.start_message_thread()

    def start_message_thread(self):
        """Start the message processing thread"""
        self.message_thread = threading.Thread(target=self._process_message_queue, daemon=True)
        self.message_thread.start()

    def _process_message_queue(self):
        """Process messages in the queue"""
        while self.running:
            try:
                message = self.message_queue.get(timeout=0.1)
                if message:
                    self._display_message(message)
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing message queue: {str(e)}")

    def _display_message(self, message: str):
        """Display a message in the chat window"""
        try:
            if not self.chat_display or not self.chat_display.winfo_exists():
                return
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            
            # Schedule the update in the main thread
            self.parent.after(0, self._safe_insert_message, formatted_message)
        except Exception as e:
            self.logger.error(f"Error displaying message: {str(e)}")

    def _safe_insert_message(self, message: str):
        """Safely insert a message into the chat display"""
        try:
            if self.chat_display and self.chat_display.winfo_exists():
                self.chat_display.insert("end", message)
                self.chat_display.see("end")
        except Exception as e:
            self.logger.error(f"Error inserting message: {str(e)}")

    def show_message(self, message: str):
        """Add a message to the queue"""
        try:
            self.message_queue.put(message)
        except Exception as e:
            self.logger.error(f"Error queueing message: {str(e)}")

    def handle_command(self, command: str) -> str:
        """Handle a command from the chat"""
        try:
            self.logger.debug(f"Handling command: {command}")
            
            # Get response from command manager
            response = self.command_manager.get_command_response(command)
            self.logger.debug(f"Command response: {response}")
            
            # Display the response
            self._display_message(f"Bot: {response}")
            
            # If connected to YouTube, send the response
            if self.youtube_client and self.youtube_client.is_connected():
                self.youtube_client.send_message(response)
                
            return response
            
        except Exception as e:
            error_msg = f"Error handling command: {str(e)}"
            self.logger.error(error_msg)
            self._display_message(f"Bot: {error_msg}")
            return error_msg
            
    def send_message(self, event=None):
        """Send a message from the input field"""
        try:
            message = self.message_input.get().strip()
            if not message:
                return
                
            self.logger.debug(f"Sending message: {message}")
                
            # Clear input field
            self.message_input.delete(0, tk.END)
            
            # Display user message
            self._display_message(f"You: {message}")
            
            # If it's a command, handle it
            if message.startswith('!'):
                self.logger.debug("Message is a command, processing...")
                self.handle_command(message)
            else:
                # Regular message - send to YouTube if connected
                if self.youtube_client and self.youtube_client.is_connected():
                    self.youtube_client.send_message(message)
                    
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            self.logger.error(error_msg)
            self._display_message(f"Bot: {error_msg}")

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.running = False
            if self.message_thread:
                self.message_thread.join(timeout=1.0)
            if hasattr(self, "main_frame"):
                self.main_frame.destroy()
            self.logger.info("Chat interface cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up: {str(e)}")

    def create_chat_interface(self):
        """Create the chat interface GUI"""
        try:
            # Create main frame that fills the window
            self.main_frame = ctk.CTkFrame(self.parent)
            self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)
            
            # Create header
            header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            header.pack(fill="x", pady=(0, 10))
            
            title = ctk.CTkLabel(header, 
                              text="Chatbot+",
                              font=("Arial", 24, "bold"))
            title.pack(side="left")
            
            # Chat display area with dark theme
            self.chat_display = ctk.CTkTextbox(
                self.main_frame,
                wrap="word",
                font=("Arial", 12)
            )
            self.chat_display.pack(expand=True, fill="both", padx=5, pady=5)
            
            # Control panel frame
            control_frame = ctk.CTkFrame(self.main_frame)
            control_frame.pack(fill="x", padx=5, pady=(0, 5))
            
            # Stream ID entry and connect button
            stream_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
            stream_frame.pack(fill="x", pady=2)
            
            stream_label = ctk.CTkLabel(stream_frame, text="Stream ID:", width=80)
            stream_label.pack(side="left", padx=5)
            
            self.stream_entry = ctk.CTkEntry(stream_frame)
            self.stream_entry.pack(side="left", expand=True, fill="x", padx=5)
            
            self.connect_button = ctk.CTkButton(
                stream_frame,
                text="Connect",
                command=self.connect_to_stream,
                width=100
            )
            self.connect_button.pack(side="right", padx=5)
            
            # Message input area
            input_frame = ctk.CTkFrame(self.main_frame)
            input_frame.pack(fill="x", padx=5, pady=5)
            
            self.message_input = ctk.CTkEntry(
                input_frame,
                placeholder_text="Type your message here..."
            )
            self.message_input.pack(side="left", expand=True, fill="x", padx=5)
            
            self.send_button = ctk.CTkButton(
                input_frame,
                text="Send",
                command=self.send_message,
                width=100
            )
            self.send_button.pack(side="right", padx=5)
            
            # Bind Enter key to send message
            self.message_input.bind("<Return>", lambda e: self.send_message())
            
            self.logger.info("Chat interface created successfully")
            
            # Show initial connection status
            self.show_message("Chat interface ready")
            if not self.connected:
                self.show_message("Not connected to any stream")
            
        except Exception as e:
            self.logger.error(f"Error creating chat interface: {str(e)}")
            raise

    def _handle_connection_change(self, connected: bool, stream_id: str = None):
        """Handle connection state changes from YouTube client"""
        try:
            self.connected = connected
            self.current_stream_id = stream_id
            
            # Update UI in main thread
            if self.parent and self.parent.winfo_exists():
                self.parent.after(0, self._update_connection_ui, connected, stream_id)
                
            if connected:
                self.show_message(f"Connected to stream {stream_id}")
                # Start chat listener in a new thread
                threading.Thread(
                    target=self._start_chat_listener,
                    daemon=True
                ).start()
            else:
                self.show_message("Disconnected from stream")
                # Try to reconnect after a delay
                if stream_id:
                    self.logger.info("Attempting to reconnect...")
                    self.parent.after(5000, self._attempt_reconnect, stream_id)
        except Exception as e:
            self.logger.error(f"Error handling connection change: {str(e)}")

    def _update_connection_ui(self, connected: bool, stream_id: str = None):
        """Update UI elements based on connection state"""
        try:
            if connected:
                self.connect_button.configure(text="Disconnect")
                if stream_id:
                    self.stream_entry.delete(0, tk.END)
                    self.stream_entry.insert(0, stream_id)
            else:
                self.connect_button.configure(text="Connect")
        except Exception as e:
            self.logger.error(f"Error updating connection UI: {str(e)}")

    def connect_to_stream(self):
        """Connect to a YouTube stream"""
        try:
            if self.connected:
                # Disconnect if already connected
                self._handle_connection_change(False)
                return
                
            stream_id = self.stream_entry.get().strip()
            if not stream_id:
                self.show_message("Please enter a stream ID")
                return
                
            def run_connect():
                try:
                    if self.youtube_client:
                        # Create event loop for async operations
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            # Run select_stream in the event loop
                            result = loop.run_until_complete(self.youtube_client.select_stream(stream_id))
                            if not result:
                                self.show_message(f"Failed to connect to stream {stream_id}")
                        finally:
                            loop.close()
                    else:
                        self.show_message("YouTube client not initialized")
                except Exception as e:
                    self.logger.error(f"Error connecting to stream: {str(e)}")
                    self.show_message(f"Error: {str(e)}")
            
            threading.Thread(target=run_connect, daemon=True).start()
            
        except Exception as e:
            self.logger.error(f"Error in connect_to_stream: {str(e)}")
            self.show_message(f"Error: {str(e)}")

    def _start_chat_listener(self):
        """Start listening to chat messages"""
        try:
            if not self.youtube_client or not self.connected:
                return
                
            # Set up message callback
            self.youtube_client.message_callback = self.handle_incoming_message
            
            # Start chat listener in a new thread
            threading.Thread(
                target=self._run_chat_listener,
                daemon=True
            ).start()
                
        except Exception as e:
            self.logger.error(f"Error starting chat listener: {str(e)}")
            self._handle_connection_change(False)

    def _run_chat_listener(self):
        """Run the chat listener in a new event loop"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.youtube_client.listen_to_chat())
            except Exception as e:
                self.logger.error(f"Error in chat listener: {str(e)}")
                self.show_message(f"Error in chat listener: {str(e)}")
                self._handle_connection_change(False)
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Error running chat listener: {str(e)}")
            self._handle_connection_change(False)

    async def handle_incoming_message(self, message: Dict[str, Any]) -> str:
        """Handle incoming chat messages"""
        try:
            if not message:
                return None
                
            # Get message details
            author = message["authorDetails"]["displayName"]
            content = message["snippet"]["displayMessage"]
            
            # Show the message in the chat
            self.show_message(f"{author}: {content}")
            
            # Check if it's a command
            if content.startswith('!'):
                # Process the command and return the response
                result = await self.handle_command(content, author)
                if result:
                    return f"@{author} {result}"
                return f"@{author} Unknown command. Type !help to see available commands"
                
            return None
                
        except Exception as e:
            self.logger.error(f"Error handling incoming message: {str(e)}")
            return None

    def _run_command_with_response(self, command: str, author: str):
        """Run command handling in a new event loop and send response to YouTube"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Get command result
                result = loop.run_until_complete(self.handle_command(command, author))
                
                # Show the result in the chat
                self.show_message(f"Command Result: {result}")
                
                # Send response to YouTube if connected
                if self.youtube_client and self.youtube_client.authenticated and self.connected:
                    # Format response
                    response = f"@{author} {result}"
                    # Send to YouTube with retry
                    success = loop.run_until_complete(self.youtube_client.send_message(response))
                    if not success:
                        self.logger.error("Failed to send command response to YouTube")
                        # Try one more time after a short delay
                        loop.run_until_complete(asyncio.sleep(1))
                        success = loop.run_until_complete(self.youtube_client.send_message(response))
                        if not success:
                            self.logger.error("Failed to send command response to YouTube after retry")
                    
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Error running command: {str(e)}")
            self.show_message(f"Error: {str(e)}")

    async def _get_help_message(self) -> str:
        """Get formatted help message"""
        try:
            help_message = "Available commands:\n"
            
            # Get all commands from the command manager
            for cmd, data in self.command_manager.commands.items():
                if data.get('enabled', True):
                    help_message += f"!{cmd} - {data.get('response', 'No description')}\n"
            
            return help_message
        except Exception as e:
            self.logger.error(f"Error getting help message: {str(e)}")
            return "An error occurred while getting help information."

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

    def _attempt_reconnect(self, stream_id: str):
        """Attempt to reconnect to the stream"""
        try:
            if not self.connected and self.youtube_client:
                self.logger.info(f"Attempting to reconnect to stream {stream_id}")
                threading.Thread(
                    target=self._run_reconnect,
                    args=(stream_id,),
                    daemon=True
                ).start()
        except Exception as e:
            self.logger.error(f"Error attempting reconnect: {str(e)}")

    def _run_reconnect(self, stream_id: str):
        """Run the reconnection process"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.youtube_client.connect_to_stream(stream_id))
                if result:
                    self.show_message("Successfully reconnected to stream")
                else:
                    self.show_message("Failed to reconnect - will try again later")
                    # Schedule another reconnection attempt
                    if self.parent and self.parent.winfo_exists():
                        self.parent.after(30000, self._attempt_reconnect, stream_id)
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"Error during reconnect: {str(e)}")
            self.show_message(f"Error during reconnect: {str(e)}") 