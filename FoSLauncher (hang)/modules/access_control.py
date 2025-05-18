import os
import json
import logging

logger = logging.getLogger("FoSLauncher")

class AccessControl:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.access_path = os.path.join(self.base_dir, "modules", "access.json")
        self.access_config = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load access configuration from access.json"""
        try:
            if os.path.exists(self.access_path):
                with open(self.access_path, "r") as f:
                    self.access_config = json.load(f)
                logger.info("Successfully loaded access configuration")
            else:
                logger.warning(f"Access configuration file not found at {self.access_path}")
                self.access_config = {
                    "users": {
                        "test_user": {
                            "permission_level": "admin",
                            "modules": {
                                "chatbot_plus": True,
                                "chatsplitter": True
                            }
                        }
                    }
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading access configuration: {e}")
            self.access_config = {}
            
    def save_config(self) -> None:
        """Save access configuration to access.json"""
        try:
            with open(self.access_path, "w") as f:
                json.dump(self.access_config, f, indent=4)
            logger.info("Successfully saved access configuration")
        except Exception as e:
            logger.error(f"Error saving access configuration: {e}")
            
    def has_permission(self, user: str, module: str) -> bool:
        """Check if a user has permission to access a module"""
        try:
            user_config = self.access_config.get("users", {}).get(user, {})
            return user_config.get("modules", {}).get(module, False)
        except Exception as e:
            logger.error(f"Error checking permissions for user {user}: {e}")
            return False
            
    def get_user_level(self, user: str) -> str:
        """Get the permission level of a user"""
        try:
            return self.access_config.get("users", {}).get(user, {}).get("permission_level", "basic")
        except Exception as e:
            logger.error(f"Error getting permission level for user {user}: {e}")
            return "basic"
            
    def can_access_module(self, user: str, module: str) -> bool:
        """Check if a user can access a specific module"""
        try:
            # Admin users can access all modules
            if self.get_user_level(user) == "admin":
                return True
            return self.has_permission(user, module)
        except Exception as e:
            logger.error(f"Error checking module access for user {user}: {e}")
            return False
            
    def add_user(self, user: str, permission_level: str = "basic", modules: dict = None) -> bool:
        """Add a new user with specified permissions"""
        try:
            if modules is None:
                modules = {}
            self.access_config.setdefault("users", {})[user] = {
                "permission_level": permission_level,
                "modules": modules
            }
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error adding user {user}: {e}")
            return False
            
    def remove_user(self, user: str) -> bool:
        """Remove a user from access control"""
        try:
            if user in self.access_config.get("users", {}):
                del self.access_config["users"][user]
                self.save_config()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing user {user}: {e}")
            return False
            
    def update_user_permissions(self, user: str, module: str, has_access: bool) -> bool:
        """Update a user's permissions for a specific module"""
        try:
            user_config = self.access_config.setdefault("users", {}).setdefault(user, {})
            user_config.setdefault("modules", {})[module] = has_access
            self.save_config()
            return True
        except Exception as e:
            logger.error(f"Error updating permissions for user {user}: {e}")
            return False 