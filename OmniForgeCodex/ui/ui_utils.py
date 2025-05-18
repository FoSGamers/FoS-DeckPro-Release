from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGroupBox, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPalette, QColor
from typing import Optional, Callable, Dict, Any
import json
import os
from config import Config

class UIUtils:
    @staticmethod
    def create_styled_button(text: str, icon: Optional[str] = None, 
                           tooltip: Optional[str] = None) -> QPushButton:
        """Create a styled button with optional icon and tooltip"""
        button = QPushButton(text)
        if icon:
            button.setIcon(QIcon(icon))
        if tooltip:
            button.setToolTip(tooltip)
        button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        return button

    @staticmethod
    def create_styled_line_edit(placeholder: Optional[str] = None,
                              tooltip: Optional[str] = None) -> QLineEdit:
        """Create a styled line edit with optional placeholder and tooltip"""
        line_edit = QLineEdit()
        if placeholder:
            line_edit.setPlaceholderText(placeholder)
        if tooltip:
            line_edit.setToolTip(tooltip)
        line_edit.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #BDBDBD;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        return line_edit

    @staticmethod
    def create_styled_combo_box(items: list, tooltip: Optional[str] = None) -> QComboBox:
        """Create a styled combo box with items and optional tooltip"""
        combo = QComboBox()
        combo.addItems(items)
        if tooltip:
            combo.setToolTip(tooltip)
        combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #BDBDBD;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(:/icons/down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        return combo

    @staticmethod
    def create_styled_group_box(title: str) -> QGroupBox:
        """Create a styled group box with title"""
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #BDBDBD;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        return group

    @staticmethod
    def create_scroll_area(widget: QWidget) -> QScrollArea:
        """Create a scroll area containing the given widget"""
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        return scroll

    @staticmethod
    def create_separator() -> QFrame:
        """Create a horizontal separator line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #BDBDBD;")
        return line

    @staticmethod
    def apply_dark_theme(widget: QWidget):
        """Apply dark theme to a widget and its children"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        widget.setPalette(palette)

    @staticmethod
    def create_tooltip(text: str) -> str:
        """Create HTML formatted tooltip"""
        return f'<div style="background-color: #424242; color: white; padding: 5px; border-radius: 3px;">{text}</div>'

    @staticmethod
    def create_error_label(text: str) -> QLabel:
        """Create a styled error label"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                color: #D32F2F;
                padding: 5px;
                border-radius: 3px;
                background-color: #FFEBEE;
            }
        """)
        return label

    @staticmethod
    def create_success_label(text: str) -> QLabel:
        """Create a styled success label"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                color: #388E3C;
                padding: 5px;
                border-radius: 3px;
                background-color: #E8F5E9;
            }
        """)
        return label 