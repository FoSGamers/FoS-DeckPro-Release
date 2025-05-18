import os
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import jsonschema
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigManager:
    """Manages application configuration with validation and hot reloading"""
    
    def __init__(self, config_path: str = "config.json", schema_path: str = "config_schema.json"):
        self.logger = logging.getLogger("config_manager")
        self.config_path = Path(config_path)
        self.schema_path = Path(schema_path)
        self.config: Dict[str, Any] = {}
        self.schema: Dict[str, Any] = {}
        self.observer = None
        self.callbacks: List[Callable] = []
        self.plugin_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Load schema first
        self.load_schema()
        
        # Then load config
        self.load_config()
        
        # Setup file watcher
        self.setup_watcher()
    
    def load_schema(self) -> bool:
        """Load the JSON schema for validation"""
        try:
            if self.schema_path.exists():
                with open(self.schema_path) as f:
                    self.schema = json.load(f)
                return True
            self.logger.warning("Schema file not found")
            return False
        except Exception as e:
            self.logger.error(f"Failed to load schema: {str(e)}")
            return False
    
    def register_plugin_schema(self, plugin_name: str, schema: Dict[str, Any]) -> bool:
        """Register a plugin-specific configuration schema"""
        try:
            self.plugin_schemas[plugin_name] = schema
            return True
        except Exception as e:
            self.logger.error(f"Failed to register schema for plugin {plugin_name}: {str(e)}")
            return False
    
    def validate_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration against its schema"""
        try:
            if plugin_name in self.plugin_schemas:
                jsonschema.validate(instance=config, schema=self.plugin_schemas[plugin_name])
            return True
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Plugin {plugin_name} configuration validation failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error validating plugin {plugin_name} configuration: {str(e)}")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """Load and validate the configuration"""
        try:
            if self.config_path.exists():
                with open(self.config_path) as f:
                    self.config = json.load(f)
                
                # Validate against schema
                if self.schema:
                    jsonschema.validate(instance=self.config, schema=self.schema)
                
                # Validate plugin configurations
                for plugin_name, plugin_config in self.config.get("plugins", {}).items():
                    if not self.validate_plugin_config(plugin_name, plugin_config):
                        self.logger.warning(f"Using default configuration for plugin {plugin_name}")
                        self.config["plugins"][plugin_name] = self.get_default_plugin_config(plugin_name)
                
                self.logger.info("Configuration loaded and validated")
            else:
                self.logger.warning("Configuration file not found, using defaults")
                self.config = self.get_default_config()
            
            return self.config
            
        except jsonschema.exceptions.ValidationError as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            return self.get_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            return self.get_default_config()
    
    def get_default_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get default configuration for a plugin"""
        return {
            "enabled": True,
            "base_dir": f"plugins/{plugin_name}",
            "requires_code": True,
            "access_level": "basic",
            "settings": {}
        }
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "plugins": {},
            "settings": {
                "auto_start_plugins": True,
                "environment": "development"
            },
            "global": {
                "security": {
                    "current_access": [],
                    "master_code": None
                }
            }
        }
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin"""
        return self.config.get("plugins", {}).get(plugin_name, self.get_default_plugin_config(plugin_name))
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Set configuration for a specific plugin"""
        try:
            if not self.validate_plugin_config(plugin_name, config):
                return False
            
            if "plugins" not in self.config:
                self.config["plugins"] = {}
            
            self.config["plugins"][plugin_name] = config
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Failed to set configuration for plugin {plugin_name}: {str(e)}")
            return False
    
    def save_config(self) -> bool:
        """Save the current configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info("Configuration saved")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False
    
    def setup_watcher(self) -> None:
        """Setup file system watcher for hot reloading"""
        class ConfigHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
            
            def on_modified(self, event):
                if event.src_path == str(self.manager.config_path):
                    self.manager.reload_config()
        
        self.observer = Observer()
        self.observer.schedule(ConfigHandler(self), str(self.config_path.parent))
        self.observer.start()
    
    def reload_config(self) -> None:
        """Reload configuration and notify callbacks"""
        if self.load_config():
            for callback in self.callbacks:
                try:
                    callback(self.config)
                except Exception as e:
                    self.logger.error(f"Error in config reload callback: {str(e)}")
    
    def register_callback(self, callback) -> None:
        """Register a callback for config changes"""
        self.callbacks.append(callback)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        try:
            keys = key.split('.')
            current = self.config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Failed to set configuration value: {str(e)}")
            return False
    
    def __del__(self):
        """Cleanup watcher on destruction"""
        if self.observer:
            self.observer.stop()
            self.observer.join() 