import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
import tkinter as tk
from tkinter import messagebox, ttk
import logging
import webbrowser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from pathlib import Path
from datetime import datetime
import traceback
from core.plugins.plugin_interface import PluginInterface, PluginDependency
import customtkinter as ctk
from .youtube_client import YouTubeClient
from .gui import YouTubeLoginApp

logger = logging.getLogger("youtube_login")

def show_error(root: Optional[tk.Tk], message: str) -> None:
    """Show an error message in the main thread"""
    try:
        if root and isinstance(root, (tk.Tk, tk.Toplevel)) and root.winfo_exists():
            root.after(0, lambda: messagebox.showerror("Error", message))
        else:
            logger.error(f"Error: {message}")
    except Exception as e:
        logger.error(f"Error showing error message: {str(e)}")
        logger.error(f"Original message: {message}")

def show_info(root: Optional[tk.Tk], message: str) -> None:
    """Show an info message in the main thread"""
    try:
        if root and isinstance(root, (tk.Tk, tk.Toplevel)) and root.winfo_exists():
            root.after(0, lambda: messagebox.showinfo("Information", message))
        else:
            logger.info(message)
    except Exception as e:
        logger.error(f"Error showing info message: {str(e)}")
        logger.error(f"Original message: {message}")

def initialize() -> None:
    """Initialize the YouTube login module"""
    logger.info("YouTube login module initialized")

