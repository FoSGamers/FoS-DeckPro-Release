import os
import sys
import json
import logging
import threading
from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from modules.logger import logger
from modules.chatbot_plus.unified_chat import UnifiedChatInterface
from modules.youtube_login.youtube_client import YouTubeClient

def show_error(root: Optional[tk.Tk], message: str) -> None:
    """Show an error message in the main thread"""
    if root:
        root.after(0, lambda: messagebox.showerror("Error", message))
    else:
        logger.error(message)

def main(project_root: str = None, root: Optional[tk.Tk] = None, config: Dict[str, Any] = None) -> None:
    """Main entry point for the unified chat module"""
    try:
        logger.info("Starting Unified Chat initialization")
        
        # Get the project root directory
        if not project_root:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logger.debug(f"Project root directory: {project_root}")
        logger.debug(f"Current module path: {os.path.abspath(__file__)}")
        
        # Initialize YouTube client
        client_secrets_path = os.path.join(project_root, "modules", "chatbot_plus", "client_secrets.json")
        logger.debug(f"Looking for client secrets at: {client_secrets_path}")
        logger.debug(f"Client secrets exists: {os.path.exists(client_secrets_path)}")
        
        if not os.path.exists(client_secrets_path):
            logger.error("YouTube API credentials not found")
            if root:
                root.after(0, lambda: messagebox.showerror(
                    "Error",
                    "YouTube API credentials not found. Please set up your credentials."
                ))
            return
            
        logger.debug("Found client secrets file, initializing YouTube client")
        youtube_client = YouTubeClient(client_secrets_path)
        logger.debug("YouTube client initialized successfully")
        
        # Check for token file
        token_path = os.path.join(os.path.dirname(client_secrets_path), "token.json")
        logger.debug(f"Looking for token file at: {token_path}")
        logger.debug(f"Token file exists: {os.path.exists(token_path)}")
        
        # Create chat window in main thread
        if root:
            # If we have a root window, create the chat interface in it
            chat_window = root
        else:
            # Create a new window in the main thread
            def create_window():
                nonlocal chat_window
                chat_window = ctk.CTk()
                chat_window.title("Unified Chat")
                chat_window.geometry("800x600")
                
            if threading.current_thread() is threading.main_thread():
                create_window()
            else:
                chat_window = None
                root = tk.Tk()
                root.withdraw()  # Hide the temporary root window
                root.after(0, create_window)
                root.mainloop()
                
        logger.debug("New chat window created successfully")
        
        # Initialize chat interface
        logger.debug("Initializing chat interface with parameters:")
        logger.debug(f"- Project root: {project_root}")
        logger.debug(f"- Chat window: {chat_window}")
        logger.debug(f"- YouTube client: {youtube_client}")
        
        chat_interface = UnifiedChatInterface(project_root, chat_window, youtube_client)
        logger.debug("Chat interface initialized successfully")
        
        if not root:
            chat_window.mainloop()
            
    except Exception as e:
        logger.error(f"Failed to initialize chat interface", exc_info=True)
        if root:
            root.after(0, lambda: messagebox.showerror("Error", f"Failed to initialize chat interface: {str(e)}"))

if __name__ == "__main__":
    main() 