from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QWidget, QRadioButton, QButtonGroup, QSizePolicy, QInputDialog, QMessageBox
from PySide6.QtGui import QPixmap
from functools import partial
import os
from cards.card import get_card_name, get_card_subtext, get_card_story, get_card_stats, regenerate_card_images, get_card_image_filenames
from gui.card_image_widget import CardImageWidget
from gui.card_back_fields_dialog import CardBackFieldsDialog
from gui.font_settings_dialog import FontSettingsDialog
from utils.template_utils import save_template, load_template, list_templates
from utils.font_settings import get_font_settings
from utils.json_utils import get_card_back_fields
from utils.json_loader import load_wasteland_json

class CardReviewDialog(QDialog):
    """
    CardReviewDialog
    ---------------
    Dialog for reviewing and approving cards, with two modes:
    1. Side-by-side: shows both front and back, each zoomable.
    2. Single-card: shows one side at a time, with a Flip button.
    The window is resizable and card previews expand with the window.
    Only the current card's images are shown at a time.
    """
    def __init__(self, cards, card_type, parent=None, from_db_flags=None, font_path=None):
        super().__init__(parent)
        self.setWindowTitle("Review and Approve Cards")
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cards = cards
        self.card_type = card_type
        self.from_db_flags = from_db_flags or [False]*len(cards)
        self.approved = []
        self.rejected = []
        self.approved_flags = []  # Track if approved card is new
        self.current = 0
        self.image_paths = []  # Store (front, back) image paths for each card
        self.mode = 'side_by_side'  # or 'single_flip'
        self.single_flip_side = 'front'  # or 'back'
        self.font_path = font_path
        # Load wasteland data and store the correct data_list for this card type
        wasteland_data = load_wasteland_json()
        self.data_list = wasteland_data.get(self.card_type, [])
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        # Mode toggle
        mode_hbox = QHBoxLayout()
        self.radio_side = QRadioButton("Side-by-side")
        self.radio_single = QRadioButton("Single (Flip)")
        self.radio_side.setChecked(True)
        self.radio_side.toggled.connect(self.switch_mode)
        mode_hbox.addWidget(self.radio_side)
        mode_hbox.addWidget(self.radio_single)
        self.layout.addLayout(mode_hbox)
        # Card Back Fields button
        self.fields_btn = QPushButton("Card Back Fields")
        self.fields_btn.clicked.connect(self.open_fields_dialog)
        self.layout.addWidget(self.fields_btn)
        # Font Settings button
        self.font_settings_btn = QPushButton("Font Settings")
        self.font_settings_btn.clicked.connect(self.open_font_settings_dialog)
        self.layout.addWidget(self.font_settings_btn)
        # Save as Template button
        self.save_template_btn = QPushButton("Save as Template")
        self.save_template_btn.clicked.connect(self.save_as_template)
        self.layout.addWidget(self.save_template_btn)
        # Flip button (only for single mode)
        self.flip_btn = QPushButton("Flip")
        self.flip_btn.clicked.connect(self.flip_card)
        self.flip_btn.hide()
        self.layout.addWidget(self.flip_btn)
        # Card image area
        self.card_area = QVBoxLayout()
        self.layout.addLayout(self.card_area)
        # Info area
        self.info_label = QLabel()
        self.layout.addWidget(self.info_label)
        # Approve/Reject buttons
        btns = QHBoxLayout()
        self.approve_btn = QPushButton("Approve")
        self.reject_btn = QPushButton("Reject")
        self.approve_btn.clicked.connect(self.approve_card)
        self.reject_btn.clicked.connect(self.reject_card)
        btns.addWidget(self.approve_btn)
        btns.addWidget(self.reject_btn)
        self.layout.addLayout(btns)
        # Prepare image paths
        for card in self.cards:
            name = get_card_name(card)
            title = name.replace(" ", "_")
            today = card.get('_date_folder') if isinstance(card, dict) else None
            card_type_dir = card.get('CardType', self.card_type) if isinstance(card, dict) else self.card_type
            card_type_dir = card_type_dir or self.card_type
            if today:
                base_dir = os.path.join('generated_cards', today)
            else:
                base_dir = 'generated_cards'
            type_dir = os.path.join(base_dir, card_type_dir)
            front_path, back_path = get_card_image_filenames(card, self.card_type)
            self.image_paths.append((front_path, back_path))
        self.update_card_view()

    def switch_mode(self):
        if self.radio_side.isChecked():
            self.mode = 'side_by_side'
            self.flip_btn.hide()
        else:
            self.mode = 'single_flip'
            self.flip_btn.show()
        self.update_card_view()

    def update_card_view(self):
        # Clear card area
        self.clear_layout(self.card_area)
        # Get current card info
        card = self.cards[self.current]
        front_path, back_path = self.image_paths[self.current]
        name = get_card_name(card)
        subtext = get_card_subtext(card, self.card_type)
        story = get_card_story(card, self.card_type)
        # Pass self.data_list to get_card_stats for correct name resolution
        stats = get_card_stats(card, self.card_type, self.data_list)
        # Show images
        if self.mode == 'side_by_side':
            hbox = QHBoxLayout()
            front_widget = CardImageWidget(front_path)
            back_widget = CardImageWidget(back_path)
            front_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            back_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            hbox.addWidget(front_widget)
            hbox.addWidget(back_widget)
            self.card_area.addLayout(hbox)
        else:
            if self.single_flip_side == 'front':
                single_widget = CardImageWidget(front_path)
            else:
                single_widget = CardImageWidget(back_path)
            single_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.card_area.addWidget(single_widget)
        # Info
        info_html = f"<b>Front:</b><br>{name}<br><i>{subtext}</i><br><br><b>Back:</b><br>{name}<br><br>{story}<br><br><pre>{stats}</pre>"
        self.info_label.setText(info_html)

    def flip_card(self):
        self.single_flip_side = 'back' if self.single_flip_side == 'front' else 'front'
        self.update_card_view()

    def approve_card(self):
        self.approved.append(self.cards[self.current])
        self.approved_flags.append(not self.from_db_flags[self.current])
        self.next_card()

    def reject_card(self):
        card = self.cards[self.current]
        front_path, back_path = self.image_paths[self.current]
        # Delete images for rejected card
        for path in [front_path, back_path]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"[DEBUG] Could not delete {path}: {e}")
        self.rejected.append(card)
        self.next_card()

    def next_card(self):
        self.current += 1
        if self.current < len(self.cards):
            self.update_card_view()
        else:
            self.accept()

    def open_fields_dialog(self):
        from utils.template_utils import load_template, list_templates
        # Check if a template is loaded for this card type
        template_fields = None
        # Try to load the most recently loaded template for this card type (if any)
        # For now, just open with all fields checked unless a template is loaded
        dlg = CardBackFieldsDialog(self.card_type, self)
        if dlg.exec() == QDialog.Accepted:
            # Regenerate images for the current card to reflect new field selection
            card = self.cards[self.current]
            regenerate_card_images(card, self.card_type, font_path=self.font_path)
            self.update_card_view()

    def open_font_settings_dialog(self):
        dlg = FontSettingsDialog(self.card_type, self)
        if dlg.exec() == QDialog.Accepted:
            # Regenerate images for the current card with new font settings
            card = self.cards[self.current]
            regenerate_card_images(card, self.card_type, font_path=self.font_path)
            self.update_card_view()

    def save_as_template(self):
        # Prompt for template name
        name, ok = QInputDialog.getText(self, "Save as Template", "Template name:")
        if not ok or not name.strip():
            return
        # Gather font settings for this card type
        font_settings = {part: get_font_settings(self.card_type, part) for part in ["title", "subtype", "body", "stats"]}
        checked_fields = get_card_back_fields(self.card_type)
        # Optionally, gather layout/style settings here
        try:
            save_template(name.strip(), self.card_type, font_settings, checked_fields)
            QMessageBox.information(self, "Template Saved", f"Template '{name.strip()}' saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save template: {e}")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.setParent(None)
            elif child_layout:
                self.clear_layout(child_layout) 