from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PluginInterface(ABC):
    """Base interface that all plugins must implement"""
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """Initialize the plugin with its configuration"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """Start the plugin"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the plugin"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the plugin name"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get the plugin version"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get the plugin description"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the plugin's configuration schema"""
        pass
    
    @abstractmethod
    def handle_event(self, event_name: str, data: Any) -> Optional[Any]:
        """Handle events from other plugins or the launcher"""
        pass 