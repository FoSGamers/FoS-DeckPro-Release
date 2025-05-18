from PySide6.QtCore import QAbstractTableModel, Qt

class DeckModel(QAbstractTableModel):
    def __init__(self, deck):
        super().__init__()
        self.deck = deck.get("mainboard", [])
        self.headers = ["Count", "Name", "Type", "CMC"]

    def rowCount(self, parent=None):
        return len(self.deck)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            card, count = self.deck[index.row()]
            col = index.column()
            if col == 0:
                return str(count)
            elif col == 1:
                return card["name"]
            elif col == 2:
                return card["type_line"]
            elif col == 3:
                return str(card["cmc"])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None
