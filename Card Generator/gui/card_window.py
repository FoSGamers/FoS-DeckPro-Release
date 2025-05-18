from PySide6.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QFormLayout, QMessageBox, QListWidget, QComboBox, QRadioButton, QButtonGroup, QListWidgetItem, QDialog, QHBoxLayout, QStackedWidget, QFileDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import sys
import os
from shutil import copy2
from functools import partial
from cards.card import generate_cards_batch, get_card_name, get_card_subtext, get_card_story, get_card_stats
from utils.json_loader import load_wasteland_json
from gui.font_browser import FontBrowserDialog
from gui.card_review import CardReviewDialog
from utils.json_utils import add_card_to_json
from config.constants import WASTELAND_JSON_PATH

class WastelandCardGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wasteland AI Card Generator")
        self.setMinimumSize(1200, 700)

        self.wasteland_data = load_wasteland_json()
        self.card_types = list(self.wasteland_data.get("schema", {}).keys())
        self.title_font_path = None  # Path to the selected font (used for all card text)

        self.type_select = QComboBox()
        self.type_select.addItems(self.card_types)
        self.type_select.currentTextChanged.connect(self.update_entry_list)

        self.source_group = QButtonGroup(self)
        self.radio_auto = QRadioButton("Auto-generate new")
        self.radio_db = QRadioButton("From database (pick existing)")
        self.radio_auto.setChecked(True)
        self.source_group.addButton(self.radio_auto)
        self.source_group.addButton(self.radio_db)
        self.radio_auto.toggled.connect(self.update_source_mode)
        self.radio_db.toggled.connect(self.update_source_mode)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Describe your encounter theme and # of cards...")
        self.count_input = QLineEdit("1")

        self.entry_list = QListWidget()
        self.entry_list.setSelectionMode(QListWidget.MultiSelection)
        self.entry_list.hide()
        self.update_entry_list(self.type_select.currentText())

        self.btn_generate = QPushButton("Generate Batch Cards")
        self.btn_generate.clicked.connect(self.generate_cards)

        self.btn_export = QPushButton("Export Approved Cards")
        self.btn_export.clicked.connect(self.export_approved_cards)

        self.btn_choose_font = QPushButton("Choose Font (Google Fonts)")
        self.btn_choose_font.clicked.connect(self.choose_font)

        self.card_list = QListWidget()
        self.card_list_label = QLabel("Generated Cards (Approved)")

        self.approved_cards = []  # Store approved card dicts
        self.approved_image_paths = []  # Store (front, back) image paths

        layout = QVBoxLayout()
        form = QFormLayout()
        form.addRow("Card Type:", self.type_select)
        form.addRow(self.radio_auto)
        form.addRow(self.radio_db)
        form.addRow("Prompt:", self.prompt_input)
        form.addRow("Card Count:", self.count_input)
        form.addRow("Database Entries:", self.entry_list)
        form.addRow(self.btn_generate)
        form.addRow(self.btn_export)
        form.addRow(self.btn_choose_font)
        layout.addLayout(form)
        layout.addWidget(self.card_list_label)
        layout.addWidget(self.card_list)

        self.setLayout(layout)
        self.update_source_mode()

    def update_entry_list(self, card_type):
        self.entry_list.clear()
        data_list = self.wasteland_data.get(card_type, [])
        for entry in data_list:
            name = entry.get('name', entry.get('Title', str(entry)))
            item = QListWidgetItem(name)
            item.setData(1000, entry)  # Store the entry dict
            self.entry_list.addItem(item)

    def update_source_mode(self):
        if self.radio_db.isChecked():
            self.prompt_input.hide()
            self.count_input.hide()
            self.entry_list.show()
        else:
            self.prompt_input.show()
            self.count_input.show()
            self.entry_list.hide()

    def generate_cards(self):
        card_type = self.type_select.currentText()
        from_db_flags = []
        if self.radio_db.isChecked():
            selected_items = self.entry_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "No selection", "Please select at least one entry from the database.")
                return
            entries = [item.data(1000) for item in selected_items]
            # Pass font path to card generator
            cards = generate_cards_batch("", len(entries), card_type, db_entries=entries, font_path=self.title_font_path)
            from_db_flags = [True] * len(cards)
        else:
            prompt = self.prompt_input.toPlainText().strip()
            try:
                count = int(self.count_input.text())
            except:
                QMessageBox.warning(self, "Invalid count", "Please enter a valid number.")
                return
            if not prompt or count < 1:
                QMessageBox.warning(self, "Missing info", "Prompt and count required.")
                return
            # Pass font path to card generator
            cards = generate_cards_batch(prompt, count, card_type, font_path=self.title_font_path)
            from_db_flags = [False] * len(cards)
        # Approval dialog
        review = CardReviewDialog(cards, card_type, self, from_db_flags=from_db_flags, font_path=self.title_font_path)
        if review.exec() == QDialog.Accepted:
            for i, card in enumerate(review.approved):
                name = get_card_name(card)
                self.card_list.addItem(f"{name} (Approved)")
                # Save image paths for export
                title = name.replace(" ", "_")
                today = card.get('_date_folder') if isinstance(card, dict) else None
                card_type_dir = card.get('CardType', card_type) if isinstance(card, dict) else card_type
                card_type_dir = card_type_dir or card_type
                if today:
                    base_dir = os.path.join('generated_cards', today)
                else:
                    base_dir = 'generated_cards'
                type_dir = os.path.join(base_dir, card_type_dir)
                front_path = os.path.join(type_dir, f"{title}_front.png")
                back_path = os.path.join(type_dir, f"{title}_back.png")
                self.approved_cards.append(card)
                self.approved_image_paths.append((front_path, back_path))
                # If new, add to JSON
                if not review.from_db_flags[i]:
                    add_card_to_json(card, card_type)

    def export_approved_cards(self):
        if not self.approved_image_paths:
            QMessageBox.information(self, "No approved cards", "There are no approved cards to export.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if not folder:
            return
        for front, back in self.approved_image_paths:
            if os.path.exists(front):
                copy2(front, folder)
            if os.path.exists(back):
                copy2(back, folder)
        QMessageBox.information(self, "Export Complete", f"Exported {len(self.approved_image_paths)*2} images to {folder}.")

    def choose_font(self):
        dialog = FontBrowserDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_font:
            self.title_font_path = dialog.selected_font
            QMessageBox.information(self, "Font Set", f"Font set to: {self.title_font_path}")

def launch_app():
    app = QApplication(sys.argv)
    window = WastelandCardGenerator()
    window.show()
    sys.exit(app.exec()) 