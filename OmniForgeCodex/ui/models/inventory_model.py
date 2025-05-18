from PySide6.QtCore import QAbstractTableModel, Qt, QTimer
from typing import List, Dict, Any

class InventoryModel(QAbstractTableModel):
    def __init__(self, inventory: List[Dict[str, Any]]):
        super().__init__()
        self._inventory = inventory
        self._undo_stack = []
        self._redo_stack = []
        self._last_save = None
        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self.autosave)
        self._autosave_timer.start(300000)  # Autosave every 5 minutes
        self.headers = ["Name", "Quantity", "Purchase Price", "Type", "CMC"]

    def rowCount(self, parent=None):
        return len(self._inventory)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            card = self._inventory[index.row()]
            col = index.column()
            if col == 0:
                return card["name"]
            elif col == 1:
                return str(card["quantity"])
            elif col == 2:
                return f"${card['purchase_price']:.2f}"
            elif col == 3:
                return card["type_line"]
            elif col == 4:
                return str(card["cmc"])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._undo_stack.append({
                'row': index.row(),
                'column': index.column(),
                'old_value': self.data(index, Qt.DisplayRole),
                'new_value': value
            })
            self._redo_stack.clear()
            
            card = self._inventory[index.row()]
            if index.column() == 0:
                card['name'] = value
            elif index.column() == 1:
                card['quantity'] = int(value)
            elif index.column() == 2:
                card['purchase_price'] = float(value.replace('$', ''))
            elif index.column() == 3:
                card['type_line'] = value
            elif index.column() == 4:
                card['cmc'] = int(value)
                
            self.dataChanged.emit(index, index)
            return True
        return False
        
    def undo(self):
        if self._undo_stack:
            action = self._undo_stack.pop()
            self._redo_stack.append(action)
            # Implement undo logic
            
    def redo(self):
        if self._redo_stack:
            action = self._redo_stack.pop()
            self._undo_stack.append(action)
            # Implement redo logic
            
    def autosave(self):
        if self._last_save != self._inventory:
            self._last_save = self._inventory.copy()
            # Implement autosave logic
