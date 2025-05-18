from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QToolBar,
    QMenu, QMenuBar, QDockWidget, QWidget, QVBoxLayout,
    QMessageBox, QSystemTrayIcon, QMenu as QSystemTrayMenu, QApplication,
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QTextBrowser
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QShortcut, QPixmap, QFont
from PySide6.QtCore import Qt, QSettings, QSize, QObject, Signal, Slot, QTimer, QTranslator, QLocale
from ui.collection_tab import CollectionTab
from ui.deck_builder_tab import DeckBuilderTab
from ui.simulation_tab import SimulationTab
from ui.analytics_tab import AnalyticsTab
from ui.selling_tools_tab import SellingToolsTab
from core.inventory_manager import InventoryManager
from core.scryfall_client import ScryfallClient
from core.codex_rules_manager import CodexRulesManager
from core.simulation_knowledge_base import SimulationKnowledgeBase
from core.deck_builder_engine import DeckBuilderEngine
from core.mtg_forge_simulator import MTGForgeSimulator
from core.output_generator import OutputGenerator
from core.analytics_engine import AnalyticsEngine
from core.trade_buylist_manager import TradeBuylistManager
from ui.ui_utils import UIUtils
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.widgets.quick_search import QuickSearchWidget
from ui.widgets.recent_files import RecentFilesWidget
from ui.widgets.status_widget import StatusWidget
from config import Config
import json
import os
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path
import threading
import time
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor
import psutil
import signal
import sys
from requests.exceptions import RequestException
from jsonschema.exceptions import ValidationError
from watchdog.events import FileSystemEvent

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings()
        self.ui_utils = UIUtils()
        self.setup_window()
        self.setup_components()
        self.setup_ui()
        self.setup_shortcuts()
        self.load_settings()
        
    def setup_window(self):
        """Setup main window properties"""
        self.setWindowTitle("OmniForgeCodex")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # Apply theme
        if self.settings.value("theme", "dark") == "dark":
            self.ui_utils.apply_dark_theme(self)
            
    def setup_components(self):
        """Initialize core components"""
        self.scryfall_client = ScryfallClient()
        self.inventory_manager = InventoryManager()
        self.rules_manager = CodexRulesManager()
        self.knowledge_base = SimulationKnowledgeBase()
        self.deck_builder = DeckBuilderEngine(
            self.inventory_manager, self.scryfall_client,
            self.rules_manager, self.knowledge_base
        )
        self.simulator = MTGForgeSimulator()
        self.output_generator = OutputGenerator()
        self.analytics_engine = AnalyticsEngine()
        self.trade_manager = TradeBuylistManager(self.scryfall_client)
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        self.setup_dock_widgets()
        self.setup_tabs()
        
    def setup_menu_bar(self):
        """Setup the menu bar with enhanced features"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        import_menu = file_menu.addMenu("Import")
        import_menu.addAction("Import Collection", self.import_collection)
        import_menu.addAction("Import Deck", self.import_deck)
        
        export_menu = file_menu.addMenu("Export")
        export_menu.addAction("Export Collection", self.export_collection)
        export_menu.addAction("Export Deck", self.export_deck)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        toolbar_action = QAction("Toolbar", self)
        toolbar_action.setCheckable(True)
        toolbar_action.setChecked(True)
        toolbar_action.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(toolbar_action)
        
        statusbar_action = QAction("Status Bar", self)
        statusbar_action.setCheckable(True)
        statusbar_action.setChecked(True)
        statusbar_action.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(statusbar_action)
        
        view_menu.addSeparator()
        
        theme_menu = view_menu.addMenu("Theme")
        theme_menu.addAction("Light", lambda: self.change_theme("light"))
        theme_menu.addAction("Dark", lambda: self.change_theme("dark"))
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        help_action = QAction("Documentation", self)
        help_action.triggered.connect(self.show_documentation)
        help_menu.addAction(help_action)
        
    def setup_toolbar(self):
        """Setup the toolbar with enhanced features"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)
        
        # Add toolbar actions
        self.toolbar.addAction(self.ui_utils.create_styled_button("New", ":/icons/new.png", "Create new file"))
        self.toolbar.addAction(self.ui_utils.create_styled_button("Open", ":/icons/open.png", "Open file"))
        self.toolbar.addAction(self.ui_utils.create_styled_button("Save", ":/icons/save.png", "Save file"))
        
        self.toolbar.addSeparator()
        
        self.toolbar.addAction(self.ui_utils.create_styled_button("Undo", ":/icons/undo.png", "Undo last action"))
        self.toolbar.addAction(self.ui_utils.create_styled_button("Redo", ":/icons/redo.png", "Redo last action"))
        
    def setup_status_bar(self):
        """Setup the status bar with enhanced features"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status widgets
        self.status_widget = StatusWidget()
        self.status_bar.addPermanentWidget(self.status_widget)
        
        self.status_bar.showMessage("Ready")
        
    def setup_dock_widgets(self):
        """Setup dock widgets for additional features"""
        # Quick Search Dock
        quick_search_dock = QDockWidget("Quick Search", self)
        quick_search_dock.setWidget(QuickSearchWidget(self.scryfall_client))
        self.addDockWidget(Qt.RightDockWidgetArea, quick_search_dock)
        
        # Recent Files Dock
        recent_files_dock = QDockWidget("Recent Files", self)
        recent_files_dock.setWidget(RecentFilesWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, recent_files_dock)
        
    def setup_tabs(self):
        """Setup the main tab widget with enhanced features"""
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)
        
        # Add tabs
        self.collection_tab = CollectionTab(self.inventory_manager)
        self.deck_builder_tab = DeckBuilderTab(self.deck_builder, self.output_generator)
        self.simulation_tab = SimulationTab(self.simulator, self.knowledge_base, self.output_generator)
        self.analytics_tab = AnalyticsTab(self.analytics_engine, self.inventory_manager)
        self.selling_tools_tab = SellingToolsTab(self.trade_manager, self.output_generator)
        
        self.tabs.addTab(self.collection_tab, "Collection")
        self.tabs.addTab(self.deck_builder_tab, "Deck Builder")
        self.tabs.addTab(self.simulation_tab, "Simulation Hub")
        self.tabs.addTab(self.analytics_tab, "Analytics")
        self.tabs.addTab(self.selling_tools_tab, "Selling Tools")
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Global shortcuts
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_file)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_file)
        QShortcut(QKeySequence("Ctrl+N"), self, self.new_file)
        
        # Tab shortcuts
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.previous_tab)
        
    def load_settings(self):
        """Load application settings"""
        # Load window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Load window state
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
            
        # Load recent files
        recent_files = self.settings.value("recentFiles", [])
        if recent_files:
            self.recent_files_widget.update_files(recent_files)
            
    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("recentFiles", self.recent_files_widget.get_files())
        
    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self, "Confirm Exit",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.save_settings()
            event.accept()
        else:
            event.ignore()
