import os
import sys
import json
from typing import Dict, Any, Optional
import tkinter as tk
from tkinter import messagebox
from modules.logger import FoSLogger
from modules.youtube_login.youtube_client import YouTubeClient
import logging

logger = logging.getLogger(__name__)

def show_error(root: Optional[tk.Tk], message: str) -> None:
    """Show an error message in the main thread"""
    if root and isinstance(root, (tk.Tk, tk.Toplevel)):
        root.after(0, lambda: messagebox.showerror("Error", message))
    else:
        logger.error(f"Error: {message}")

def show_info(root: Optional[tk.Tk], message: str) -> None:
    """Show an info message in the main thread"""
    if root and isinstance(root, (tk.Tk, tk.Toplevel)):
        root.after(0, lambda: messagebox.showinfo("Information", message))
    else:
        logger.info(message)

def initialize(logger: FoSLogger) -> None:
    """Initialize the YouTube login module"""
    logger.info("YouTube login module initialized")

class YouTubeLogin:
    def __init__(self):
        logger.info("Initializing YouTubeLogin")
        self.root = None
        self.client_secrets_path = None
        self.credentials_path = None
        self.project_root = None

    def start(self, project_root: str):
        """Start the YouTube login GUI"""
        logger.info("Starting YouTube login GUI")
        self.project_root = project_root
        self.client_secrets_path = os.path.join(project_root, "modules", "youtube_login", "client_secrets.json")
        self.credentials_path = os.path.join(project_root, "modules", "youtube_login", "credentials.json")

        if not os.path.exists(self.client_secrets_path):
            logger.error(f"Client secrets file not found at: {self.client_secrets_path}")
            messagebox.showerror("Error", "YouTube API credentials not found. Please set up your credentials.")
            return False

        self.root = tk.Tk()
        self.root.title("YouTube Login")
        self.root.geometry("400x200")
        
        # Create main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill="both")
        
        # Add login button
        login_button = tk.Button(main_frame, text="Login to YouTube", 
                               command=self.authenticate,
                               font=("Arial", 12))
        login_button.pack(pady=20)
        
        # Start the main loop
        self.root.mainloop()
        return True

    def stop(self):
        """Stop the YouTube login GUI"""
        logger.info("Stopping YouTube login GUI")
        if self.root:
            self.root.quit()
            self.root.destroy()
            self.root = None

    def authenticate(self):
        """Handle YouTube authentication"""
        logger.info("Starting YouTube authentication")
        try:
            # Import YouTubeClient here to avoid circular imports
            from .youtube_client import YouTubeClient
            
            client = YouTubeClient(self.client_secrets_path, self.credentials_path)
            if client.authenticate():
                messagebox.showinfo("Success", "Successfully authenticated with YouTube!")
                self.stop()
            else:
                messagebox.showerror("Error", "Failed to authenticate with YouTube.")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            messagebox.showerror("Error", f"Authentication failed: {str(e)}")

def main(project_root: str) -> bool:
    """Main function to start the YouTube login module"""
    app = YouTubeLogin()
    return app.start(project_root)

if __name__ == "__main__":
    main(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) 