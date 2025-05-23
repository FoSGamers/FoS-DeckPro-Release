from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QHBoxLayout

class BulkEditRemoveDialog(QDialog):
    def __init__(self, cards, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Edit/Remove Filtered Cards")
        self.result = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Filtered cards: {len(cards)}"))
        # Remove all
        remove_btn = QPushButton("Remove All Filtered Cards")
        remove_btn.clicked.connect(self.remove_all)
        layout.addWidget(remove_btn)
        # Bulk edit
        layout.addWidget(QLabel("Bulk Edit Field for All Filtered Cards:"))
        edit_row = QHBoxLayout()
        self.field_combo = QComboBox()
        self.field_combo.addItems(columns)
        edit_row.addWidget(self.field_combo)
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("New value")
        edit_row.addWidget(self.value_edit)
        edit_btn = QPushButton("Apply Bulk Edit")
        edit_btn.clicked.connect(self.bulk_edit)
        edit_row.addWidget(edit_btn)
        layout.addLayout(edit_row)
        # Cancel
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
    def remove_all(self):
        self.result = ("remove", None, None)
        self.accept()
    def bulk_edit(self):
        field = self.field_combo.currentText()
        value = self.value_edit.text()
        if not field:
            return
        self.result = ("edit", field, value)
        self.accept()
    def get_result(self):
        return self.result 