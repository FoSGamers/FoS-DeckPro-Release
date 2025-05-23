from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt

class ImportColumnMappingDialog(QDialog):
    """
    Dialog for mapping CSV columns to app fields.
    For each CSV column, user can select which app field it maps to (or 'Ignore').
    """
    def __init__(self, csv_columns, app_fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map CSV Columns to Fields")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.csv_columns = csv_columns
        self.app_fields = app_fields
        self.mapping = {}

        layout = QVBoxLayout(self)
        instructions = QLabel(
            "For each CSV column, select which field it should map to.\n"
            "Choose 'Ignore' to skip importing that column."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.table = QTableWidget(len(csv_columns), 2)
        self.table.setHorizontalHeaderLabels(["CSV Column", "Map to Field"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        for row, col_name in enumerate(csv_columns):
            self.table.setItem(row, 0, QTableWidgetItem(col_name))
            combo = QComboBox()
            combo.addItem("Ignore")
            combo.addItems(app_fields)
            # Try to auto-map by name
            for i, field in enumerate(app_fields, 1):
                if field.lower() == col_name.lower():
                    combo.setCurrentIndex(i)
                    break
            self.table.setCellWidget(row, 1, combo)
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def get_mapping(self):
        """
        Returns a dict: {csv_column: mapped_field or None}
        """
        mapping = {}
        for row in range(self.table.rowCount()):
            csv_col = self.table.item(row, 0).text()
            field = self.table.cellWidget(row, 1).currentText()
            mapping[csv_col] = field if field != "Ignore" else None
        return mapping 