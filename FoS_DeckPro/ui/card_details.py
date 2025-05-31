from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QTextEdit, QHBoxLayout, QScrollArea, QFormLayout, QSizePolicy, QFrame
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
    """
    Widget to display all key card info in a readable, modern, scrollable layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #f8fafd; border: 1.5px solid #b3c6e0; border-radius: 10px; padding: 10px 10px 10px 10px;")
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.inner = QWidget()
        self.form = QFormLayout(self.inner)
        self.form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.form.setFormAlignment(Qt.AlignTop)
        self.form.setSpacing(8)
        self.labels = {}
        for key in [
            "Name", "Set name", "Set code", "Collector number", "Rarity", "Condition", "Foil", "Language", "Purchase price", "Whatnot price", "type_line", "mana_cost", "colors", "oracle_text"
        ]:
            l = QLabel()
            l.setWordWrap(True)
            l.setStyleSheet("font-size: 15px; color: #222; padding: 2px 0;")
            self.labels[key] = l
            label_widget = QLabel(f"<b>{key.replace('_', ' ').title()}:</b>")
            label_widget.setStyleSheet("font-size: 15px; color: #1976d2; padding: 2px 0;")
            self.form.addRow(label_widget, l)
        self.inner.setLayout(self.form)
        self.scroll.setWidget(self.inner)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def show_card_details(self, card):
        """
        Update the details area with all key info from the card dict.
        """
        for key, label in self.labels.items():
            val = card.get(key, "")
            if key == "colors" and isinstance(val, (list, tuple)):
                val = ", ".join(val)
            if key == "oracle_text":
                val = val.replace("\n", "<br>")
                label.setText(f'<span style="font-size:14px; color:#444;">{val}</span>')
            else:
                label.setText(str(val))

    def _delete_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
                elif item.layout() is not None:
                    self._delete_layout(item.layout())
            layout.deleteLater() 