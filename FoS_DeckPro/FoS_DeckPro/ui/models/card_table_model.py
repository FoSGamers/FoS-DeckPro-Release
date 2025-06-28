from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from typing import List, Dict, Any

class CardTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict[str, Any]] = None, columns: List[str] = None):
        super().__init__()
        self._data = data or []
        self._columns = columns or []
        self._headers = self._columns if self._columns else []
        if self._data and not self._columns:
            self._headers = list(self._data[0].keys()) if self._data else []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if 0 <= row < len(self._data) and 0 <= col < len(self._headers):
                return str(self._data[row].get(self._headers[col], ""))

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if 0 <= section < len(self._headers):
                    return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        if role == Qt.EditRole:
            row = index.row()
            col = index.column()
            if 0 <= row < len(self._data) and 0 <= col < len(self._headers):
                self._data[row][self._headers[col]] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def updateData(self, new_data: List[Dict[str, Any]]):
        self.beginResetModel()
        self._data = new_data
        if self._data and not self._columns:
            self._headers = list(self._data[0].keys())
        self.endResetModel()

    def update_cards(self, new_cards: List[Dict[str, Any]]):
        """Update the cards data and refresh the model."""
        self.beginResetModel()
        self._data = new_cards
        if self._data and not self._columns:
            self._headers = list(self._data[0].keys())
        self.endResetModel()

    def _update_pagination(self):
        """Placeholder method for pagination - the actual pagination is handled by CardTableView."""
        pass

    @property
    def cards(self) -> List[Dict[str, Any]]:
        """Get the current cards data."""
        return self._data

    @property
    def columns(self) -> List[str]:
        """Get the current columns."""
        return self._headers

    @columns.setter
    def columns(self, new_columns: List[str]):
        """Set the columns and update headers."""
        self._columns = new_columns
        self._headers = new_columns
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(new_columns) - 1)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable 