from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton
from PySide6.QtCore import Qt, Signal
from typing import List, Dict, Any, Optional
import json
import os
from config import Config

class RecentFilesWidget(QWidget):
    file_selected = Signal(str)  # Emitted when a file is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recent_files = []
        self.setup_ui()
        self.load_recent_files()
        
    def setup_ui(self):
        """Setup the recent files widget UI"""
        layout = QVBoxLayout(self)
        
        # Recent files list
        self.files_list = QListWidget()
        self.files_list.itemClicked.connect(self.on_file_selected)
        layout.addWidget(self.files_list)
        
        # Clear button
        clear_button = QPushButton("Clear Recent Files")
        clear_button.clicked.connect(self.clear_recent_files)
        layout.addWidget(clear_button)
        
    def load_recent_files(self):
        """Load recent files from settings"""
        try:
            if os.path.exists(Config.RECENT_FILES_PATH):
                with open(Config.RECENT_FILES_PATH, 'r') as f:
                    self.recent_files = json.load(f)
                self.update_files_list()
        except Exception as e:
            print(f"Error loading recent files: {e}")
            
    def update_files_list(self):
        """Update the files list widget"""
        self.files_list.clear()
        for file_path in self.recent_files:
            self.files_list.addItem(os.path.basename(file_path))
            
    def add_recent_file(self, file_path: str):
        """Add a file to recent files"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:10]  # Keep only 10 most recent
        self.save_recent_files()
        self.update_files_list()
        
    def clear_recent_files(self):
        """Clear recent files"""
        self.recent_files = []
        self.save_recent_files()
        self.update_files_list()
        
    def save_recent_files(self):
        """Save recent files to settings"""
        try:
            os.makedirs(os.path.dirname(Config.RECENT_FILES_PATH), exist_ok=True)
            with open(Config.RECENT_FILES_PATH, 'w') as f:
                json.dump(self.recent_files, f)
        except Exception as e:
            print(f"Error saving recent files: {e}")
            
    def on_file_selected(self, item):
        """Handle file selection"""
        index = self.files_list.row(item)
        if 0 <= index < len(self.recent_files):
            self.file_selected.emit(self.recent_files[index]) 