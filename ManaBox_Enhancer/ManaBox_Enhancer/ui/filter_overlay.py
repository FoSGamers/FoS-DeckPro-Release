from PyQt6.QtWidgets import QWidget, QLineEdit
from PyQt6.QtCore import Qt, QRect, QEvent

class FilterOverlay(QWidget):
    HEIGHT = 28
    def __init__(self, table, columns, parent=None):
        super().__init__(parent or table.viewport())
        self.table = table
        self.columns = columns
        self.filters = {}
        self.setFixedHeight(self.HEIGHT)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: rgba(255,255,255,0.8);")
        for col in columns:
            filt = QLineEdit(self)
            filt.setPlaceholderText(col)
            self.filters[col] = filt
        self.table.viewport().installEventFilter(self)
        self.table.horizontalHeader().sectionResized.connect(self.update_positions)
        self.table.horizontalHeader().sectionMoved.connect(self.update_positions)
        self.table.horizontalScrollBar().valueChanged.connect(self.update_positions)
        self.update_positions()

    def update_positions(self):
        # Overlay sits at y=0 in the viewport, width matches viewport
        self.setGeometry(0, 0, self.table.viewport().width(), self.HEIGHT)
        for i, col in enumerate(self.columns):
            idx = self.table.model.columns.index(col)
            x = self.table.columnViewportPosition(idx)
            width = self.table.columnWidth(idx)
            self.filters[col].setGeometry(QRect(x, 0, width, self.HEIGHT))

    def eventFilter(self, obj, event):
        if obj is self.table.viewport():
            if event.type() in (QEvent.Resize, QEvent.Paint, QEvent.Move):
                self.update_positions()
        return super().eventFilter(obj, event) 