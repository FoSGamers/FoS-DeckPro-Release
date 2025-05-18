from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import requests

class ImagePreview(QLabel):
    """
    QLabel-based widget for displaying a card image preview.
    Images are only ever scaled down (never up) and always centered.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Image Preview (to be implemented)")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(10)
        self.setStyleSheet("border: 1px solid #ccc;")
        self._original_pixmap = None  # Store the original pixmap for correct scaling
        # No background, no extra padding

    def show_card_image(self, card):
        """
        Load and display the card image from the given card dict.
        Only scale down images, never up. Center the image.
        """
        url = card.get("image_url", "")
        print(f"[ImagePreview] Loading image URL: {url}")  # Debug output
        if url:
            self.setText("Loading image...")
            self.setPixmap(QPixmap())
            self._original_pixmap = None
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                if not pixmap.isNull():
                    self._original_pixmap = pixmap
                    self._update_scaled_pixmap()
                    self.setText("")
                    print("[ImagePreview] Image loaded successfully.")
                else:
                    print("[ImagePreview] Invalid image data.")
                    self.setText("Invalid image data")
                    self.setPixmap(QPixmap())
            except Exception as e:
                print(f"[ImagePreview] Failed to load image: {e}")
                self.setText(f"Failed to load image: {e}")
                self.setPixmap(QPixmap())
                self._original_pixmap = None
        else:
            print("[ImagePreview] No image URL available.")
            self.setText("No image available")
            self.setPixmap(QPixmap())
            self._original_pixmap = None

    def resizeEvent(self, event):
        """
        Rescale the image to fit the new size, but only scale down (never up).
        Always scale from the original pixmap for crispness.
        """
        self._update_scaled_pixmap()
        super().resizeEvent(event)

    def _update_scaled_pixmap(self):
        """
        Helper to update the displayed pixmap according to the current widget size.
        Only scales down the image, never up, and keeps it centered.
        Always scale from the original pixmap for best quality.
        """
        if self._original_pixmap and not self._original_pixmap.isNull():
            label_width = self.width()
            label_height = self.height()
            img_width = self._original_pixmap.width()
            img_height = self._original_pixmap.height()
            # Only scale down if image is larger than label in either dimension
            if img_width > label_width or img_height > label_height:
                scaled = self._original_pixmap.scaled(
                    label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.setPixmap(scaled)
            else:
                # Image is smaller than label, show at original size (centered)
                self.setPixmap(self._original_pixmap)
        else:
            self.setPixmap(QPixmap())
