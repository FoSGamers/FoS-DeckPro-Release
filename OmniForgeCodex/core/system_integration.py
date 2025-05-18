from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon
import platform
import os

class SystemIntegration(QObject):
    file_dropped = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_system_tray()
        self.setup_file_associations()
        self.setup_drag_drop()
        
    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(QIcon(":/icons/app.png"))
        self.tray_icon.setToolTip("OmniForgeCodex")
        
        menu = QMenu()
        show_action = menu.addAction("Show")
        show_action.triggered.connect(self.show_main_window)
        
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
    def setup_file_associations(self):
        if platform.system() == "Windows":
            self._setup_windows_associations()
        elif platform.system() == "Darwin":
            self._setup_macos_associations()
        elif platform.system() == "Linux":
            self._setup_linux_associations()
            
    def setup_drag_drop(self):
        # Implement drag and drop support
        pass
        
    def show_notification(self, title: str, message: str):
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information) 