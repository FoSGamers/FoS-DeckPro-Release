from .base_dialog import BaseDialog
from PySide6.QtWidgets import QProgressBar, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal

class ProgressDialog(BaseDialog):
    cancelled = Signal()
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModal)
        
        layout = QVBoxLayout()
        self.label = QLabel()
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate progress
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        
        self.add_button("Cancel", "reject")
        
    def set_progress(self, value: int, maximum: int = 100):
        self.progress.setRange(0, maximum)
        self.progress.setValue(value)
        
    def set_message(self, message: str):
        self.label.setText(message) 