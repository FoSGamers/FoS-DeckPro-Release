import os
import json
import logging
from typing import Dict, Any, Optional
from jsonschema import validate, ValidationError

logger = logging.getLogger("FoSLauncher")

class ConfigManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(self.base_dir, "config")
        self.global_config: Dict[str, Any] = {}
        self.module_configs: Dict[str, Dict[str, Any]] = {}
        self.schema: Dict[str, Any] = {}
        self.load_all_configs()
        
    def load_all_configs(self) -> None:
        """Load all configuration files"""
        try:
            # Load schema
            schema_path = os.path.join(self.config_dir, "schema.json")
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    self.schema = json.load(f)
            
            # Load global config
            global_path = os.path.join(self.config_dir, "global.json")
            if os.path.exists(global_path):
                with open(global_path, "r") as f:
                    self.global_config = json.load(f)
                    if self.schema:
                        validate(instance=self.global_config, schema=self.schema)
            
            # Load module configs
            modules_dir = os.path.join(self.config_dir, "modules")
            if os.path.exists(modules_dir):
                for filename in os.listdir(modules_dir):
                    if filename.endswith(".json"):
                        module_name = filename[:-5]  # Remove .json extension
                        with open(os.path.join(modules_dir, filename), "r") as f:
                            self.module_configs[module_name] = json.load(f)
            
            logger.info("Successfully loaded all configurations")
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            
    def save_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            if config_type == "global":
                path = os.path.join(self.config_dir, "global.json")
            else:
                path = os.path.join(self.config_dir, "modules", f"{config_type}.json")
                
            with open(path, "w") as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Successfully saved {config_type} configuration")
            return True
        except Exception as e:
            logger.error(f"Error saving {config_type} configuration: {e}")
            return False
            
    def get_global(self, key: str, default: Any = None) -> Any:
        """Get a global configuration value"""
        try:
            return self.global_config.get(key, default)
        except Exception as e:
            logger.error(f"Error getting global configuration value for {key}: {e}")
            return default
            
    def get_module_config(self, module: str) -> Dict[str, Any]:
        """Get configuration for a specific module"""
        try:
            return self.module_configs.get(module, {})
        except Exception as e:
            logger.error(f"Error getting module configuration for {module}: {e}")
            return {}
            
    def update_module_config(self, module: str, config: Dict[str, Any]) -> bool:
        """Update configuration for a specific module"""
        try:
            self.module_configs[module] = config
            return self.save_config(module, config)
        except Exception as e:
            logger.error(f"Error updating module configuration for {module}: {e}")
            return False
            
    def validate_access(self, module: str, access_code: str) -> bool:
        """Validate access code for a module"""
        try:
            module_config = self.get_module_config(module)
            if not module_config.get("requires_code", False):
                return True
                
            access_level = module_config.get("access_level", "basic")
            access_codes = self.global_config.get("global", {}).get("security", {}).get("access_codes", {})
            
            if access_level in access_codes:
                return access_codes[access_level]["code"] == access_code
            return False
        except Exception as e:
            logger.error(f"Error validating access for {module}: {e}")
            return False 