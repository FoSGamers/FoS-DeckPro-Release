from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod

@dataclass
class PluginDependency:
    """Represents a plugin dependency"""
    name: str
    version: str
    optional: bool = False

class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(f"plugin.{self.get_name()}")
        self.config = config
        self._running = False
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get the plugin version"""
        pass
    
    @property
    def dependencies(self) -> List[PluginDependency]:
        """Get plugin dependencies"""
        return []
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the plugin name"""
        pass
    
    def start(self) -> bool:
        """Start the plugin"""
        try:
            if not self._running:
                self._running = True
                self.on_start()
                self.logger.info("Plugin started")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to start plugin: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the plugin"""
        try:
            if self._running:
                self._running = False
                self.on_stop()
                self.logger.info("Plugin stopped")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to stop plugin: {str(e)}")
            return False
    
    def is_running(self) -> bool:
        """Check if plugin is running"""
        return self._running
    
    def handle_event(self, event_name: str, data: Any) -> None:
        """Handle an event"""
        try:
            if self._running:
                self.on_event(event_name, data)
        except Exception as e:
            self.logger.error(f"Error handling event {event_name}: {str(e)}")
    
    def on_start(self) -> None:
        """Called when plugin starts"""
        pass
    
    def on_stop(self) -> None:
        """Called when plugin stops"""
        pass
    
    def on_event(self, event_name: str, data: Any) -> None:
        """Called when an event is received"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        try:
            keys = key.split('.')
            current = self.config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
            return True
        except Exception as e:
            self.logger.error(f"Failed to set configuration value: {str(e)}")
            return False 