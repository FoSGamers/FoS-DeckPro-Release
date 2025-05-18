from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
from utils.json_utils import get_card_back_fields, set_card_back_fields

# Possible fields for each card type (can be extended/configured)
CARD_TYPE_FIELDS = {
    "players": ["Stats", "Equipment", "Buffs", "Inventory"],
    "enemies": ["Stats", "Equipment", "Buffs", "Inventory"],
    "weapons": ["Damage", "Hit Modifier", "Type", "Special Effects"],
    "armor": ["Damage Resistance", "Hit Modifier", "Dodge Modifier"],
    "items": ["Type", "Hit Modifier", "Properties"],
    "locations": ["Glossary"],
    "vendors": ["Location", "Inventory"],
    "buffs": ["Effect", "Duration"],
    "events": ["Dice", "Success Threshold", "Stat Bonuses", "Loot"]
}

class CardBackFieldsDialog(QDialog):
    """
    Dialog for selecting which fields appear on the back of a card for a given card type.
    Loads and saves preferences using utils/json_utils.
    """
    def __init__(self, card_type, parent=None, checked_fields=None):
        super().__init__(parent)
        self.setWindowTitle(f"Select Card Back Fields: {card_type}")
        self.card_type = card_type
        self.fields = CARD_TYPE_FIELDS.get(card_type, [])
        # If checked_fields is provided (from template), use it; else default to all checked
        if checked_fields is not None:
            self.selected_fields = set(checked_fields)
        else:
            self.selected_fields = set(self.fields)
        self.checkboxes = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Select which fields to show on the back of {self.card_type} cards:"))
        for field in self.fields:
            cb = QCheckBox(field)
            cb.setChecked(field in self.selected_fields)
            self.checkboxes[field] = cb
            layout.addWidget(cb)
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def get_selected_fields(self):
        return [field for field, cb in self.checkboxes.items() if cb.isChecked()]

    def accept(self):
        selected = self.get_selected_fields()
        set_card_back_fields(self.card_type, selected)
        super().accept()

    def set_checked_fields(self, checked_fields):
        for field, cb in self.checkboxes.items():
            cb.setChecked(field in checked_fields)
        self.selected_fields = set(checked_fields) 