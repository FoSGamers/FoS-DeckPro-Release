from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTextEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, List, Optional
from .aptpt_feature import APTPTFeatureManager
from .aptpt import log_aptpt_event

class FeatureImplementationDialog(QDialog):
    feature_implemented = Signal(str, dict)  # feature name, result

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("APTPT Feature Implementation")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Initialize feature manager
        self.feature_manager = APTPTFeatureManager()
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Add feature selection
        selection_layout = QHBoxLayout()
        
        self.feature_combo = QComboBox()
        self.feature_combo.currentTextChanged.connect(self._on_feature_selected)
        selection_layout.addWidget(QLabel("Feature:"))
        selection_layout.addWidget(self.feature_combo)
        
        layout.addLayout(selection_layout)
        
        # Add feature details
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)
        
        # Add requirements list
        requirements_layout = QVBoxLayout()
        requirements_layout.addWidget(QLabel("Requirements:"))
        
        self.requirements_list = QListWidget()
        requirements_layout.addWidget(self.requirements_list)
        
        layout.addLayout(requirements_layout)
        
        # Add dependencies list
        dependencies_layout = QVBoxLayout()
        dependencies_layout.addWidget(QLabel("Dependencies:"))
        
        self.dependencies_list = QListWidget()
        dependencies_layout.addWidget(self.dependencies_list)
        
        layout.addLayout(dependencies_layout)
        
        # Add implementation options
        options_layout = QHBoxLayout()
        
        self.auto_fix_checkbox = QCheckBox("Auto-fix requirements")
        self.auto_fix_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_fix_checkbox)
        
        self.retry_checkbox = QCheckBox("Retry on failure")
        self.retry_checkbox.setChecked(True)
        options_layout.addWidget(self.retry_checkbox)
        
        layout.addLayout(options_layout)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.implement_button = QPushButton("Implement")
        self.implement_button.clicked.connect(self._implement_feature)
        button_layout.addWidget(self.implement_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initialize UI
        self._update_feature_list()
        
        # Log dialog creation
        log_aptpt_event(
            'info',
            'Feature implementation dialog created',
            {'timestamp': datetime.now().isoformat()}
        )

    def _update_feature_list(self) -> None:
        """Update the feature combo box."""
        self.feature_combo.clear()
        for name in sorted(self.feature_manager.features.keys()):
            self.feature_combo.addItem(name)

    def _on_feature_selected(self, feature_name: str) -> None:
        """Handle feature selection."""
        try:
            if not feature_name:
                return
            
            # Get feature status
            status = self.feature_manager.get_feature_status(feature_name)
            
            # Update details
            details = f"""
            Name: {status['name']}
            Description: {status['description']}
            Status: {status['status']}
            Error Count: {status['error_count']}
            Last Success: {status['last_success'] or 'Never'}
            Last Error: {status['last_error'] or 'None'}
            """
            self.details_text.setPlainText(details)
            
            # Update requirements
            self.requirements_list.clear()
            for req in status['requirements']:
                item = QListWidgetItem(req)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.requirements_list.addItem(item)
            
            # Update dependencies
            self.dependencies_list.clear()
            for dep in status['dependencies']:
                dep_status = self.feature_manager.get_feature_status(dep)
                item = QListWidgetItem(f"{dep} ({dep_status['status']})")
                self.dependencies_list.addItem(item)
            
        except Exception as e:
            log_aptpt_event(
                'error',
                'Failed to update feature details',
                {
                    'feature': feature_name,
                    'error': str(e)
                }
            )

    def _implement_feature(self) -> None:
        """Implement the selected feature."""
        try:
            feature_name = self.feature_combo.currentText()
            if not feature_name:
                return
            
            # Get selected requirements
            requirements = []
            for i in range(self.requirements_list.count()):
                item = self.requirements_list.item(i)
                if item.checkState() == Qt.Checked:
                    requirements.append(item.text())
            
            # Implement feature
            result = self.feature_manager.implement_feature(
                feature_name,
                auto_fix=self.auto_fix_checkbox.isChecked(),
                retry=self.retry_checkbox.isChecked(),
                requirements=requirements
            )
            
            # Emit signal
            self.feature_implemented.emit(feature_name, result)
            
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Feature '{feature_name}' implemented successfully!"
            )
            
            # Close dialog
            self.accept()
            
        except Exception as e:
            # Show error message
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to implement feature: {e}"
            )
            
            # Log error
            log_aptpt_event(
                'error',
                'Feature implementation failed',
                {
                    'feature': feature_name,
                    'error': str(e)
                }
            )

def show_feature_implementation_dialog(parent=None) -> Optional[Dict[str, Any]]:
    """Show the feature implementation dialog."""
    try:
        dialog = FeatureImplementationDialog(parent)
        if dialog.exec():
            return dialog.feature_manager.get_feature_status(
                dialog.feature_combo.currentText()
            )
        return None
    except Exception as e:
        log_aptpt_event(
            'error',
            'Failed to show feature implementation dialog',
            {'error': str(e)}
        )
        return None 