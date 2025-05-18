import os
import json
import jsonschema
from typing import Dict, List, Optional, Any
from modules.logger import FoSLogger

class AccessManager:
    """Manages access control for FoSLauncher modules"""
    
    def __init__(self, logger: FoSLogger):
        self.logger = logger
        self.config_path = os.path.join(os.path.dirname(__file__), "access.json")
        self.schema_path = os.path.join(os.path.dirname(__file__), "schema.json")
        self.config = self.load_config()
        self.logger.info("Access manager initialized")
        self.logger.debug(f"Configuration loaded from {self.config_path}")
        
    def load_config(self) -> Dict[str, Any]:
        """Load access configuration"""
        try:
            self.logger.info("Loading access configuration")
            if not os.path.exists(self.config_path):
                self.logger.warning("Access configuration not found, creating default")
                return self.create_default_config()
                
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Validate against schema
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            jsonschema.validate(instance=config, schema=schema)
            
            self.logger.info("Access configuration loaded successfully")
            self.logger.debug(f"Configuration: {config}")
            return config
            
        except Exception as e:
            self.logger.error("Failed to load access configuration", exc_info=True)
            return self.create_default_config()
            
    def save_config(self) -> None:
        """Save access configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.info("Access configuration saved")
            self.logger.debug(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error("Error saving access configuration", exc_info=True)
            raise
            
    def create_default_config(self) -> Dict[str, Any]:
        """Create default access configuration"""
        try:
            default_config = {
                "version": "1.0.0",
                "users": {
                    "default": {
                        "modules": {
                            "chatsplitter": {
                                "unlocked": True,
                                "features": ["basic_export"]
                            },
                            "chatbot_plus": {
                                "unlocked": False,
                                "features": []
                            },
                            "command_manager": {
                                "unlocked": False,
                                "features": []
                            }
                        }
                    }
                },
                "access_codes": {
                    "master": {
                        "code": "FoSGamers2024",
                        "modules": ["all"]
                    }
                }
            }
            
            self.save_config()
            self.logger.info("Default access configuration created")
            self.logger.debug(f"Default configuration: {default_config}")
            return default_config
            
        except Exception as e:
            self.logger.error("Error creating default access configuration", exc_info=True)
            raise
            
    def validate_access_code(self, code: str) -> bool:
        """Validate an access code"""
        try:
            if not code:
                self.logger.warning("Empty access code provided")
                return False
                
            # Check if code matches master code
            if code == self.config.get("access_codes", {}).get("master", {}).get("code"):
                self.logger.info("Master code verified")
                return True
                
            # Check other access codes
            for access_code in self.config.get("access_codes", {}).values():
                if code == access_code.get("code"):
                    self.logger.info(f"Access code verified for modules: {access_code.get('modules', [])}")
                    return True
                    
            self.logger.warning(f"Invalid access code: {code}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating access code: {str(e)}")
            return False
            
    def check_module_access(self, user: str, module_id: str) -> bool:
        """Check if a user has access to a module"""
        try:
            # Get user's access configuration
            user_config = self.config.get("users", {}).get(user)
            if not user_config:
                self.logger.warning(f"User {user} not found in access config")
                return False
                
            # Check module access
            module_access = user_config.get("modules", {}).get(module_id)
            if not module_access:
                self.logger.debug(f"No access configuration found for module {module_id}")
                return False
                
            # Check if module is unlocked
            if not module_access.get("unlocked", False):
                self.logger.debug(f"Module {module_id} is locked for user {user}")
                return False
                
            # Check if user has all features
            features = module_access.get("features", [])
            if "all" in features:
                self.logger.debug(f"User {user} has full access to module {module_id}")
                return True
                
            self.logger.debug(f"User {user} has limited access to module {module_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking module access: {str(e)}")
            return False
            
    def check_feature_access(self, user: str, module: str, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        try:
            self.logger.debug(f"Checking feature access for {user} to {module}.{feature}")
            
            # Check if user exists
            if user not in self.config["users"]:
                self.logger.warning(f"User {user} not found")
                return False
                
            # Check if module exists for user
            if module not in self.config["users"][user]["modules"]:
                self.logger.warning(f"Module {module} not found for user {user}")
                return False
                
            # Check if feature is available
            if feature in self.config["users"][user]["modules"][module]["features"]:
                self.logger.info(f"Feature access for {user} to {module}.{feature}: True")
                return True
                
            self.logger.warning(f"No access found for {user} to {module}.{feature}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking feature access for {user} to {module}.{feature}", exc_info=True)
            return False
            
    def update_user_access(self, user: str, module_id: str, unlocked: bool, features: List[str]) -> None:
        """Update a user's access to a module"""
        try:
            # Ensure user exists in config
            if user not in self.config.get("users", {}):
                self.config["users"][user] = {"modules": {}}
                
            # Update module access
            self.config["users"][user]["modules"][module_id] = {
                "unlocked": unlocked,
                "features": features
            }
            
            # Save changes
            self.save_config()
            self.logger.info(f"Updated access for user {user} to module {module_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating user access: {str(e)}")
            
    def add_user(self, user: str) -> None:
        """Add a new user"""
        try:
            self.logger.debug(f"Adding new user {user}")
            
            if user not in self.config["users"]:
                self.config["users"][user] = {
                    "modules": {}
                }
                self.save_config()
                self.logger.info(f"Added new user {user}")
            else:
                self.logger.warning(f"User {user} already exists")
                
        except Exception as e:
            self.logger.error(f"Error adding user {user}", exc_info=True)
            raise
            
    def remove_user(self, user: str) -> None:
        """Remove a user"""
        try:
            self.logger.debug(f"Removing user {user}")
            
            if user in self.config["users"]:
                del self.config["users"][user]
                self.save_config()
                self.logger.info(f"Removed user {user}")
            else:
                self.logger.warning(f"User {user} not found")
                
        except Exception as e:
            self.logger.error(f"Error removing user {user}", exc_info=True)
            raise
            
    def get_master_code(self) -> Optional[str]:
        """Get the master access code"""
        try:
            return self.config.get("access_codes", {}).get("master", {}).get("code")
        except Exception as e:
            self.logger.error(f"Error getting master code: {str(e)}")
            return None 