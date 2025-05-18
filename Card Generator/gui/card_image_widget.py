from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSizePolicy, QScrollArea
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize
import os

CARD_ASPECT_RATIO = 768 / 1152  # width / height

class CardImageWidget(QWidget):
    """
    CardImageWidget
    ---------------
    A reusable widget for displaying a card image with zoom controls and pan/scroll support.
    Maintains the correct card aspect ratio and prevents stretching.
    When zoomed in, scrollbars appear and you can pan to see any part of the card.
    Usage:
        widget = CardImageWidget(image_path)
        widget.set_image(image_path)
    """
    def __init__(self, image_path=None, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.zoom = 1.0
        self.pixmap = None
        self.init_ui()
        if image_path:
            self.set_image(image_path)

    def init_ui(self):
        layout = QVBoxLayout()
        # Scroll area for the image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setWidget(self.image_label)
        btn_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        btn_layout.addWidget(self.btn_zoom_out)
        btn_layout.addWidget(self.btn_zoom_in)
        layout.addWidget(self.scroll_area)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(192, 288)  # Minimum size with correct aspect ratio

    def set_image(self, image_path):
        self.image_path = image_path
        self.zoom = 1.0
        self.pixmap = QPixmap(self.image_path) if self.image_path and os.path.exists(self.image_path) else None
        self.update_image()

    def zoom_in(self):
        self.zoom = min(self.zoom + 0.1, 3.0)
        self.update_image()

    def zoom_out(self):
        self.zoom = max(self.zoom - 0.1, 0.2)
        self.update_image()

    def resizeEvent(self, event):
        self.update_image()
        super().resizeEvent(event)

    def update_image(self):
        if self.pixmap and not self.pixmap.isNull():
            # Calculate the largest size that fits in the widget while maintaining aspect ratio
            w = self.width()
            h = self.height()
            # Adjust for zoom
            w = int(w * self.zoom)
            h = int(h * self.zoom)
            # Maintain card aspect ratio
            if w / h > CARD_ASPECT_RATIO:
                w = int(h * CARD_ASPECT_RATIO)
            else:
                h = int(w / CARD_ASPECT_RATIO)
            scaled = self.pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.image_label.setText("")
        else:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("Image not found") 