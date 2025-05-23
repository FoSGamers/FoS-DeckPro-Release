from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QTextEdit, QHBoxLayout, QScrollArea
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# Map JSON keys to human-friendly names
FRIENDLY_NAMES = {
    "Name": "Name",
    "Set name": "Set Name",
    "Set code": "Set Code",
    "Collector number": "Collector #",
    "Rarity": "Rarity",
    "Condition": "Condition",
    "Foil": "Foil",
    "Language": "Language",
    "Purchase price": "Purchase Price",
    "Whatnot price": "Whatnot Price",
    "ManaBox ID": "ManaBox ID",
    "Scryfall ID": "Scryfall ID",
    "Misprint": "Misprint",
    "Altered": "Altered",
    "Purchase price currency": "Currency",
    "Quantity": "Quantity",
    "cmc": "CMC",
    "color_identity": "Color Identity",
    "colors": "Colors",
    "legal_commander": "Commander Legal",
    "legal_pauper": "Pauper Legal",
    "mana_cost": "Mana Cost",
    "type_line": "Type",
    "oracle_text": "Oracle Text",
    # Add more as needed
}

# Fields to hide by default
HIDE_FIELDS = {"_original_order", "image_url", "quantity"}

class CardDetails(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vlayout = QVBoxLayout()
        self.setLayout(self.vlayout)
        self.grid_layout = None
        self.oracle_group = None
        self.oracle_text = None

        # Add a scroll area for the details content
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.vlayout.addWidget(self.scroll_area)

        # The widget that will actually hold the details
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        self.details_widget.setLayout(self.details_layout)
        self.scroll_area.setWidget(self.details_widget)

    def show_card_details(self, card):
        # Clear previous widgets and layouts from the details layout
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                self._delete_layout(item.layout())
        # Prepare fields (excluding oracle_text and hidden fields)
        fields = [(k, v) for k, v in card.items() if k != "oracle_text" and k not in HIDE_FIELDS and v not in (None, "")]
        # Use a single QGridLayout with two columns of fields (label/value, label/value per row)
        grid = QGridLayout()
        num_fields = len(fields)
        for i in range(0, num_fields, 2):
            # Left column
            key1, value1 = fields[i]
            label1 = QLabel(FRIENDLY_NAMES.get(key1, key1) + ":")
            label1.setFont(QFont("Arial", weight=QFont.Bold))
            label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_label1 = QLabel(str(value1))
            val_label1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(label1, i // 2, 0)
            grid.addWidget(val_label1, i // 2, 1)
            # Right column (if exists)
            if i + 1 < num_fields:
                key2, value2 = fields[i + 1]
                label2 = QLabel(FRIENDLY_NAMES.get(key2, key2) + ":")
                label2.setFont(QFont("Arial", weight=QFont.Bold))
                label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                val_label2 = QLabel(str(value2))
                val_label2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                grid.addWidget(label2, i // 2, 2)
                grid.addWidget(val_label2, i // 2, 3)
        self.details_layout.addLayout(grid)
        # Show oracle_text in a QTextEdit at the end if present
        if "oracle_text" in card and card["oracle_text"]:
            group = QGroupBox("Oracle Text")
            vbox = QVBoxLayout()
            self.oracle_text = QTextEdit()
            self.oracle_text.setReadOnly(True)
            self.oracle_text.setPlainText(card["oracle_text"])
            vbox.addWidget(self.oracle_text)
            group.setLayout(vbox)
            self.details_layout.addWidget(group)

    def _delete_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
                elif item.layout() is not None:
                    self._delete_layout(item.layout())
            layout.deleteLater() 