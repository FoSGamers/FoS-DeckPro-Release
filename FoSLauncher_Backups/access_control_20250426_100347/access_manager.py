import os
import json
import jsonschema
from typing import Dict, List, Optional, Any
from modules.logger.logger import FoSLogger

class AccessManager:
    def __init__(self):
        self.logger = FoSLogger()
        self.access_logger = self.logger.get_logger("access")
        self.config_path = os.path.join(os.path.dirname(__file__), "access.json")
        self.schema_path = os.path.join(os.path.dirname(__file__), "schema.json")
        self.config = self.load_config()
        self.logger.log_info("access", "Access manager initialized")
        self.logger.log_debug("access", f"Configuration loaded from {self.config_path}")
        
    def load_config(self) -> Dict[str, Any]:
        """Load and validate access configuration"""
        try:
            if not os.path.exists(self.config_path):
                self.logger.log_warning("access", f"Access config not found at {self.config_path}, creating default")
                return self.create_default_config()
                
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Validate against schema
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            jsonschema.validate(instance=config, schema=schema)
            
            self.logger.log_info("access", "Access configuration loaded and validated")
            self.logger.log_debug("access", f"Configuration: {config}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.log_exception(self.access_logger, "Invalid JSON in access configuration", e)
            return self.create_default_config()
        except jsonschema.ValidationError as e:
            self.logger.log_exception(self.access_logger, "Access configuration validation failed", e)
            return self.create_default_config()
        except Exception as e:
            self.logger.log_exception(self.access_logger, "Error loading access configuration", e)
            return self.create_default_config()
            
    def save_config(self) -> None:
        """Save access configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            self.logger.log_info("access", "Access configuration saved")
            self.logger.log_debug("access", f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.log_exception(self.access_logger, "Error saving access configuration", e)
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
            self.logger.log_info("access", "Default access configuration created")
            self.logger.log_debug("access", f"Default configuration: {default_config}")
            return default_config
            
        except Exception as e:
            self.logger.log_exception(self.access_logger, "Error creating default access configuration", e)
            raise
            
    def validate_access_code(self, code: str) -> bool:
        """Validate an access code"""
        try:
            self.logger.log_debug("access", f"Validating access code: {code}")
            
            # Check master code first
            if code == self.config["access_codes"]["master"]["code"]:
                self.logger.log_info("access", "Master code validated successfully")
                return True
                
            # Check other access codes
            for access_code in self.config["access_codes"].values():
                if code == access_code["code"]:
                    self.logger.log_info("access", "Access code validated successfully")
                    return True
                    
            self.logger.log_warning("access", f"Invalid access code: {code}")
            return False
            
        except Exception as e:
            self.logger.log_exception(self.access_logger, f"Error validating access code {code}", e)
            return False
            
    def check_module_access(self, user: str, module: str) -> bool:
        """Check if user has access to a module"""
        try:
            self.logger.log_debug("access", f"Checking module access for {user} to {module}")
            
            # Check if user exists
            if user not in self.config["users"]:
                self.logger.log_warning("access", f"User {user} not found")
                return False
                
            # Check if module is unlocked for user
            if module in self.config["users"][user]["modules"]:
                access = self.config["users"][user]["modules"][module]["unlocked"]
                self.logger.log_info("access", f"Module access for {user} to {module}: {access}")
                return access
                
            self.logger.log_warning("access", f"No access found for {user} to {module}")
            return False
            
        except Exception as e:
            self.logger.log_exception(self.access_logger, f"Error checking module access for {user} to {module}", e)
            return False
            
    def check_feature_access(self, user: str, module: str, feature: str) -> bool:
        """Check if user has access to a specific feature"""
        try:
            self.logger.log_debug("access", f"Checking feature access for {user} to {module}.{feature}")
            
            # Check if user exists
            if user not in self.config["users"]:
                self.logger.log_warning("access", f"User {user} not found")
                return False
                
            # Check if module exists for user
            if module not in self.config["users"][user]["modules"]:
                self.logger.log_warning("access", f"Module {module} not found for user {user}")
                return False
                
            # Check if feature is available
            if feature in self.config["users"][user]["modules"][module]["features"]:
                self.logger.log_info("access", f"Feature access for {user} to {module}.{feature}: True")
                return True
                
            self.logger.log_warning("access", f"No access found for {user} to {module}.{feature}")
            return False
            
        except Exception as e:
            self.logger.log_exception(self.access_logger, f"Error checking feature access for {user} to {module}.{feature}", e)
            return False
            
    def update_user_access(self, user: str, module: str, unlocked: bool, features: List[str]) -> None:
        """Update user's access to a module"""
        try:
            self.logger.log_debug("access", f"Updating access for {user} to {module}")
            
            # Create user if doesn't exist
            if user not in self.config["users"]:
                self.config["users"][user] = {
                    "modules": {}
                }
                
            # Create module entry if doesn't exist
            if module not in self.config["users"][user]["modules"]:
                self.config["users"][user]["modules"][module] = {
                    "unlocked": False,
                    "features": []
                }
                
            # Update access settings
            self.config["users"][user]["modules"][module]["unlocked"] = unlocked
            self.config["users"][user]["modules"][module]["features"] = features
            
            self.save_config()
            self.logger.log_info("access", f"Updated access for {user} to {module}")
            self.logger.log_debug("access", f"New access settings: unlocked={unlocked}, features={features}")
            
        except Exception as e:
            self.logger.log_exception(self.access_logger, f"Error updating access for {user} to {module}", e)
            raise
            
    def add_user(self, user: str) -> None:
        """Add a new user"""
        try:
            self.logger.log_debug("access", f"Adding new user {user}")
            
            if user not in self.config["users"]:
                self.config["users"][user] = {
                    "modules": {}
                }
                self.save_config()
                self.logger.log_info("access", f"Added new user {user}")
            else:
                self.logger.log_warning("access", f"User {user} already exists")
                
        except Exception as e:
            self.logger.log_exception(self.access_logger, f"Error adding user {user}", e)
            raise
            
    def remove_user(self, user: str) -> None:
        """Remove a user"""
        try:
            self.logger.log_debug("access", f"Removing user {user}")
            
            if user in self.config["users"]:
                del self.config["users"][user]
                self.save_config()
                self.logger.log_info("access", f"Removed user {user}")
            else:
                self.logger.log_warning("access", f"User {user} not found")
                
        except Exception as e:
            self.logger.log_exception(self.access_logger, f"Error removing user {user}", e)
            raise 