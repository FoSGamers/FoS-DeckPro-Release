from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem, QLabel
)
from PySide6.QtCore import Qt, Signal

class ColumnCustomizationDialog(QDialog):
    """
    Dialog for customizing columns: show/hide with checkboxes, drag & drop to reorder, and restore defaults.
    """
    def __init__(self, columns, visible_columns, default_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Columns")
        self.setMinimumWidth(400)
        self.columns = columns.copy()
        self.visible_columns = set(visible_columns)
        self.default_columns = default_columns.copy()

        layout = QVBoxLayout(self)
        instructions = QLabel("Check columns to show, drag to reorder. Restore Defaults resets order and visibility.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Create list widget with proper drag-drop settings
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDropIndicatorShown(True)
        layout.addWidget(self.list_widget)

        # Add items with proper flags
        for col in self.columns:
            item = QListWidgetItem(col)
            item.setFlags(
                Qt.ItemIsEnabled |
                Qt.ItemIsSelectable |
                Qt.ItemIsUserCheckable |
                Qt.ItemIsDragEnabled |
                Qt.ItemIsDropEnabled
            )
            item.setCheckState(Qt.Checked if col in self.visible_columns else Qt.Unchecked)
            self.list_widget.addItem(item)

        # Add buttons
        btns = QHBoxLayout()
        restore_btn = QPushButton("Restore Defaults")
        restore_btn.clicked.connect(self.restore_defaults)
        btns.addWidget(restore_btn)
        btns.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def restore_defaults(self):
        """Reset columns to default order and visibility."""
        self.list_widget.clear()
        for col in self.default_columns:
            item = QListWidgetItem(col)
            item.setFlags(
                Qt.ItemIsEnabled |
                Qt.ItemIsSelectable |
                Qt.ItemIsUserCheckable |
                Qt.ItemIsDragEnabled |
                Qt.ItemIsDropEnabled
            )
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)

    def get_columns(self):
        """
        Returns (ordered_columns, visible_columns) after customization.
        """
        ordered = []
        visible = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            col = item.text()
            ordered.append(col)
            if item.checkState() == Qt.Checked:
                visible.append(col)
        return ordered, visible 