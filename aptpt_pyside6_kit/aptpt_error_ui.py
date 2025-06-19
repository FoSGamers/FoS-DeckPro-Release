"""
Error UI module for APTPT.
Provides error dialogs, crash handling, and recovery UI components.
"""

from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton
from PySide6.QtCore import Qt
from aptpt_pyside6_kit.aptpt import log_aptpt_event

class APTPTErrorDialog(QDialog):
    """Enhanced error dialog with detailed information and recovery options."""
    
    def __init__(self, parent, event, description, variables, exception=None):
        super().__init__(parent)
        self.setWindowTitle("APTPT Error")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Error message
        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.message.setHtml(f"""
            <h3>Error: {description}</h3>
            <p><b>Event:</b> {event}</p>
            <p><b>Exception:</b> {str(exception) if exception else 'None'}</p>
        """)
        layout.addWidget(self.message)
        
        # Variables display
        self.variables = QTextEdit()
        self.variables.setReadOnly(True)
        self.variables.setMaximumHeight(150)
        var_text = "<h4>Context Variables:</h4><pre>"
        for k, v in variables.items():
            var_text += f"{k}: {v}\n"
        var_text += "</pre>"
        self.variables.setHtml(var_text)
        layout.addWidget(self.variables)
        
        # Buttons
        button_layout = QVBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.report_button = QPushButton("Generate Error Report")
        self.report_button.clicked.connect(self.generate_report)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.report_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def generate_report(self):
        """Generate a detailed error report."""
        # TODO: Implement error report generation
        pass

def show_aptpt_error_dialog(parent, event, description, variables, exception=None):
    """
    Show an APTPT error dialog with full context.
    
    Args:
        parent: Parent widget
        event: Event name/identifier
        description: Error description
        variables: Dictionary of context variables
        exception: Optional exception object
    """
    log_aptpt_event(event, description, variables, exception)
    dialog = APTPTErrorDialog(parent, event, description, variables, exception)
    dialog.exec()

def show_aptpt_warning(parent, event, description, variables):
    """
    Show an APTPT warning dialog.
    
    Args:
        parent: Parent widget
        event: Event name/identifier
        description: Warning description
        variables: Dictionary of context variables
    """
    log_aptpt_event(event, description, variables, level="WARN")
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("APTPT Warning")
    msg.setText(description)
    msg.setDetailedText("\n".join(f"{k}: {v}" for k, v in variables.items()))
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec() 