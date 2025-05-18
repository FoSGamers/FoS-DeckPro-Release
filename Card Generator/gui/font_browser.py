"""
font_browser.py

Provides FontBrowserDialog for browsing, previewing, and downloading Google Fonts.
Uses FileDownloadThread from utils.font_downloader for background downloads.

Classes:
    - FontBrowserDialog: Main dialog for font browsing and selection.

Usage:
    from gui.font_browser import FontBrowserDialog
    dialog = FontBrowserDialog(parent)
    if dialog.exec() == QDialog.Accepted:
        font_path = dialog.selected_font
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QLabel, QPushButton, QMessageBox
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtCore import Signal
import os
from config.constants import FONTS_DIR, GOOGLE_FONTS_API_URL
from utils.font_downloader import FileDownloadThread

class FontBrowserDialog(QDialog):
    """
    FontBrowserDialog
    -----------------
    Dialog for browsing, previewing, and downloading Google Fonts.
    Downloads fonts in the background and provides live preview.
    Workflow:
        1. Select a font in the list.
        2. Click 'Load Font Preview' to download (if needed) and preview the font.
        3. Click 'Download & Use Font' to set the font for use and close the dialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Google Fonts Browser")
        self.resize(600, 500)
        self.fonts = []
        self.selected_font = None
        self.preview_text = "CARD TITLE\nCreature — Mutant\nBorn from the irradiated wasteland, this towering abomination exudes a powerful aura of destruction.\nSTRENGTH: 10  CONSTITUTION: 14  ROLL DAMAGE: 2D8 RADIANT"
        self.font_cache = {}  # family -> font path
        self.download_thread = None
        self.current_preview_font = None
        self.init_ui()
        self.fetch_fonts()

    def init_ui(self):
        layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search fonts...")
        self.search_bar.textChanged.connect(self.filter_fonts)
        self.font_list = QListWidget()
        self.font_list.currentItemChanged.connect(self.on_font_selected)
        self.preview_label = QLabel(self.preview_text)
        self.preview_label.setMinimumHeight(160)
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        self.status_label = QLabel("")
        self.btn_load_preview = QPushButton("Load Font Preview")
        self.btn_load_preview.setEnabled(False)
        self.btn_load_preview.clicked.connect(self.load_font_preview)
        self.btn_download = QPushButton("Download & Use Font")
        self.btn_download.clicked.connect(self.download_and_use_font)
        self.btn_download.setEnabled(False)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.font_list)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.btn_load_preview)
        layout.addWidget(self.btn_download)
        self.setLayout(layout)

    def fetch_fonts(self):
        import requests
        try:
            resp = requests.get(GOOGLE_FONTS_API_URL)
            data = resp.json()
            self.fonts = data.get("items", [])
            self.show_fonts(self.fonts)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to fetch fonts: {e}")

    def show_fonts(self, fonts):
        self.font_list.clear()
        for font in fonts:
            self.font_list.addItem(font["family"])

    def filter_fonts(self, text):
        filtered = [f for f in self.fonts if text.lower() in f["family"].lower()]
        self.show_fonts(filtered)

    def on_font_selected(self, current, previous):
        if not current:
            self.btn_download.setEnabled(False)
            self.btn_load_preview.setEnabled(False)
            self.status_label.setText("")
            self.preview_label.setFont(QFont())
            self.preview_label.setText(self.preview_text)
            return
        font_name = current.text()
        font_info = next((f for f in self.fonts if f["family"] == font_name), None)
        if not font_info:
            self.btn_download.setEnabled(False)
            self.btn_load_preview.setEnabled(False)
            self.status_label.setText("Font info not found.")
            return
        font_path = os.path.join(FONTS_DIR, f"{font_name.replace(' ', '')}-Regular.ttf")
        self.btn_load_preview.setEnabled(True)
        if os.path.exists(font_path):
            self.status_label.setText("Font ready! Click 'Load Font Preview' to preview.")
            self.btn_download.setEnabled(True)
        else:
            self.status_label.setText("Font not downloaded. Click 'Load Font Preview' to download and preview.")
            self.btn_download.setEnabled(True)
        self.preview_label.setFont(QFont())
        self.preview_label.setText(self.preview_text)
        self.current_preview_font = None

    def load_font_preview(self):
        item = self.font_list.currentItem()
        if not item:
            return
        font_name = item.text()
        font_info = next((f for f in self.fonts if f["family"] == font_name), None)
        if not font_info:
            self.status_label.setText("Font info not found.")
            print("[DEBUG] Font info not found for:", font_name)
            return
        url = font_info["files"].get("regular") or list(font_info["files"].values())[0]
        font_path = os.path.join(FONTS_DIR, f"{font_name.replace(' ', '')}-Regular.ttf")
        print(f"[DEBUG] Attempting to preview font: {font_name} at {font_path}")
        if os.path.exists(font_path):
            self.status_label.setText("Font ready! Preview loaded.")
            self.update_preview(font_path)
            self.current_preview_font = font_path
        else:
            self.status_label.setText("Downloading font for preview…")
            self.btn_load_preview.setEnabled(False)
            self.download_thread = FileDownloadThread(url, font_path)
            self.download_thread.finished.connect(self.on_preview_download_finished)
            self.download_thread.start()

    def on_preview_download_finished(self, font_path, success, error_msg):
        print(f"[DEBUG] Download finished for {font_path}, success={success}, error={error_msg}")
        if success:
            self.status_label.setText("Font ready! Preview loaded.")
            self.btn_load_preview.setEnabled(True)
            self.update_preview(font_path)
            self.current_preview_font = font_path
        else:
            self.status_label.setText(f"Error: {error_msg}")
            self.btn_load_preview.setEnabled(True)
            print(f"[DEBUG] Font download error: {error_msg}")

    def download_and_use_font(self):
        item = self.font_list.currentItem()
        if not item:
            return
        font_name = item.text()
        font_info = next((f for f in self.fonts if f["family"] == font_name), None)
        if not font_info:
            self.status_label.setText("Font info not found.")
            return
        url = font_info["files"].get("regular") or list(font_info["files"].values())[0]
        font_path = os.path.join(FONTS_DIR, f"{font_name.replace(' ', '')}-Regular.ttf")
        if os.path.exists(font_path):
            self.selected_font = font_path
            QMessageBox.information(self, "Font Downloaded", f"Font '{font_name}' downloaded and ready to use!")
            self.accept()
            return
        self.status_label.setText("Downloading…")
        self.btn_download.setEnabled(False)
        self.download_thread = FileDownloadThread(url, font_path)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.start()

    def on_download_finished(self, font_path, success, error_msg):
        if success:
            self.status_label.setText("Font ready!")
            self.btn_download.setEnabled(True)
            self.selected_font = font_path
            QMessageBox.information(self, "Font Downloaded", f"Font downloaded and ready to use!")
            self.accept()
        else:
            self.status_label.setText(f"Error: {error_msg}")
            self.btn_download.setEnabled(True)

    def update_preview(self, font_path):
        import os
        print(f"[DEBUG] update_preview called with font_path: {font_path}")
        if not os.path.exists(font_path):
            print(f"[DEBUG] Font file does not exist: {font_path}")
        else:
            size = os.path.getsize(font_path)
            print(f"[DEBUG] Font file exists. Size: {size} bytes")
        try:
            font_id = QFontDatabase.addApplicationFont(font_path)
            families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"[DEBUG] Loaded font families: {families}")
            if families:
                preview_font = QFont(families[0], 28)
                self.preview_label.setFont(preview_font)
                self.preview_label.setText(self.preview_text)
                self.preview_label.repaint()  # Force repaint in case of UI lag
            else:
                print(f"[DEBUG] No font families loaded for {font_path}, using Pillow fallback.")
                # Fallback: render preview text to image using Pillow
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    from PySide6.QtGui import QPixmap
                    # Create image
                    img_w, img_h = 560, 180
                    img = Image.new("RGBA", (img_w, img_h), (240, 240, 240, 255))
                    draw = ImageDraw.Draw(img)
                    # Try to load the font at a reasonable size
                    try:
                        pil_font = ImageFont.truetype(font_path, 28)
                    except Exception as e:
                        print(f"[DEBUG] Pillow could not load font: {e}")
                        pil_font = ImageFont.load_default()
                    # Draw text (wrap if needed)
                    import textwrap
                    lines = textwrap.wrap(self.preview_text, width=50)
                    y = 10
                    for line in lines:
                        draw.text((10, y), line, font=pil_font, fill=(0,0,0,255))
                        y += pil_font.getbbox(line)[3] - pil_font.getbbox(line)[1] + 2
                    # Convert to QPixmap and set on label
                    img = img.convert("RGBA")
                    data = img.tobytes("raw", "RGBA")
                    from PySide6.QtGui import QImage
                    qimg = QImage(data, img_w, img_h, QImage.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.preview_label.setPixmap(pixmap)
                    self.preview_label.setText("")
                except Exception as e:
                    print(f"[DEBUG] Exception in Pillow fallback: {e}")
                    self.preview_label.setFont(QFont())
                    self.preview_label.setText(self.preview_text)
        except Exception as e:
            print(f"[DEBUG] Exception in update_preview: {e}")
            self.preview_label.setFont(QFont())
            self.preview_label.setText(self.preview_text) 