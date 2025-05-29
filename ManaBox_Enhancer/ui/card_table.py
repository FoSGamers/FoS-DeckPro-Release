from PySide6.QtWidgets import QTableView, QMenu, QHeaderView, QSizePolicy, QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox
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

    def __init__(self, inventory, columns=None, parent=None):
        super().__init__(parent)
        print("DEBUG: CardTableView __init__ called")
        self.inventory = inventory
        self.columns = columns if columns is not None else ["Name", "Set", "Collector Number"]
        self.model = CardTableModel([], self.columns)
        self.setModel(self.model)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.doubleClicked.connect(self.on_double_click)
        self.default_widths = {col: 100 for col in self.columns}
        # Pagination
        self.page_size = 100
        self.current_page = 0
        self.filtered_cards = []
        self.pagination_widget = self._create_pagination_widget()
        # Scrollbars always as needed
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollMode(QTableView.ScrollPerPixel)
        self.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideNone)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        # Ensure selectionChanged is connected
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)

        # Set default column widths for clarity
        for i, col in enumerate(self.columns):
            self.setColumnWidth(i, self.default_widths.get(col, 100))

        # Make columns user-resizable and allow switching to stretch mode
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

    def _create_pagination_widget(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.page_label = QLabel()
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems([str(x) for x in [50, 100, 250, 500, 1000]])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        self.first_btn = QPushButton("First")
        self.prev_btn = QPushButton("Prev")
        self.next_btn = QPushButton("Next")
        self.last_btn = QPushButton("Last")
        self.first_btn.clicked.connect(self._go_first)
        self.prev_btn.clicked.connect(self._go_prev)
        self.next_btn.clicked.connect(self._go_next)
        self.last_btn.clicked.connect(self._go_last)
        layout.addWidget(QLabel("Page size:"))
        layout.addWidget(self.page_size_combo)
        layout.addWidget(self.first_btn)
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_label)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.last_btn)
        layout.addStretch()
        return widget

    def _on_page_size_changed(self, val):
        self.page_size = int(val)
        self.current_page = 0
        self._update_pagination()

    def _go_first(self):
        self.current_page = 0
        self._update_pagination()

    def _go_prev(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_pagination()

    def _go_next(self):
        if self.current_page < self._max_page():
            self.current_page += 1
            self._update_pagination()

    def _go_last(self):
        self.current_page = self._max_page()
        self._update_pagination()

    def _max_page(self):
        if not self.filtered_cards:
            return 0
        return max(0, (len(self.filtered_cards) - 1) // self.page_size)

    def _update_pagination(self):
        total = len(self.filtered_cards)
        max_page = self._max_page()
        print(f"DEBUG: CardTableView _update_pagination: page {self.current_page+1}/{max_page+1}, total {total}")
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_cards = self.filtered_cards[start:end]
        print(f"DEBUG: CardTableView _update_pagination: displaying {len(page_cards)} cards: {[c.get('Name') for c in page_cards]}")
        self.model.set_cards(page_cards)
        self.cards = page_cards
        self.viewport().update()
        self.first_btn.setEnabled(self.current_page > 0)
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < max_page)
        self.last_btn.setEnabled(self.current_page < max_page)

    def update_cards(self, cards):
        print(f"DEBUG: CardTableView update_cards called with {len(cards)} cards: {[c.get('Name') for c in cards]}")
        self.filtered_cards = cards
        self.current_page = 0
        self._update_pagination()

    def on_selection_changed(self, selected, deselected):
        indexes = self.selectedIndexes()
        if indexes:
            row = indexes[0].row()
            if row == 0:
                return  # Ignore blank filter row
            if 0 < row <= len(self.cards):
                print("DEBUG: CardTableView emitting card_selected:", self.cards[row - 1])
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

    def set_stretch_columns(self, stretch=True):
        mode = QHeaderView.Stretch if stretch else QHeaderView.Interactive
        self.horizontalHeader().setSectionResizeMode(mode)

    def reset_column_widths(self):
        for i, col in enumerate(self.columns):
            self.setColumnWidth(i, self.default_widths.get(col, 100))
