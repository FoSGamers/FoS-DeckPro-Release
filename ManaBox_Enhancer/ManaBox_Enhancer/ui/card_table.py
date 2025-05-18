from PySide6.QtWidgets import QTableView, QMenu
from PySide6.QtCore import QAbstractTableModel, Qt, Signal, QModelIndex

class CardTableModel(QAbstractTableModel):
    def __init__(self, cards=None, columns=None):
        super().__init__()
        self.cards = cards if cards is not None else []
        self.columns = columns if columns is not None else ["Name", "Set", "Collector Number"]

    def rowCount(self, parent=None):
        return len(self.cards) + 1  # +1 for the blank filter row

    def columnCount(self, parent=None):
        return len(self.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        if index.row() == 0:
            return ""  # Blank filter row
        card = self.cards[index.row() - 1]
        col = self.columns[index.column()]
        return str(card.get(col, ""))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.columns[section]
        return None

    def set_cards(self, cards):
        self.beginResetModel()
        self.cards = cards
        self.endResetModel()

class CardTableView(QTableView):
    card_selected = Signal(dict)
    edit_card_requested = Signal(int)  # row index
    delete_card_requested = Signal(list)  # list of row indices

    def __init__(self, inventory, columns, parent=None):
        super().__init__(parent)
        self.model = CardTableModel([], columns)
        self.setModel(self.model)
        self.setMinimumHeight(300)
        self.inventory = inventory
        self.columns = columns
        self.cards = []
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.doubleClicked.connect(self.on_double_click)

        # Enable both horizontal and vertical scrollbars as needed
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QTableView.ScrollPerPixel)
        self.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideNone)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)

        # Set default column widths for clarity
        default_widths = {
            "Name": 180,
            "Set name": 140,
            "Set code": 80,
            "Collector number": 90,
            "Rarity": 80,
            "Condition": 90,
            "Foil": 60,
            "Language": 80,
            "Purchase price": 100,
            "Whatnot price": 100
        }
        for i, col in enumerate(self.columns):
            self.setColumnWidth(i, default_widths.get(col, 100))

    def update_cards(self, cards):
        self.cards = cards
        self.model.set_cards(cards)

    def on_selection_changed(self, selected, deselected):
        indexes = self.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            if row == 0:
                return  # Ignore blank filter row
            if 0 < row <= len(self.cards):
                self.card_selected.emit(self.cards[row - 1])

    def show_context_menu(self, pos):
        index = self.indexAt(pos)
        if not index.isValid() or index.row() == 0:
            return
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Card")
        delete_action = menu.addAction("Delete Card(s)")
        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == edit_action:
            self.edit_card_requested.emit(index.row() - 1)
        elif action == delete_action:
            rows = sorted(set(idx.row() - 1 for idx in self.selectedIndexes() if idx.row() > 0))
            if rows:
                self.delete_card_requested.emit(rows)

    def on_double_click(self, index: QModelIndex):
        if index.isValid() and index.row() > 0:
            self.edit_card_requested.emit(index.row() - 1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            rows = sorted(set(idx.row() - 1 for idx in self.selectedIndexes() if idx.row() > 0))
            if rows:
                self.delete_card_requested.emit(rows)
        else:
            super().keyPressEvent(event)
