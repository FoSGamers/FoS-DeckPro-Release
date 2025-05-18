from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal

class BaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setup_ui()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
    def add_button(self, text: str, role: str = "accept"):
        button = QPushButton(text)
        if role == "accept":
            button.clicked.connect(self.accept)
        elif role == "reject":
            button.clicked.connect(self.reject)
        self.layout.addWidget(button)
        return button 