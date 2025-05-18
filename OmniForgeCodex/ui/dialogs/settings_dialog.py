from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QComboBox, QCheckBox, QSpinBox,
    QPushButton, QGroupBox, QFormLayout, QFileDialog,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QSettings
from ui.ui_utils import UIUtils
from config import Config
import os

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.ui_utils = UIUtils()
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the settings dialog UI"""
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        
        # Add tabs
        tab_widget.addTab(self.create_general_tab(), "General")
        tab_widget.addTab(self.create_appearance_tab(), "Appearance")
        tab_widget.addTab(self.create_paths_tab(), "Paths")
        tab_widget.addTab(self.create_advanced_tab(), "Advanced")
        
        layout.addWidget(tab_widget)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        save_button = self.ui_utils.create_styled_button("Save")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = self.ui_utils.create_styled_button("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def create_general_tab(self) -> QWidget:
        """Create the general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # General settings group
        general_group = self.ui_utils.create_styled_group_box("General Settings")
        general_layout = QFormLayout()
        
        # Auto-save
        self.auto_save_checkbox = QCheckBox()
        self.auto_save_checkbox.setToolTip("Automatically save changes")
        general_layout.addRow("Auto-save:", self.auto_save_checkbox)
        
        # Auto-save interval
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setSuffix(" minutes")
        self.auto_save_interval.setToolTip("Interval between auto-saves")
        general_layout.addRow("Auto-save interval:", self.auto_save_interval)
        
        # Default format
        self.default_format = QComboBox()
        self.default_format.addItems(["pauper_60", "pauper_edh"])
        self.default_format.setToolTip("Default deck format")
        general_layout.addRow("Default format:", self.default_format)
        
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)
        
        # Recent files group
        recent_group = self.ui_utils.create_styled_group_box("Recent Files")
        recent_layout = QFormLayout()
        
        # Max recent files
        self.max_recent_files = QSpinBox()
        self.max_recent_files.setRange(1, 20)
        self.max_recent_files.setToolTip("Maximum number of recent files to remember")
        recent_layout.addRow("Maximum recent files:", self.max_recent_files)
        
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        return widget
        
    def create_appearance_tab(self) -> QWidget:
        """Create the appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme settings group
        theme_group = self.ui_utils.create_styled_group_box("Theme")
        theme_layout = QFormLayout()
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setToolTip("Application theme")
        theme_layout.addRow("Theme:", self.theme_combo)
        
        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setToolTip("Application font size")
        theme_layout.addRow("Font size:", self.font_size)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Display settings group
        display_group = self.ui_utils.create_styled_group_box("Display")
        display_layout = QFormLayout()
        
        # Show toolbar
        self.show_toolbar = QCheckBox()
        self.show_toolbar.setToolTip("Show main toolbar")
        display_layout.addRow("Show toolbar:", self.show_toolbar)
        
        # Show status bar
        self.show_statusbar = QCheckBox()
        self.show_statusbar.setToolTip("Show status bar")
        display_layout.addRow("Show status bar:", self.show_statusbar)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        return widget
        
    def create_paths_tab(self) -> QWidget:
        """Create the paths settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Forge settings group
        forge_group = self.ui_utils.create_styled_group_box("MTG Forge")
        forge_layout = QFormLayout()
        
        # Forge executable path
        forge_path_layout = QHBoxLayout()
        self.forge_path = QLineEdit()
        self.forge_path.setReadOnly(True)
        browse_button = self.ui_utils.create_styled_button("Browse")
        browse_button.clicked.connect(self.browse_forge_path)
        forge_path_layout.addWidget(self.forge_path)
        forge_path_layout.addWidget(browse_button)
        forge_layout.addRow("Forge executable:", forge_path_layout)
        
        # Forge user data path
        user_data_layout = QHBoxLayout()
        self.user_data_path = QLineEdit()
        self.user_data_path.setReadOnly(True)
        browse_button = self.ui_utils.create_styled_button("Browse")
        browse_button.clicked.connect(self.browse_user_data_path)
        user_data_layout.addWidget(self.user_data_path)
        user_data_layout.addWidget(browse_button)
        forge_layout.addRow("User data directory:", user_data_layout)
        
        forge_group.setLayout(forge_layout)
        layout.addWidget(forge_group)
        
        # Export settings group
        export_group = self.ui_utils.create_styled_group_box("Export")
        export_layout = QFormLayout()
        
        # Default export directory
        export_dir_layout = QHBoxLayout()
        self.export_dir = QLineEdit()
        self.export_dir.setReadOnly(True)
        browse_button = self.ui_utils.create_styled_button("Browse")
        browse_button.clicked.connect(self.browse_export_dir)
        export_dir_layout.addWidget(self.export_dir)
        export_dir_layout.addWidget(browse_button)
        export_layout.addRow("Default export directory:", export_dir_layout)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        return widget
        
    def create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Simulation settings group
        sim_group = self.ui_utils.create_styled_group_box("Simulation")
        sim_layout = QFormLayout()
        
        # Default simulation runs
        self.sim_runs = QSpinBox()
        self.sim_runs.setRange(1, 1000)
        self.sim_runs.setToolTip("Default number of simulation runs")
        sim_layout.addRow("Default simulation runs:", self.sim_runs)
        
        # Simulation timeout
        self.sim_timeout = QSpinBox()
        self.sim_timeout.setRange(30, 3600)
        self.sim_timeout.setSuffix(" seconds")
        self.sim_timeout.setToolTip("Maximum time for a single simulation")
        sim_layout.addRow("Simulation timeout:", self.sim_timeout)
        
        sim_group.setLayout(sim_layout)
        layout.addWidget(sim_group)
        
        # Cache settings group
        cache_group = self.ui_utils.create_styled_group_box("Cache")
        cache_layout = QFormLayout()
        
        # Cache size
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 10000)
        self.cache_size.setSuffix(" MB")
        self.cache_size.setToolTip("Maximum cache size")
        cache_layout.addRow("Cache size:", self.cache_size)
        
        # Cache expiry
        self.cache_expiry = QSpinBox()
        self.cache_expiry.setRange(1, 24)
        self.cache_expiry.setSuffix(" hours")
        self.cache_expiry.setToolTip("Cache expiration time")
        cache_layout.addRow("Cache expiry:", self.cache_expiry)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        return widget
        
    def load_settings(self):
        """Load settings from QSettings"""
        # General settings
        self.auto_save_checkbox.setChecked(self.settings.value("auto_save", True, type=bool))
        self.auto_save_interval.setValue(self.settings.value("auto_save_interval", 5, type=int))
        self.default_format.setCurrentText(self.settings.value("default_format", "pauper_60"))
        self.max_recent_files.setValue(self.settings.value("max_recent_files", 10, type=int))
        
        # Appearance settings
        self.theme_combo.setCurrentText(self.settings.value("theme", "Light"))
        self.font_size.setValue(self.settings.value("font_size", 12, type=int))
        self.show_toolbar.setChecked(self.settings.value("show_toolbar", True, type=bool))
        self.show_statusbar.setChecked(self.settings.value("show_statusbar", True, type=bool))
        
        # Path settings
        self.forge_path.setText(self.settings.value("forge_path", Config.FORGE_EXECUTABLE))
        self.user_data_path.setText(self.settings.value("user_data_path", Config.FORGE_USER_DATA))
        self.export_dir.setText(self.settings.value("export_dir", Config.OUTPUT_DIR))
        
        # Advanced settings
        self.sim_runs.setValue(self.settings.value("sim_runs", 100, type=int))
        self.sim_timeout.setValue(self.settings.value("sim_timeout", 300, type=int))
        self.cache_size.setValue(self.settings.value("cache_size", 1000, type=int))
        self.cache_expiry.setValue(self.settings.value("cache_expiry", 1, type=int))
        
    def save_settings(self):
        """Save settings to QSettings"""
        # General settings
        self.settings.setValue("auto_save", self.auto_save_checkbox.isChecked())
        self.settings.setValue("auto_save_interval", self.auto_save_interval.value())
        self.settings.setValue("default_format", self.default_format.currentText())
        self.settings.setValue("max_recent_files", self.max_recent_files.value())
        
        # Appearance settings
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("font_size", self.font_size.value())
        self.settings.setValue("show_toolbar", self.show_toolbar.isChecked())
        self.settings.setValue("show_statusbar", self.show_statusbar.isChecked())
        
        # Path settings
        self.settings.setValue("forge_path", self.forge_path.text())
        self.settings.setValue("user_data_path", self.user_data_path.text())
        self.settings.setValue("export_dir", self.export_dir.text())
        
        # Advanced settings
        self.settings.setValue("sim_runs", self.sim_runs.value())
        self.settings.setValue("sim_timeout", self.sim_timeout.value())
        self.settings.setValue("cache_size", self.cache_size.value())
        self.settings.setValue("cache_expiry", self.cache_expiry.value())
        
        self.accept()
        
    def browse_forge_path(self):
        """Browse for Forge executable"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Forge Executable", "",
            "Executable Files (*.exe *.sh);;All Files (*.*)"
        )
        if path:
            self.forge_path.setText(path)
            
    def browse_user_data_path(self):
        """Browse for Forge user data directory"""
        path = QFileDialog.getExistingDirectory(
            self, "Select User Data Directory", ""
        )
        if path:
            self.user_data_path.setText(path)
            
    def browse_export_dir(self):
        """Browse for export directory"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Export Directory", ""
        )
        if path:
            self.export_dir.setText(path) 