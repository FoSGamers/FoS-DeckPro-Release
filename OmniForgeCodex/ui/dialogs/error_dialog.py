from .base_dialog import BaseDialog
from PySide6.QtWidgets import QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class ErrorDialog(BaseDialog):
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        layout = QVBoxLayout()
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        self.add_button("OK", "accept") 