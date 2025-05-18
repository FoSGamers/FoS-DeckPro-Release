import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import logging
from datetime import datetime
import re

class ChatSplitterApp:
    def __init__(self, parent, base_dir, config):
        self.parent = parent
        self.base_dir = base_dir
        self.config = config
        self.logger = logging.getLogger("chatsplitter.gui")
        
        # Initialize variables
        self.output_dir = os.path.join(base_dir, config.get('default_output_dir', 'output'))
        self.image_dir = os.path.join(base_dir, config.get('default_image_dir', 'images'))
        self.max_file_size_mb = config.get('max_file_size_mb', 25)
        self.user_name = "FoSGamers"
        
        # Create directories if they don't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Set up the GUI elements"""
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(self.main_frame, 
                           text="Chat Splitter",
                           font=("Arial", 24, "bold"))
        title.pack(pady=(0, 20))
        
        # File selection frame
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", pady=10)
        
        # JSON file selection
        json_label = ctk.CTkLabel(file_frame, text="Chat JSON File:")
        json_label.pack(anchor="w", padx=10, pady=5)
        
        json_button_frame = ctk.CTkFrame(file_frame)
        json_button_frame.pack(fill="x", padx=10)
        
        self.json_path_var = tk.StringVar()
        json_entry = ctk.CTkEntry(json_button_frame, textvariable=self.json_path_var)
        json_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        json_button = ctk.CTkButton(json_button_frame, 
                                  text="Browse",
                                  command=self.browse_json)
        json_button.pack(side="right")
        
        # Output directory selection
        output_label = ctk.CTkLabel(file_frame, text="Output Directory:")
        output_label.pack(anchor="w", padx=10, pady=5)
        
        output_button_frame = ctk.CTkFrame(file_frame)
        output_button_frame.pack(fill="x", padx=10)
        
        self.output_path_var = tk.StringVar(value=self.output_dir)
        output_entry = ctk.CTkEntry(output_button_frame, textvariable=self.output_path_var)
        output_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        output_button = ctk.CTkButton(output_button_frame, 
                                    text="Browse",
                                    command=self.browse_output)
        output_button.pack(side="right")
        
        # Settings frame
        settings_frame = ctk.CTkFrame(self.main_frame)
        settings_frame.pack(fill="x", pady=10)
        
        # User name
        name_label = ctk.CTkLabel(settings_frame, text="Your Name:")
        name_label.pack(anchor="w", padx=10, pady=5)
        
        self.name_var = tk.StringVar(value=self.user_name)
        name_entry = ctk.CTkEntry(settings_frame, textvariable=self.name_var)
        name_entry.pack(fill="x", padx=10)
        
        # File size limit
        size_label = ctk.CTkLabel(settings_frame, text="Max File Size (MB):")
        size_label.pack(anchor="w", padx=10, pady=5)
        
        self.size_var = tk.StringVar(value=str(self.max_file_size_mb))
        size_entry = ctk.CTkEntry(settings_frame, textvariable=self.size_var)
        size_entry.pack(fill="x", padx=10)
        
        # Process button
        self.process_button = ctk.CTkButton(self.main_frame,
                                          text="Split Chats",
                                          command=self.process_chats)
        self.process_button.pack(pady=20)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.main_frame, text="")
        self.status_label.pack(pady=10)
        
    def browse_json(self):
        """Browse for JSON file"""
        file_path = filedialog.askopenfilename(
            title="Select Chat JSON File",
            filetypes=[("JSON files", "*.json")]
        )
        if file_path:
            self.json_path_var.set(file_path)
            
    def browse_output(self):
        """Browse for output directory"""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_path_var.set(dir_path)
            
    def process_chats(self):
        """Process the chat JSON file"""
        try:
            # Get paths
            json_file = self.json_path_var.get()
            output_dir = self.output_path_var.get()
            
            # Validate inputs
            if not json_file or not os.path.exists(json_file):
                messagebox.showerror("Error", "Please select a valid JSON file")
                return
                
            if not output_dir:
                messagebox.showerror("Error", "Please select an output directory")
                return
                
            # Get settings
            try:
                self.max_file_size_mb = float(self.size_var.get())
                if self.max_file_size_mb <= 0:
                    raise ValueError("File size must be positive")
            except ValueError:
                messagebox.showerror("Error", "Invalid file size limit")
                return
                
            self.user_name = self.name_var.get().strip() or "FoSGamers"
            
            # Process the file
            self.status_label.configure(text="Processing chats...")
            # TODO: Implement chat processing logic
            self.status_label.configure(text="Chats processed successfully!")
            
        except Exception as e:
            self.logger.error(f"Error processing chats: {str(e)}")
            messagebox.showerror("Error", f"Failed to process chats: {str(e)}")
            self.status_label.configure(text="Error processing chats")
            
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy() 