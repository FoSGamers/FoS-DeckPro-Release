import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("FoSLauncher")

class ConfigManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(self.base_dir, "modules", "config.json")
        self.config: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from config.json"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self.config = json.load(f)
                logger.info("Successfully loaded configuration")
            else:
                logger.warning(f"Configuration file not found at {self.config_path}")
                self.config = {
                    "base_dir": self.base_dir,
                    "access": {
                        "modules": {
                            "chatbot_plus": {
                                "features": {
                                    "youtube": True,
                                    "websocket": True
                                }
                            },
                            "chatsplitter": {
                                "features": {
                                    "enabled": True
                                }
                            }
                        }
                    },
                    "websocket": {
                        "host": "localhost",
                        "port": 8765
                    },
                    "gui": {
                        "theme": "dark",
                        "window_size": "800x600"
                    }
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = {}
            
    def save_config(self) -> None:
        """Save configuration to config.json"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            logger.info("Successfully saved configuration")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        try:
            return self.config.get(key, default)
        except Exception as e:
            logger.error(f"Error getting configuration value for {key}: {e}")
            return default
            
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        try:
            self.config[key] = value
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error setting configuration value for {key}: {e}")
            return False
            
    def get_module_config(self, module: str) -> Dict[str, Any]:
        """Get configuration for a specific module"""
        try:
            return self.config.get("access", {}).get("modules", {}).get(module, {})
        except Exception as e:
            logger.error(f"Error getting module configuration for {module}: {e}")
            return {}
            
    def validate_config(self) -> bool:
        """Validate configuration structure"""
        try:
            required_keys = ["base_dir", "access", "websocket", "gui"]
            return all(key in self.config for key in required_keys)
        except Exception as e:
            logger.error(f"Error validating configuration: {e}")
            return False
            
    def update_module_config(self, module: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific module"""
        try:
            self.config.setdefault("access", {}).setdefault("modules", {})[module] = config
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error updating module configuration for {module}: {e}")
            return False 