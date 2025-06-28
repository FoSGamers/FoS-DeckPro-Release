from PySide6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QTextEdit,
    QPushButton, QHBoxLayout, QLabel, QCheckBox
)
from PySide6.QtCore import Qt
from typing import Dict, Any, Optional
from .aptpt import log_aptpt_event

class APTPTErrorDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add error message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Add context display
        if context:
            context_label = QLabel("Context:")
            layout.addWidget(context_label)
            
            context_text = QTextEdit()
            context_text.setReadOnly(True)
            context_text.setPlainText(str(context))
            layout.addWidget(context_text)
        
        # Add recovery options
        recovery_layout = QHBoxLayout()
        
        self.retry_checkbox = QCheckBox("Retry operation")
        self.retry_checkbox.setChecked(True)
        recovery_layout.addWidget(self.retry_checkbox)
        
        self.adapt_checkbox = QCheckBox("Adapt thresholds")
        self.adapt_checkbox.setChecked(True)
        recovery_layout.addWidget(self.adapt_checkbox)
        
        layout.addLayout(recovery_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Log dialog creation
        log_aptpt_event(
            'info',
            'Error dialog created',
            {
                'title': title,
                'message': message,
                'context': context
            }
        )

    def get_recovery_options(self) -> Dict[str, bool]:
        """Get selected recovery options."""
        return {
            'retry': self.retry_checkbox.isChecked(),
            'adapt': self.adapt_checkbox.isChecked()
        }

def show_aptpt_error_dialog(
    parent,
    function_name: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None
) -> None:
    """Show an APTPT error dialog with recovery options."""
    try:
        # Log error
        log_aptpt_event(
            'error',
            message,
            {
                'function': function_name,
                'context': context
            },
            exception
        )
        
        # Create and show dialog
        dialog = APTPTErrorDialog(
            f"Error in {function_name}",
            message,
            context,
            parent
        )
        
        if dialog.exec():
            # Get recovery options
            options = dialog.get_recovery_options()
            
            # Log recovery action
            log_aptpt_event(
                'recovery',
                'User selected recovery options',
                {
                    'function': function_name,
                    'options': options
                }
            )
            
            # TODO: Implement recovery actions based on options
    except Exception as e:
        # If error dialog fails, show basic message box
        QMessageBox.critical(
            parent,
            "Error",
            f"Failed to show error dialog: {e}"
        )

def show_aptpt_warning(
    parent,
    function_name: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Show an APTPT warning dialog."""
    try:
        # Log warning
        log_aptpt_event(
            'warning',
            message,
            {
                'function': function_name,
                'context': context
            }
        )
        
        # Show warning dialog
        QMessageBox.warning(
            parent,
            f"Warning in {function_name}",
            message
        )
    except Exception as e:
        # If warning dialog fails, show basic message box
        QMessageBox.warning(
            parent,
            "Warning",
            f"Failed to show warning dialog: {e}"
        ) 