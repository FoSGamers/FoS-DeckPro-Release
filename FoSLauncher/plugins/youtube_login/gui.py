import tkinter as tk
import customtkinter as ctk
import logging

class YouTubeLoginGUI:
    def __init__(self, youtube_client: YouTubeClient, base_dir: str):
        self.youtube_client = youtube_client
        self.base_dir = base_dir
        self.logger = logging.getLogger("youtube_login_gui")
        self.root = None
        self.stream_list = None
        self.connect_button = None
        self.status_label = None
        self.running = False

    def create_gui(self):
        """Create the GUI"""
        try:
            self.root = ctk.CTk()
            self.root.title("YouTube Login")
            self.root.geometry("600x400")
            
            # Create main frame
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(expand=True, fill="both", padx=10, pady=10)
            
            # Create stream list
            stream_frame = ctk.CTkFrame(main_frame)
            stream_frame.pack(expand=True, fill="both", padx=5, pady=5)
            
            stream_label = ctk.CTkLabel(stream_frame, text="Available Streams:")
            stream_label.pack(pady=5)
            
            self.stream_list = ctk.CTkTextbox(stream_frame, height=200)
            self.stream_list.pack(expand=True, fill="both", padx=5, pady=5)
            
            # Create control buttons
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill="x", padx=5, pady=5)
            
            self.connect_button = ctk.CTkButton(
                button_frame,
                text="Connect",
                command=self.connect_to_stream
            )
            self.connect_button.pack(side="left", padx=5)
            
            refresh_button = ctk.CTkButton(
                button_frame,
                text="Refresh",
                command=self.refresh_streams
            )
            refresh_button.pack(side="left", padx=5)
            
            # Create status label
            self.status_label = ctk.CTkLabel(main_frame, text="Status: Ready")
            self.status_label.pack(pady=5)
            
            # Set up window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)
            
            # Initial refresh
            self.refresh_streams()
            
        except Exception as e:
            self.logger.error(f"Error creating GUI: {str(e)}")
            raise

    def on_close(self):
        """Handle window close"""
        try:
            self.running = False
            if self.root:
                self.root.destroy()
        except Exception as e:
            self.logger.error(f"Error closing GUI: {str(e)}")

    def refresh_streams(self):
        """Refresh the stream list"""
        try:
            if not self.youtube_client or not self.youtube_client.authenticated:
                self.status_label.configure(text="Status: Not authenticated")
                return
                
            self.status_label.configure(text="Status: Refreshing streams...")
            
            # Get available streams
            streams = self.youtube_client.list_available_streams()
            if isinstance(streams, str):
                self.status_label.configure(text=f"Status: {streams}")
                return
                
            # Update stream list
            self.stream_list.delete("1.0", tk.END)
            for stream in streams:
                self.stream_list.insert("end", f"{stream['title']} (ID: {stream['id']})\n")
                
            self.status_label.configure(text="Status: Ready")
            
        except Exception as e:
            self.logger.error(f"Error refreshing streams: {str(e)}")
            self.status_label.configure(text=f"Status: Error - {str(e)}")

    def connect_to_stream(self):
        """Connect to the selected stream"""
        try:
            if not self.youtube_client or not self.youtube_client.authenticated:
                self.status_label.configure(text="Status: Not authenticated")
                return
                
            # Get selected stream ID
            selection = self.stream_list.get("1.0", tk.END).strip()
            if not selection:
                self.status_label.configure(text="Status: No stream selected")
                return
                
            # Extract stream ID
            stream_id = selection.split("(ID: ")[1].rstrip(")")
            
            self.status_label.configure(text=f"Status: Connecting to stream {stream_id}...")
            
            # Connect to stream
            result = self.youtube_client.connect_to_stream(stream_id)
            if result:
                self.status_label.configure(text=f"Status: Connected to stream {stream_id}")
            else:
                self.status_label.configure(text="Status: Failed to connect")
                
        except Exception as e:
            self.logger.error(f"Error connecting to stream: {str(e)}")
            self.status_label.configure(text=f"Status: Error - {str(e)}")

    def run(self):
        """Run the GUI"""
        try:
            self.running = True
            self.create_gui()
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"Error running GUI: {str(e)}")
            raise 