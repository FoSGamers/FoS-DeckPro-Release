import os
import logging
from typing import Dict, Any, Optional
from .config.config_manager import ConfigManager
from .plugins.plugin_manager import PluginManager
from .events.event_system import EventSystem, Event, EventPriority

class Launcher:
    """Main launcher class that coordinates the plugin system"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = {
            "global": {
                "security": {
                    "current_access": ["basic"],
                    "master_code": "FoSGamers2024"
                }
            },
            "plugins": {},
            "settings": {
                "auto_start_plugins": True,
                "environment": "development"
            }
        }
        self.plugin_manager = None
        self.event_system = None
        self.gui_launcher = None
        self._running = False
        self.logger = logging.getLogger("launcher")
        self.master_access = False
        
        # Load configuration
        try:
            config_manager = ConfigManager(self.config_path)
            loaded_config = config_manager.load_config()
            if loaded_config:
                self.config.update(loaded_config)
            self.logger.info("Configuration loaded and validated")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            # Using default config initialized above

    def get_config(self, section=None, default=None):
        """Get configuration section or full config"""
        if section:
            return self.config.get(section, default)
        return self.config

    def set_master_access(self, enabled: bool):
        """Set master access status"""
        current_access = self.config.get("global", {}).get("security", {}).get("current_access", [])
        if enabled and "master" not in current_access:
            current_access.append("master")
        elif not enabled and "master" in current_access:
            current_access.remove("master")
        self.config["global"]["security"]["current_access"] = current_access
        self.master_access = enabled

    def start(self) -> bool:
        """Start the launcher"""
        try:
            self.logger.info("Starting launcher")
            
            # Initialize event system
            self.event_system = EventSystem()
            self.event_system.start()
            self.logger.info("Event system started")
            
            # Initialize plugin manager
            self.plugin_manager = PluginManager(self.config, self.event_system)
            
            # Load enabled plugins
            for plugin_name, plugin_config in self.config.get("plugins", {}).items():
                if plugin_config.get("enabled", True):
                    try:
                        self.plugin_manager.load_plugin(plugin_name, plugin_config)
                    except Exception as e:
                        self.logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
            
            # Start GUI if in the config
            if self.config.get("settings", {}).get("auto_start_plugins", True):
                try:
                    from .gui_launcher import GUILauncher
                    self.gui_launcher = GUILauncher(self)
                    self.gui_launcher.start()
                except Exception as e:
                    self.logger.error(f"Failed to start GUI launcher: {str(e)}")
            
            self._running = True
            self.logger.info("Launcher started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start launcher: {str(e)}")
            return False

    def stop(self) -> bool:
        """Stop the launcher"""
        try:
            self.logger.info("Stopping launcher")
            
            # Stop GUI launcher
            if self.gui_launcher:
                try:
                    self.gui_launcher.stop()
                except Exception as e:
                    self.logger.error(f"Failed to stop GUI launcher: {str(e)}")
            
            # Stop event system
            if self.event_system:
                try:
                    self.event_system.stop()
                    self.logger.info("Event system stopped")
                except Exception as e:
                    self.logger.error(f"Failed to stop event system: {str(e)}")
            
            self._running = False
            self.logger.info("Launcher stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop launcher: {str(e)}")
            return False
    
    def install_plugin(self, plugin_name: str, config: dict) -> bool:
        """Install a new plugin"""
        try:
            # Add launcher reference to plugin config
            config["launcher"] = self
            
            # Add plugin to config
            self.config_manager.set(f"plugins.{plugin_name}", config)
            
            # Load and start plugin
            if self.plugin_manager.load_plugin(plugin_name, config):
                if self.config_manager.get("settings.auto_start_plugins", True):
                    return self.plugin_manager.start_plugin(plugin_name)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to install plugin {plugin_name}: {str(e)}")
            return False
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin"""
        try:
            # Stop and unload plugin
            if self.plugin_manager.stop_plugin(plugin_name):
                if self.plugin_manager.unload_plugin(plugin_name):
                    # Remove from config
                    self.config_manager.set(f"plugins.{plugin_name}", None)
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to uninstall plugin {plugin_name}: {str(e)}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Any]:
        """Get a plugin instance"""
        return self.plugin_manager.get_plugin(plugin_name)
    
    def broadcast_event(self, event_name: str, data: Any, priority: EventPriority = EventPriority.NORMAL) -> None:
        """Broadcast an event to all plugins"""
        event = Event(name=event_name, data=data, priority=priority)
        self.event_system.emit(event)
    
    def has_plugin_access(self, plugin_name: str) -> bool:
        """Check if user has access to a plugin"""
        if self.master_access:
            return True
            
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return False
            
        # Check plugin's access requirements
        plugin_config = self.config_manager.get(f"plugins.{plugin_name}", {})
        if not plugin_config.get("requires_code", True):
            return True
            
        # Check user's access level
        user_access = self.config_manager.get("global.security.current_access", [])
        plugin_access = plugin_config.get("access_level", "none")
        
        return plugin_access in user_access or plugin_access == "none" 