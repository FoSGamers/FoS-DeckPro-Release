from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QColorDialog, QComboBox, QWidget, QFormLayout, QCheckBox, QScrollArea, QInputDialog, QMessageBox
from PySide6.QtGui import QColor, QFontDatabase, QFont, QPixmap
from utils.font_settings import get_font_settings, set_font_settings
from utils.template_utils import list_templates, load_template
import os
from gui.font_browser import FontBrowserDialog
import tempfile
from PIL import Image, ImageDraw, ImageFont
from utils.json_utils import set_card_back_fields

CARD_PARTS = ["title", "subtype", "body", "stats"]
FONT_DIR = "fonts"

class FontSettingsDialog(QDialog):
    """
    Dialog for configuring font size, color, placement (x, y), style, and font file for each card part for a given card type.
    """
    def __init__(self, card_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Font Settings: {card_type}")
        self.card_type = card_type
        self.controls = {}
        self.font_files = self.get_downloaded_fonts()
        self.init_ui()

    def get_downloaded_fonts(self):
        fonts = []
        if os.path.exists(FONT_DIR):
            for fname in os.listdir(FONT_DIR):
                if fname.lower().endswith(".ttf") or fname.lower().endswith(".otf"):
                    fonts.append(fname)
        return sorted(fonts)

    def init_ui(self):
        layout = QVBoxLayout()
        # Add Download More Fonts button
        btn_download_fonts = QPushButton("Download More Fonts")
        btn_download_fonts.clicked.connect(self.download_more_fonts)
        layout.addWidget(btn_download_fonts)
        # Add Load Template button
        btn_load_template = QPushButton("Load Template")
        btn_load_template.clicked.connect(self.load_template)
        layout.addWidget(btn_load_template)
        # Scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        form_container = QWidget()
        form = QFormLayout(form_container)
        self.preview_labels = {}
        for part in CARD_PARTS:
            settings = get_font_settings(self.card_type, part)
            size = settings.get("size", 32)
            color = settings.get("color", "#000000")
            x = settings.get("x", 0)
            y = settings.get("y", 0)
            bold = settings.get("bold", False)
            italic = settings.get("italic", False)
            all_caps = settings.get("all_caps", False)
            underline = settings.get("underline", False)
            letter_spacing = settings.get("letter_spacing", 0)
            line_spacing = settings.get("line_spacing", 0)
            shadow = settings.get("shadow", False)
            font_file = settings.get("font_file", None)
            size_spin = QSpinBox()
            size_spin.setRange(8, 200)
            size_spin.setValue(size)
            color_btn = QPushButton()
            color_btn.setStyleSheet(f"background: {color}")
            color_btn.clicked.connect(lambda _, b=color_btn, p=part: self.pick_color(b, p))
            x_spin = QSpinBox()
            x_spin.setRange(-500, 2000)
            x_spin.setValue(x)
            y_spin = QSpinBox()
            y_spin.setRange(-500, 2000)
            y_spin.setValue(y)
            bold_cb = QCheckBox("Bold")
            bold_cb.setChecked(bold)
            italic_cb = QCheckBox("Italic")
            italic_cb.setChecked(italic)
            all_caps_cb = QCheckBox("All Caps")
            all_caps_cb.setChecked(all_caps)
            underline_cb = QCheckBox("Underline")
            underline_cb.setChecked(underline)
            letter_spacing_spin = QSpinBox()
            letter_spacing_spin.setRange(-10, 50)
            letter_spacing_spin.setValue(letter_spacing)
            line_spacing_spin = QSpinBox()
            line_spacing_spin.setRange(-10, 50)
            line_spacing_spin.setValue(line_spacing)
            shadow_cb = QCheckBox("Shadow")
            shadow_cb.setChecked(shadow)
            # Font selection combo
            font_combo = QComboBox()
            font_combo.addItem("(Default)")
            for fname in self.font_files:
                font_combo.addItem(fname)
            if font_file and font_file in self.font_files:
                font_combo.setCurrentText(font_file)
            else:
                font_combo.setCurrentIndex(0)
            # Live preview label
            preview_label = QLabel(f"{part.capitalize()} Preview")
            self.preview_labels[part] = preview_label
            self.controls[part] = {
                "font": font_combo,
                "size": size_spin,
                "color": color_btn,
                "x": x_spin,
                "y": y_spin,
                "color_val": color,
                "bold": bold_cb,
                "italic": italic_cb,
                "all_caps": all_caps_cb,
                "underline": underline_cb,
                "letter_spacing": letter_spacing_spin,
                "line_spacing": line_spacing_spin,
                "shadow": shadow_cb
            }
            self.update_preview_label(part)
            # Connect font/size changes to preview
            font_combo.currentTextChanged.connect(lambda _, p=part: self.update_preview_label(p))
            size_spin.valueChanged.connect(lambda _, p=part: self.update_preview_label(p))
            bold_cb.stateChanged.connect(lambda _, p=part: self.update_preview_label(p))
            italic_cb.stateChanged.connect(lambda _, p=part: self.update_preview_label(p))
            row = QHBoxLayout()
            row.addWidget(QLabel("Font:"))
            row.addWidget(font_combo)
            row.addWidget(QLabel("Size:"))
            row.addWidget(size_spin)
            row.addWidget(QLabel("Color:"))
            row.addWidget(color_btn)
            row.addWidget(QLabel("X:"))
            row.addWidget(x_spin)
            row.addWidget(QLabel("Y:"))
            row.addWidget(y_spin)
            row.addWidget(bold_cb)
            row.addWidget(italic_cb)
            row.addWidget(all_caps_cb)
            row.addWidget(underline_cb)
            row.addWidget(QLabel("Letter Spacing:"))
            row.addWidget(letter_spacing_spin)
            row.addWidget(QLabel("Line Spacing:"))
            row.addWidget(line_spacing_spin)
            row.addWidget(shadow_cb)
            form.addRow(QLabel(part.capitalize()), row)
            form.addRow(preview_label)
        scroll.setWidget(form_container)
        layout.addWidget(scroll)
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        self.setLayout(layout)

    def pick_color(self, btn, part):
        col = QColorDialog.getColor(QColor(self.controls[part]["color_val"]))
        if col.isValid():
            self.controls[part]["color_val"] = col.name()
            btn.setStyleSheet(f"background: {col.name()}")

    def accept(self):
        for part, ctrls in self.controls.items():
            font_file = ctrls["font"].currentText()
            if font_file == "(Default)":
                font_file = None
            settings = {
                "font_file": font_file,
                "size": ctrls["size"].value(),
                "color": ctrls["color_val"],
                "x": ctrls["x"].value(),
                "y": ctrls["y"].value(),
                "bold": ctrls["bold"].isChecked(),
                "italic": ctrls["italic"].isChecked(),
                "all_caps": ctrls["all_caps"].isChecked(),
                "underline": ctrls["underline"].isChecked(),
                "letter_spacing": ctrls["letter_spacing"].value(),
                "line_spacing": ctrls["line_spacing"].value(),
                "shadow": ctrls["shadow"].isChecked()
            }
            set_font_settings(self.card_type, part, settings)
        super().accept()

    def download_more_fonts(self):
        dialog = FontBrowserDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh font list in all combos
            self.font_files = self.get_downloaded_fonts()
            for part in CARD_PARTS:
                combo = self.controls[part]["font"]
                current = combo.currentText()
                combo.clear()
                combo.addItem("(Default)")
                for fname in self.font_files:
                    combo.addItem(fname)
                if current and current in self.font_files:
                    combo.setCurrentText(current)
                else:
                    combo.setCurrentIndex(0)
                self.update_preview_label(part)

    def load_template(self):
        templates = list_templates()
        if not templates:
            QMessageBox.information(self, "No Templates", "No templates found.")
            return
        name, ok = QInputDialog.getItem(self, "Load Template", "Select a template:", templates, editable=False)
        if not ok or not name:
            return
        template = load_template(name)
        font_settings = template.get('font_settings', {})
        checked_fields = template.get('checked_fields', None)
        # Update card back fields config if checked_fields is present
        if checked_fields is not None:
            set_card_back_fields(self.card_type, checked_fields)
        for part in CARD_PARTS:
            settings = font_settings.get(part, {})
            # Set font combo
            font_file = settings.get("font_file", None)
            combo = self.controls[part]["font"]
            if font_file and font_file in self.font_files:
                combo.setCurrentText(font_file)
            else:
                combo.setCurrentIndex(0)
            # Set other controls
            self.controls[part]["size"].setValue(settings.get("size", 32))
            self.controls[part]["color_val"] = settings.get("color", "#000000")
            self.controls[part]["color"].setStyleSheet(f"background: {settings.get('color', '#000000')}")
            self.controls[part]["x"].setValue(settings.get("x", 0))
            self.controls[part]["y"].setValue(settings.get("y", 0))
            self.controls[part]["bold"].setChecked(settings.get("bold", False))
            self.controls[part]["italic"].setChecked(settings.get("italic", False))
            self.controls[part]["all_caps"].setChecked(settings.get("all_caps", False))
            self.controls[part]["underline"].setChecked(settings.get("underline", False))
            self.controls[part]["letter_spacing"].setValue(settings.get("letter_spacing", 0))
            self.controls[part]["line_spacing"].setValue(settings.get("line_spacing", 0))
            self.controls[part]["shadow"].setChecked(settings.get("shadow", False))
            self.update_preview_label(part)
        QMessageBox.information(self, "Template Loaded", f"Template '{name}' loaded and applied.")

    def update_preview_label(self, part):
        ctrls = self.controls[part]
        font_name = ctrls["font"].currentText()
        size = ctrls["size"].value()
        bold = ctrls["bold"].isChecked()
        italic = ctrls["italic"].isChecked()
        color = ctrls["color_val"]
        # Use a real sample text for preview
        sample_texts = {
            "title": "CARD TITLE\nMutant Overlord",
            "subtype": "Creature — Mutant\nBoss",
            "body": "Born from the irradiated wasteland, this towering abomination exudes a powerful aura of destruction.\nSpecial: Roll 2d8 for damage.",
            "stats": "STRENGTH: 10  CONSTITUTION: 14\nROLL DAMAGE: 2D8 RADIANT"
        }
        preview_text = sample_texts.get(part, "Sample Text")
        label = self.preview_labels[part]
        fallback = False
        if font_name and font_name != "(Default)":
            font_path = os.path.join(FONT_DIR, font_name)
            font_id = QFontDatabase.addApplicationFont(font_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                qfont = QFont(families[0], size)
                qfont.setBold(bold)
                qfont.setItalic(italic)
                label.setFont(qfont)
                label.setText(preview_text)
                label.setPixmap(QPixmap())
            else:
                # Pillow fallback
                fallback = True
                img = Image.new("RGBA", (600, 100), (255, 255, 255, 0))
                draw = ImageDraw.Draw(img)
                try:
                    pil_font = ImageFont.truetype(font_path, size)
                except Exception:
                    pil_font = ImageFont.load_default()
                # Draw text in selected color
                try:
                    rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                except Exception:
                    rgb = (0, 0, 0)
                draw.multiline_text((10, 10), preview_text, font=pil_font, fill=rgb)
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    img.save(tmp.name)
                    pixmap = QPixmap(tmp.name)
                label.setPixmap(pixmap)
                label.setText("")
        else:
            qfont = QFont("Arial", size)
            qfont.setBold(bold)
            qfont.setItalic(italic)
            label.setFont(qfont)
            label.setText(preview_text)
            label.setPixmap(QPixmap())
        label.setToolTip(f"Font: {font_name if font_name and font_name != '(Default)' else 'Default'}" + (" (Pillow fallback)" if fallback else ""))
        label.setMinimumHeight(60)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {color};") 