class StreamSelector(tk.Toplevel):
    def __init__(self, parent, youtube_client):
        logger.debug("Initializing StreamSelector")
        try:
            if not parent or not parent.winfo_exists():
                logger.error("Invalid parent window")
                raise ValueError("Invalid parent window")
            
            super().__init__(parent)
            
            self.youtube_client = youtube_client
            self.selected_stream = None
            self._is_running = True
            
            # Make window modal and visible
            logger.debug("Setting up window properties")
            self.lift()  # Lift window to top
            self.focus_force()  # Force focus
            self.transient(parent)
            self.grab_set()
            
            # Set up window close handler
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            
            self.title("YouTube Stream Selector")
            self.geometry("800x400")  # Made wider to accommodate new column
            
            self.setup_ui()
            
            # Center the window
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            x = (self.winfo_screenwidth() // 2) - (width // 2)
            y = (self.winfo_screenheight() // 2) - (height // 2)
            self.geometry(f'{width}x{height}+{x}+{y}')
            
            # Load streams after a short delay to let the window appear
            self.after(100, self.refresh_streams)
            
            logger.debug("StreamSelector initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing StreamSelector: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
            
    def setup_ui(self):
        """Set up the user interface"""
        try:
            logger.debug("Setting up UI components")
            
            # Create main frame with padding
            self.main_frame = ttk.Frame(self, padding="10")
            self.main_frame.pack(expand=True, fill="both")
            
            # Add status label
            self.status_label = ttk.Label(self.main_frame, text="Loading streams...", anchor="center")
            self.status_label.pack(fill="x", pady=(0, 10))
            
            # Create treeview frame
            tree_frame = ttk.Frame(self.main_frame)
            tree_frame.pack(expand=True, fill="both")
            
            # Create treeview with privacy column
            self.tree = ttk.Treeview(tree_frame, columns=("title", "status", "privacy", "start_time"), show="headings", selectmode="browse")
            self.tree.heading("title", text="Stream Title")
            self.tree.heading("status", text="Status")
            self.tree.heading("privacy", text="Privacy")
            self.tree.heading("start_time", text="Start Time")
            
            # Configure column widths
            self.tree.column("title", width=300, minwidth=200)
            self.tree.column("status", width=100, minwidth=80)
            self.tree.column("privacy", width=100, minwidth=80)
            self.tree.column("start_time", width=150, minwidth=120)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack tree and scrollbar
            self.tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add buttons
            button_frame = ttk.Frame(self.main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            refresh_btn = ttk.Button(button_frame, text="Refresh", command=self.refresh_streams)
            refresh_btn.pack(side="left", padx=5)
            
            select_btn = ttk.Button(button_frame, text="Select Stream", command=self.select_stream)
            select_btn.pack(side="right", padx=5)
            
            # Double click to select stream
            self.tree.bind('<Double-1>', lambda e: self.select_stream())
            
            logger.debug("UI setup completed")
            
        except Exception as e:
            logger.error(f"Error setting up UI: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
    def on_close(self):
        """Handle window close"""
        logger.debug("Closing StreamSelector")
        try:
            if not self._is_running:
                return
                
            self._is_running = False
            self.grab_release()
            self.destroy()
            
        except Exception as e:
            logger.error(f"Error closing StreamSelector: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
        
    def refresh_streams(self):
        """Refresh the list of available streams"""
        logger.debug("Refreshing streams")
        try:
            self.status_label.config(text="Loading streams...")
            self.update_idletasks()
            
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get streams from YouTube client
            streams = self.youtube_client.list_available_streams()
            
            if isinstance(streams, str):
                self.status_label.config(text=f"Error: {streams}")
                return
            
            if not streams:
                self.status_label.config(text="No streams found")
                return
            
            # Add streams to treeview
            for stream in streams:
                start_time = stream.get("actual_start_time") or stream.get("scheduled_start_time", "")
                if start_time:
                    try:
                        # Convert to datetime and format
                        dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        start_time = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception as e:
                        logger.warning(f"Error formatting date: {str(e)}")
                
                self.tree.insert("", "end", values=(
                    stream["title"],
                    stream["status"],
                    stream.get("privacy", "unknown").title(),
                    start_time
                ), tags=(stream["id"],))
            
            # Select first item
            if self.tree.get_children():
                self.tree.selection_set(self.tree.get_children()[0])
                self.tree.focus_set()
            
            self.status_label.config(text=f"Found {len(streams)} stream(s)")
            logger.debug(f"Refreshed streams: found {len(streams)} stream(s)")
            
        except Exception as e:
            error_msg = f"Error refreshing streams: {str(e)}"
            self.status_label.config(text=error_msg)
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            
    def select_stream(self):
        """Select the highlighted stream"""
        logger.debug("Selecting stream")
        try:
            selection = self.tree.selection()
            if not selection:
                show_error(self, "Please select a stream")
                return
            
            # Get the stream ID from the item's tags
            stream_id = self.tree.item(selection[0])["tags"][0]
            
            self.status_label.config(text="Connecting to stream...")
            self.update_idletasks()
            
            # Try to connect to the stream
            if self.connect_to_stream(stream_id):
                show_info(self, "Successfully connected to stream!")
                self.on_close()
            else:
                # Get the last error message from the logger
                error_msg = "Failed to connect to stream"
                for handler in self.youtube_client.logger.handlers:
                    if isinstance(handler, logging.Handler):
                        if handler.formatter and hasattr(handler, 'buffer'):
                            for record in reversed(handler.buffer):
                                if record.levelno >= logging.ERROR:
                                    error_msg = record.getMessage()
                                    break
                
                self.status_label.config(text="Failed to connect to stream")
                show_error(self, error_msg)
                
        except Exception as e:
            error_msg = f"Error selecting stream: {str(e)}"
            self.status_label.config(text=error_msg)
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            show_error(self, error_msg)

    def connect_to_stream(self, stream_id: str) -> bool:
        """Connect to a specific stream"""
        try:
            if not self.youtube_client:
                self.logger.error("YouTube client not initialized")
                return False

            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Run select_stream in the event loop
                result = loop.run_until_complete(self.youtube_client.select_stream(stream_id))
                return result
            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"Error connecting to stream: {str(e)}")
            return False

class YouTubeLogin:
    def __init__(self):
        logger.info("Initializing YouTubeLogin")
        self.root = None
        self.client_secrets_path = None
        self.token_path = None
        self.project_root = None
        self.credentials = None
        self._window_created = False
        self._parent = None
        self._is_running = False

    def create_window(self, parent=None):
        """Create the login window"""
        logger.info("Creating YouTube login window")
        
        if self._window_created:
            logger.warning("Window already exists")
            return
            
        self._parent = parent
        if parent:
            self.root = tk.Toplevel(parent)
        else:
            self.root = tk.Tk()
            
        self.root.title("YouTube Login")
        self.root.geometry("400x200")
        
        # Make window modal
        if parent:
            self.root.transient(parent)
            self.root.grab_set()
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill="both")
        
        # Add login button
        login_button = ttk.Button(main_frame, text="Login to YouTube", 
                               command=self.authenticate)
        login_button.pack(pady=20)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
        
        # Ensure window is visible and focused
        self.root.lift()
        self.root.focus_force()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self._window_created = True
        logger.info("YouTube login window created and displayed")

    def on_close(self):
        """Handle window close"""
        logger.info("Closing YouTube login window")
        self.stop()

    def start(self, project_root: str, parent=None):
        """Start the YouTube login GUI"""
        if self._is_running:
            logger.warning("YouTube login GUI is already running")
            return True
            
        logger.info("Starting YouTube login GUI")
        self.project_root = project_root
        
        # Set up paths
        self.client_secrets_path = os.path.join(project_root, "plugins", "youtube_login", "client_secrets.json")
        self.token_path = os.path.join(project_root, "config", "modules", "youtube_login", "token.pickle")
        
        # Create token directory if it doesn't exist
        os.makedirs(os.path.dirname(self.token_path), exist_ok=True)

        if not os.path.exists(self.client_secrets_path):
            logger.error(f"Client secrets file not found at: {self.client_secrets_path}")
            show_error(parent, "YouTube API credentials not found. Please set up your credentials.")
            return False

        try:
            # Create and show the window
            self.create_window(parent)
            self._is_running = True
            
            if not parent:
                # Start the main loop if we're the main window
                self.root.mainloop()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting YouTube login GUI: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.stop()
            return False

    def stop(self):
        """Stop the YouTube login GUI"""
        if not self._is_running:
            return
            
        logger.info("Stopping YouTube login GUI")
        try:
            if self.root:
                if self._parent:
                    self.root.grab_release()  # Release modal state
                self.root.quit()
                self.root.destroy()
                self.root = None
                self._window_created = False
                self._parent = None
            self._is_running = False
        except Exception as e:
            logger.error(f"Error stopping YouTube login GUI: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    def authenticate(self):
        """Handle YouTube authentication"""
        logger.info("Starting YouTube authentication")
        try:
            # Load client secrets
            with open(self.client_secrets_path, 'r') as f:
                client_secrets = json.load(f)

            # Create OAuth2 flow
            flow = InstalledAppFlow.from_client_config(
                client_secrets,
                scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
            )

            # Hide the main window during authentication
            if self.root:
                self.root.withdraw()

            try:
                # Run the flow to get credentials
                self.credentials = flow.run_local_server(port=0)
                
                # Save the credentials
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
                
                logger.info("Successfully authenticated with YouTube")
                show_info(self.root, "Successfully authenticated with YouTube!")
            finally:
                # Ensure window is shown again if authentication fails
                if self.root:
                    self.root.deiconify()
                    self.root.lift()
                    self.root.focus_force()
            
            self.stop()
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            show_error(self.root, f"Authentication failed: {str(e)}")

def main(project_root: str) -> bool:
    """Main function to start the YouTube login module"""
    app = YouTubeLogin()
    return app.start(project_root)

class YouTubeLoginPlugin(PluginInterface):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_dir = config.get('base_dir', "plugins/youtube_login")
        self.app = None
        self.window = None
        self.logger = logging.getLogger("youtube_login")

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[PluginDependency]:
        return []

    def get_name(self) -> str:
        return "youtube_login"

if __name__ == "__main__":
    main(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) 