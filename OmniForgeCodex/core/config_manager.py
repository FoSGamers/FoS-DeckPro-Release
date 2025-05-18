from pathlib import Path
import json
import shutil
from typing import Dict, Any, Optional, List, Union
import logging
from datetime import datetime
import os
import yaml
import jsonschema
from cryptography.fernet import Fernet
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import copy

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.default_config = self.config_dir / "default.json"
        self.user_config = self.config_dir / "user.json"
        self.env_config = self.config_dir / f"env_{os.getenv('ENV', 'development')}.json"
        self.secure_config = self.config_dir / "secure.json"
        self.schema_dir = self.config_dir / "schemas"
        self.backup_dir = self.config_dir / "backups"
        self.migration_dir = self.config_dir / "migrations"
        
        # Configuration state
        self._config: Dict[str, Any] = {}
        self._config_lock = threading.RLock()
        self._config_history: List[Dict[str, Any]] = []
        self._config_observers: List[callable] = []
        
        # Security
        self._encryption_key = None
        
        # Setup - Reordered to create directories first
        self.setup_directories()  # Moved before _setup_encryption
        self._setup_encryption()
        self.load_config()
        self._setup_file_watcher()
        
    def setup_directories(self):
        """Setup required directories"""
        for directory in [self.config_dir, self.schema_dir, self.backup_dir, self.migration_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _setup_encryption(self):
        """Setup encryption for secure configuration"""
        key_file = self.config_dir / ".encryption_key"
        if not key_file.exists():
            self._encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self._encryption_key)
        else:
            with open(key_file, 'rb') as f:
                self._encryption_key = f.read()
                
    def load_config(self, validate: bool = True) -> Dict[str, Any]:
        """Load configuration with validation and inheritance"""
        with self._config_lock:
            # Load default configuration
            config = self._load_default_config()
            
            # Load environment-specific configuration
            if self.env_config.exists():
                env_config = self._load_json_file(self.env_config)
                config = self._merge_configs(config, env_config)
                
            # Load user configuration
            if self.user_config.exists():
                user_config = self._load_json_file(self.user_config)
                config = self._merge_configs(config, user_config)
                
            # Load secure configuration
            if self.secure_config.exists():
                secure_config = self._load_secure_config()
                config = self._merge_configs(config, secure_config)
                
            if validate:
                self._validate_config(config)
                
            # Store configuration history
            self._config_history.append({
                'timestamp': datetime.now().isoformat(),
                'config': copy.deepcopy(config)
            })
            
            self._config = config
            self._notify_observers('config_loaded', config)
            return config
            
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        if not self.default_config.exists():
            return self._create_default_config()
        return self._load_json_file(self.default_config)
        
    def _load_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Load JSON file with error handling"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
            return {}
            
    def _load_secure_config(self) -> Dict[str, Any]:
        """Load encrypted configuration"""
        try:
            with open(self.secure_config, 'rb') as f:
                encrypted_data = f.read()
            fernet = Fernet(self._encryption_key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            logging.error(f"Error loading secure config: {e}")
            return {}
            
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configurations with proper inheritance"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
        
    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration against schema"""
        schema_path = self.schema_dir / "config.schema.json"
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            try:
                jsonschema.validate(instance=config, schema=schema)
            except jsonschema.exceptions.ValidationError as e:
                logging.error(f"Configuration validation error: {e}")
                raise
                
    def save_config(self, config: Dict[str, Any], secure: bool = False):
        """Save configuration with backup"""
        with self._config_lock:
            # Create backup
            if self.user_config.exists():
                backup_path = self.backup_dir / f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(self.user_config, backup_path)
                
            # Save configuration
            if secure:
                self._save_secure_config(config)
            else:
                with open(self.user_config, 'w') as f:
                    json.dump(config, f, indent=2)
                    
            # Update configuration
            self._config = config
            self._config_history.append({
                'timestamp': datetime.now().isoformat(),
                'config': copy.deepcopy(config)
            })
            
            self._notify_observers('config_saved', config)
            
    def _save_secure_config(self, config: Dict[str, Any]):
        """Save encrypted configuration"""
        try:
            fernet = Fernet(self._encryption_key)
            encrypted_data = fernet.encrypt(json.dumps(config).encode())
            with open(self.secure_config, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            logging.error(f"Error saving secure config: {e}")
            raise
            
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """Get configuration value"""
        with self._config_lock:
            if key is None:
                return self._config
            return self._config.get(key, default)
            
    def set_config(self, key: str, value: Any, secure: bool = False):
        """Set configuration value"""
        with self._config_lock:
            config = self._config.copy()
            config[key] = value
            self.save_config(config, secure)
            
    def _setup_file_watcher(self):
        """Setup file watcher for configuration changes"""
        class ConfigFileHandler(FileSystemEventHandler):
            def __init__(self, config_manager):
                self.config_manager = config_manager
                
            def on_modified(self, event):
                if event.src_path.endswith('.json'):
                    self.config_manager.load_config()
                    
        observer = Observer()
        observer.schedule(ConfigFileHandler(self), str(self.config_dir), recursive=False)
        observer.start()
        
    def add_observer(self, callback: callable):
        """Add configuration change observer"""
        self._config_observers.append(callback)
        
    def remove_observer(self, callback: callable):
        """Remove configuration change observer"""
        if callback in self._config_observers:
            self._config_observers.remove(callback)
            
    def _notify_observers(self, event: str, data: Any):
        """Notify observers of configuration changes"""
        for observer in self._config_observers:
            try:
                observer(event, data)
            except Exception as e:
                logging.error(f"Error in config observer: {e}")
                
    def get_config_history(self) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        return self._config_history
        
    def restore_config(self, timestamp: str):
        """Restore configuration from history"""
        for history_entry in reversed(self._config_history):
            if history_entry['timestamp'] == timestamp:
                self.save_config(history_entry['config'])
                return
        raise ValueError(f"No configuration found for timestamp {timestamp}")
        
    def export_config(self, format: str = 'json') -> str:
        """Export configuration in specified format"""
        with self._config_lock:
            if format == 'json':
                return json.dumps(self._config, indent=2)
            elif format == 'yaml':
                return yaml.dump(self._config)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
    def import_config(self, config_data: str, format: str = 'json'):
        """Import configuration from specified format"""
        with self._config_lock:
            if format == 'json':
                config = json.loads(config_data)
            elif format == 'yaml':
                config = yaml.safe_load(config_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            self._validate_config(config)
            self.save_config(config)
            
    def cleanup(self):
        """Clean up resources"""
        # Implement cleanup logic
        pass 

    def _create_default_config(self) -> Dict[str, Any]:
        """Create and save default configuration"""
        default_config = {
            "application": {
                "name": "OmniForgeCodex",
                "version": "1.0.0",
                "environment": os.getenv('ENV', 'development')
            },
            "ui": {
                "theme": "light",
                "language": "en",
                "window": {
                    "width": 1024,
                    "height": 768,
                    "maximized": False
                }
            },
            "logging": {
                "level": "INFO",
                "file_rotation": {
                    "max_size": 10485760,  # 10MB
                    "backup_count": 5
                }
            },
            "security": {
                "encryption_enabled": True,
                "session_timeout": 3600  # 1 hour
            },
            "paths": {
                "data": "data",
                "logs": "logs",
                "temp": "temp"
            }
        }
        
        # Save default configuration
        with open(self.default_config, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config 

    def load_default(self):
        """Load default configuration"""
        with self._config_lock:
            config = self._load_default_config()
            self._config = config
            self._notify_observers('config_loaded', config)
            return config 