from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QLabel,
    QWidget, QScrollArea
)
from PySide6.QtCore import Qt, Signal

class ColumnItem(QWidget):
    """Widget for each column in the list, with a checkbox and label."""
    def __init__(self, column_name, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.label = QLabel(column_name)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()

    def is_checked(self):
        return self.checkbox.isChecked()

    def set_checked(self, checked):
        self.checkbox.setChecked(checked)

    def column_name(self):
        return self.label.text()

class ExportColumnsDialog(QDialog):
    """Dialog for selecting and ordering columns for CSV export."""
    
    def __init__(self, all_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select and Order Export Columns")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Select columns to export and drag to reorder them.\n"
            "Unchecked columns will not be included in the export."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Column list
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        layout.addWidget(self.list_widget)
        
        # Populate the list
        for column in all_columns:
            item = QListWidgetItem(self.list_widget)
            column_widget = ColumnItem(column)
            item.setSizeHint(column_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, column_widget)
        
        # Buttons for selecting/deselecting all
        button_layout = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self.select_all_columns)
        deselect_all = QPushButton("Deselect All")
        deselect_all.clicked.connect(self.deselect_all_columns)
        button_layout.addWidget(select_all)
        button_layout.addWidget(deselect_all)
        layout.addLayout(button_layout)
        
        # Dialog buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def select_all_columns(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            widget.set_checked(True)

    def deselect_all_columns(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            widget.set_checked(False)

    def get_selected_columns(self):
        """Returns list of selected column names in current order."""
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget.is_checked():
                selected.append(widget.column_name())
        return selected 