# File: modules/chatbot_plus/main.py

import os
import sys
import json
import logging
import asyncio
import threading
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import customtkinter as ctk
import tkinter.messagebox as messagebox
import tkinter as tk
from typing import Dict, Any, Optional
from modules.logger import logger

from .stream_clients.youtube_client import YouTubeChatClient
from .unified_chat import UnifiedChatInterface
from .status_manager import StatusManager
from modules.chatbot_plus.youtube_client import YouTubeClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FoSLauncher")

# Create FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
connected_clients = set()
youtube_client = None
chat_interface = None
status_manager = StatusManager()

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

def show_error(root: Optional[tk.Tk], message: str) -> None:
    """Show an error message in the main thread"""
    if root:
        root.after(0, lambda: messagebox.showerror("Error", message))
    else:
        logger.error(message)

def initialize_components(root: Optional[tk.Tk] = None) -> bool:
    """Initialize all components"""
    try:
        # Load configurations
        config_path = os.path.join(project_root, "config.json")
        if not os.path.exists(config_path):
            show_error(root, "Configuration file not found")
            return False
            
        with open(config_path, "r") as f:
            config = json.load(f)
            
        # Initialize YouTube client
        try:
            client_secrets_path = os.path.join(project_root, "modules", "chatbot_plus", "client_secrets.json")
            logger.debug(f"Looking for client secrets at: {client_secrets_path}")
            
            if not os.path.exists(client_secrets_path):
                logger.error(f"Client secrets file not found at: {client_secrets_path}")
                show_error(root, "YouTube API credentials not found. Please set up your credentials.")
                return False
                
            logger.debug("Found client secrets file, initializing YouTube client")
            youtube_client = YouTubeClient(client_secrets_path)
            
            # Authenticate with YouTube
            logger.debug("Attempting YouTube authentication")
            if not youtube_client.authenticate(root):
                logger.error("YouTube authentication failed")
                show_error(root, "Failed to authenticate with YouTube. Please check your credentials.")
                return False
                
            logger.info("Successfully authenticated with YouTube")
            
        except Exception as e:
            show_error(root, f"Error initializing YouTube client: {str(e)}")
            return False
            
        # Initialize other components...
        
        return True
        
    except Exception as e:
        show_error(root, f"Failed to initialize components: {str(e)}")
        return False

def cleanup():
    """Clean up resources before shutdown"""
    try:
        if youtube_client:
            youtube_client.stop()
        if status_manager:
            status_manager.stop_status_checks()
        if chat_interface:
            chat_interface.cleanup()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections"""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"New client connected. Total clients: {len(connected_clients)}")
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if not isinstance(message, dict):
                    raise ValueError("Message must be a JSON object")
                
                message_type = message.get("type")
                if not message_type:
                    raise ValueError("Message must have a 'type' field")
                
                if message_type == "chat":
                    content = message.get("content")
                    if not content:
                        raise ValueError("Chat message must have 'content' field")
                    
                    # Process chat message
                    response = await process_chat_message(content)
                    await websocket.send_text(json.dumps({
                        "type": "chat",
                        "content": response
                    }))
                    
                elif message_type == "status":
                    # Handle status updates
                    status = message.get("status")
                    if status:
                        await broadcast_message({
                            "type": "status",
                            "status": status
                        })
                
                else:
                    raise ValueError(f"Unknown message type: {message_type}")
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid message format"
                }))
            except ValueError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Internal server error"
                }))
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client removed. Total clients: {len(connected_clients)}")

async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients"""
    if not connected_clients:
        logger.warning("No connected clients to broadcast to")
        return
        
    disconnected_clients = set()
    for client in connected_clients:
        try:
            await client.send_text(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)
        except Exception as e:
            logger.error(f"Error broadcasting to client: {e}")
            disconnected_clients.add(client)
    
    # Clean up disconnected clients
    for client in disconnected_clients:
        connected_clients.remove(client)

async def process_chat_message(content: str) -> str:
    """Process a chat message and return a response"""
    try:
        if not chat_interface:
            logger.error("Chat interface not initialized")
            return "Error: Chat interface not initialized"
            
        # Process the message through the chat interface
        response = await chat_interface.process_message(content)
        return response
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return "Sorry, I encountered an error processing your message."

def run_fastapi():
    """Run the FastAPI server"""
    try:
        # Create event loop for the server thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the server
        config = uvicorn.Config(app, host="127.0.0.1", port=8001, loop=loop)
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())
    except Exception as e:
        logger.error(f"Failed to start server on port 8001: {e}")
        try:
            # Try alternative port
            config = uvicorn.Config(app, host="127.0.0.1", port=8002, loop=loop)
            server = uvicorn.Server(config)
            loop.run_until_complete(server.serve())
        except Exception as e:
            logger.error(f"Failed to start server on port 8002: {e}")

def main(root: Optional[tk.Tk] = None) -> None:
    """Main entry point for the chatbot plus module"""
    try:
        logger.info("Starting FoSGamers Chatbot+")
        
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logger.debug(f"Project root: {project_root}")
        
        if not initialize_components(root):
            return
            
        # Start the main module functionality
        logger.info("Chatbot Plus module started successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        show_error(root, f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Create a temporary root window if running directly
    root = tk.Tk()
    root.withdraw()  # Hide the window
    main(root)
    root.mainloop()
