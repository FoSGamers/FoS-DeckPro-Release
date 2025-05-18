from PySide6.QtCore import QSettings, QByteArray
from typing import Dict, Any
import json

class StateManager:
    def __init__(self):
        self.settings = QSettings()
        
    def save_window_state(self, window):
        self.settings.setValue("window/geometry", window.saveGeometry())
        self.settings.setValue("window/state", window.saveState())
        
    def restore_window_state(self, window):
        geometry = self.settings.value("window/geometry")
        if geometry:
            window.restoreGeometry(geometry)
            
        state = self.settings.value("window/state")
        if state:
            window.restoreState(state)
            
    def save_recent_files(self, files: list):
        self.settings.setValue("recent_files", files)
        
    def get_recent_files(self) -> list:
        return self.settings.value("recent_files", [], type=list)
        
    def save_user_preferences(self, preferences: Dict[str, Any]):
        self.settings.setValue("preferences", json.dumps(preferences))
        
    def get_user_preferences(self) -> Dict[str, Any]:
        preferences = self.settings.value("preferences", "{}")
        return json.loads(preferences) 