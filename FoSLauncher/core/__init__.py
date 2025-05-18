"""Core package for FoSLauncher"""

from .launcher import Launcher
from .gui_launcher import GUILauncher
from .events.event_system import EventSystem, Event, EventPriority
from .plugins.plugin_manager import PluginManager
from .plugins.plugin_interface import PluginInterface, PluginDependency
from .config.config_manager import ConfigManager

__all__ = [
    'Launcher',
    'GUILauncher',
    'EventSystem',
    'Event',
    'EventPriority',
    'PluginManager',
    'PluginInterface',
    'PluginDependency',
    'ConfigManager'
] 