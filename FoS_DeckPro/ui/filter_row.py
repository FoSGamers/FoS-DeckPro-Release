from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel

class FilterRow(QWidget):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Filter:"))
        self.filters = {}
        for col in columns:
            filt = QLineEdit()
            filt.setPlaceholderText(col)
            layout.addWidget(filt)
            self.filters[col] = filt
        self.setLayout(layout)
