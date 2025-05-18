from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, Optional

class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the status widget UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Status labels
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.status_label)
        
        self.progress_label = QLabel()
        self.progress_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.progress_label)
        
    def set_status(self, message: str):
        """Set the status message"""
        self.status_label.setText(message)
        
    def set_progress(self, message: str):
        """Set the progress message"""
        self.progress_label.setText(message)
        
    def clear(self):
        """Clear all status messages"""
        self.status_label.clear()
        self.progress_label.clear() 