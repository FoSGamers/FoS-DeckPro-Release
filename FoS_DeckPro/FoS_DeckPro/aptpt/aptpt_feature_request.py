from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, List, Optional
from .aptpt import log_aptpt_event

class FeatureRequestDialog(QDialog):
    feature_requested = Signal(str, str, List[str])  # name, description, requirements
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Request New Feature")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add name field
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Feature Name:"))
        
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        
        layout.addLayout(name_layout)
        
        # Add description field
        layout.addWidget(QLabel("Description:"))
        
        self.description_edit = QTextEdit()
        layout.addWidget(self.description_edit)
        
        # Add requirements field
        layout.addWidget(QLabel("Requirements:"))
        
        self.requirements_edit = QTextEdit()
        self.requirements_edit.setPlaceholderText(
            "Enter requirements, one per line"
        )
        layout.addWidget(self.requirements_edit)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self._submit_request)
        button_layout.addWidget(self.submit_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Log dialog creation
        log_aptpt_event(
            'info',
            'Feature request dialog created',
            {'timestamp': datetime.now().isoformat()}
        )
    
    def _submit_request(self) -> None:
        """Submit feature request."""
        try:
            # Get values
            name = self.name_edit.text().strip()
            description = self.description_edit.toPlainText().strip()
            requirements = [
                req.strip()
                for req in self.requirements_edit.toPlainText().split('\n')
                if req.strip()
            ]
            
            # Validate
            if not name:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Please enter a feature name"
                )
                return
            
            if not description:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Please enter a description"
                )
                return
            
            # Emit signal
            self.feature_requested.emit(name, description, requirements)
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                "Feature request submitted successfully!"
            )
            
            # Close dialog
            self.accept()
            
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to submit feature request: {e}"
            )
            
            # Log error
            log_aptpt_event(
                'error',
                'Failed to submit feature request',
                {'error': str(e)}
            )

def show_feature_request_dialog(parent=None) -> Optional[Dict[str, Any]]:
    """Show the feature request dialog."""
    try:
        dialog = FeatureRequestDialog(parent)
        if dialog.exec():
            return {
                'name': dialog.name_edit.text().strip(),
                'description': dialog.description_edit.toPlainText().strip(),
                'requirements': [
                    req.strip()
                    for req in dialog.requirements_edit.toPlainText().split('\n')
                    if req.strip()
                ]
            }
        return None
    except Exception as e:
        log_aptpt_event(
            'error',
            'Failed to show feature request dialog',
            {'error': str(e)}
        )
        return None 