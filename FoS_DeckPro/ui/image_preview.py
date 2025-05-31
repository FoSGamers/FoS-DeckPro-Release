from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QUrl, QByteArray, QObject
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import os

class ImagePreview(QLabel):
    """
    QLabel-based widget for displaying a card image preview.
    Images are only ever scaled down (never up) and always centered.
    Now supports async network image loading via QNetworkAccessManager.
    Handles reply deletion and race conditions robustly.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("No image available")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumWidth(10)
        self.setStyleSheet("border: 1.5px solid #b3c6e0; background: #f5f7fa; color: #888; font-style: italic;")
        self._original_pixmap = None  # Store the original pixmap for correct scaling
        self._manager = QNetworkAccessManager(self)
        self._network_reply = None
        self._current_request_id = 0
        # No background, no extra padding

    def show_card_image(self, card):
        """
        Load and display the card image from the given card dict.
        Only scale down images, never up. Center the image.
        Supports both URLs and local file paths.
        """
        url = card.get("image_url", "")
        print(f"DEBUG: show_card_image called with url: {url}")
        self._current_request_id += 1
        request_id = self._current_request_id
        # Clean up previous reply if needed
        if self._network_reply is not None:
            try:
                self._network_reply.finished.disconnect()
            except Exception:
                pass
            self._network_reply.deleteLater()
            self._network_reply = None
        if not url:
            self.setText("No image available")
            self.setPixmap(QPixmap())
            self._original_pixmap = None
            return
        # If it's a local file
        if os.path.exists(url):
            print(f"DEBUG: Loading local file image: {url}")
            pixmap = QPixmap(url)
            if not pixmap.isNull():
                self.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self._original_pixmap = pixmap
                self.setText("")
            else:
                self.setText("Image failed to load")
                self.setPixmap(QPixmap())
                self._original_pixmap = None
            return
        # Otherwise, try to load from network
        print(f"DEBUG: Loading network image: {url}")
        request = QNetworkRequest(QUrl(url))
        self.setText("Loading image...")
        self.setPixmap(QPixmap())
        self._original_pixmap = None
        reply = self._manager.get(request)
        self._network_reply = reply
        def on_finished():
            print(f"DEBUG: on_finished slot called for url: {url}")
            # Only handle if this is the latest request
            if request_id != self._current_request_id:
                print(f"DEBUG: Ignoring late reply for url: {url}")
                reply.deleteLater()
                return
            print(f"DEBUG: _on_image_loaded called for url: {url}")
            if reply.error() != QNetworkReply.NetworkError.NoError:
                print(f"DEBUG: Network reply error: {reply.error()} for URL: {url}")
                self.setText("Image failed to load")
                self.setPixmap(QPixmap())
                self._original_pixmap = None
            else:
                print(f"DEBUG: Entering image load else block for url: {url}")
                data = reply.readAll()
                print(f"DEBUG: type(data)={type(data)}, data={data[:40]}...")
                data_bytes = bytes(data)
                print(f"DEBUG: type(data_bytes)={type(data_bytes)}, len(data_bytes)={len(data_bytes)}")
                if not data_bytes:
                    print(f"WARNING: No image data received for url: {url}")
                print(f"DEBUG: Image data length: {len(data_bytes)} bytes")
                pixmap = QPixmap()
                loaded = pixmap.loadFromData(data_bytes)
                print(f"DEBUG: QPixmap loaded: {loaded}, isNull: {pixmap.isNull()}")
                if loaded and not pixmap.isNull():
                    self.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self._original_pixmap = pixmap
                    self.setText("")
                    print(f"DEBUG: Network image loaded and pixmap is valid")
                else:
                    self.setText("Image failed to load")
                    self.setPixmap(QPixmap())
                    self._original_pixmap = None
            reply.deleteLater()
            self._network_reply = None
        reply.finished.connect(on_finished)

    def resizeEvent(self, event):
        """
        Rescale the image to fit the new size, but only scale down (never up).
        Always scale from the original pixmap for crispness.
        """
        super().resizeEvent(event)
        if self._original_pixmap:
            self.setPixmap(self._original_pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

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
