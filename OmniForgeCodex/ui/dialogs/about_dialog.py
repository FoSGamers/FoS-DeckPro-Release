from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QTextBrowser
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from ui.ui_utils import UIUtils
import json
import os
from config import Config

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_utils = UIUtils()
        self.setup_ui()
        self.load_about_data()
        
    def setup_ui(self):
        """Setup the about dialog UI"""
        self.setWindowTitle("About OmniForgeCodex")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Logo and title
        header_layout = QHBoxLayout()
        
        logo_label = QLabel()
        logo_pixmap = QPixmap(":/icons/app.png")
        logo_label.setPixmap(logo_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        title_layout = QVBoxLayout()
        title_label = QLabel("OmniForgeCodex")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {Config.VERSION}")
        version_label.setFont(QFont("Arial", 10))
        title_layout.addWidget(version_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # About tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        
        description = QTextBrowser()
        description.setOpenExternalLinks(True)
        description.setHtml(self.get_description_html())
        about_layout.addWidget(description)
        
        tab_widget.addTab(about_tab, "About")
        
        # Credits tab
        credits_tab = QWidget()
        credits_layout = QVBoxLayout(credits_tab)
        
        credits = QTextBrowser()
        credits.setOpenExternalLinks(True)
        credits.setHtml(self.get_credits_html())
        credits_layout.addWidget(credits)
        
        tab_widget.addTab(credits_tab, "Credits")
        
        # License tab
        license_tab = QWidget()
        license_layout = QVBoxLayout(license_tab)
        
        license_text = QTextBrowser()
        license_text.setPlainText(self.get_license_text())
        license_layout.addWidget(license_text)
        
        tab_widget.addTab(license_tab, "License")
        
        layout.addWidget(tab_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = self.ui_utils.create_styled_button("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def get_description_html(self) -> str:
        """Get the description HTML"""
        return """
        <h2>OmniForgeCodex</h2>
        <p>OmniForgeCodex is a comprehensive tool for managing and analyzing Magic: The Gathering collections,
        building decks, and simulating games using MTG Forge.</p>
        
        <h3>Features</h3>
        <ul>
            <li>Collection Management</li>
            <li>Deck Building</li>
            <li>Game Simulation</li>
            <li>Analytics</li>
            <li>Trading Tools</li>
        </ul>
        
        <h3>Links</h3>
        <p>
            <a href="https://github.com/yourusername/OmniForgeCodex">GitHub Repository</a><br>
            <a href="https://github.com/yourusername/OmniForgeCodex/issues">Report Issues</a><br>
            <a href="https://github.com/yourusername/OmniForgeCodex/wiki">Documentation</a>
        </p>
        """
        
    def get_credits_html(self) -> str:
        """Get the credits HTML"""
        return """
        <h2>Credits</h2>
        
        <h3>Development</h3>
        <p>Created by [Your Name]</p>
        
        <h3>Contributors</h3>
        <ul>
            <li>Contributor 1</li>
            <li>Contributor 2</li>
            <li>Contributor 3</li>
        </ul>
        
        <h3>Special Thanks</h3>
        <p>Thanks to the MTG Forge team for their excellent work on the Forge project.</p>
        
        <h3>Libraries</h3>
        <ul>
            <li>PySide6 - Qt for Python</li>
            <li>Scryfall API</li>
            <li>Other libraries...</li>
        </ul>
        """
        
    def get_license_text(self) -> str:
        """Get the license text"""
        return """
        MIT License

        Copyright (c) 2024 [Your Name]

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
        """ 