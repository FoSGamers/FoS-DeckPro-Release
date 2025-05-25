from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt

class EditCardDialog(QDialog):
    """
    Dialog for editing or adding a card. Shows all fields as editable widgets.
    """
    def __init__(self, card=None, all_fields=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Card" if card else "Add Card")
        self.setMinimumWidth(400)
        self.card = card.copy() if card else {}
        self.all_fields = all_fields or [
            "Name", "Set name", "Set code", "Collector number", "Rarity",
            "Condition", "Foil", "Language", "Purchase price", "Whatnot price",
            "ManaBox ID", "Scryfall ID", "Misprint", "Altered", "Purchase price currency",
            "Quantity", "cmc", "color_identity", "colors", "legal_commander", "legal_pauper",
            "mana_cost", "type_line", "oracle_text"
        ]
        self.inputs = {}

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        form = QVBoxLayout(content)

        for field in self.all_fields:
            hbox = QHBoxLayout()
            label = QLabel(field + ":")
            hbox.addWidget(label)
            # Use QComboBox for some fields, QLineEdit for others
            if field in ("Rarity", "Condition", "Foil", "Language"):
                combo = QComboBox()
                if field == "Rarity":
                    combo.addItems(["common", "uncommon", "rare", "mythic"])
                elif field == "Condition":
                    combo.addItems(["near_mint", "light_play", "moderate_play", "heavy_play", "damaged"])
                elif field == "Foil":
                    combo.addItems(["normal", "foil", "etched"])
                elif field == "Language":
                    combo.addItems(["en", "es", "fr", "de", "it", "pt", "ja", "ko", "ru", "zh"])
                value = self.card.get(field, "")
                if value:
                    idx = combo.findText(value)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                hbox.addWidget(combo)
                self.inputs[field] = combo
            else:
                edit = QLineEdit(str(self.card.get(field, "")))
                hbox.addWidget(edit)
                self.inputs[field] = edit
            form.addLayout(hbox)
        content.setLayout(form)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def get_card(self):
        card = {}
        for field, widget in self.inputs.items():
            if isinstance(widget, QComboBox):
                card[field] = widget.currentText()
            else:
                card[field] = widget.text()
        return card 