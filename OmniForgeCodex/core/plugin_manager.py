from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from pathlib import Path
import importlib
import importlib.util
import sys
import json
import logging
from datetime import datetime
import threading
from dataclasses import dataclass
from enum import Enum
import yaml
import jsonschema
import zipfile
import shutil
import tempfile
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PySide6.QtCore import QObject, Signal, Slot, QTimer
import time
import inspect
import pkgutil
import uuid
import queue
from concurrent.futures import ThreadPoolExecutor

class PluginType(Enum):
    CORE = "core"
    FEATURE = "feature"
    INTEGRATION = "integration"
    THEME = "theme"
    LANGUAGE = "language"
    ANALYTICS = "analytics"
    EXPORT = "export"
    IMPORT = "import"
    VALIDATION = "validation"
    CUSTOM = "custom"
    UI = "ui"
    DATA = "data"

class PluginStatus(Enum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UPDATING = "updating"
    ERROR = "error"

@dataclass
class PluginInfo:
    id: str
    name: str
    version: str
    type: PluginType
    status: PluginStatus
    description: str
    author: str
    dependencies: List[str]
    entry_point: str
    config: Dict[str, Any]
    install_date: datetime
    last_update: datetime
    error_message: Optional[str] = None

class PluginManager(QObject):
    plugin_installed = Signal(PluginInfo)  # plugin_info
    plugin_enabled = Signal(str)  # plugin_id
    plugin_disabled = Signal(str)  # plugin_id
    plugin_updated = Signal(PluginInfo)  # plugin_info
    plugin_error = Signal(str, str)  # plugin_id, error_message
    
    def __init__(self):
        super().__init__()
        self.plugins_dir = Path("plugins")
        self.plugin_config = self.plugins_dir / "config.json"
        self.plugin_schema = self.plugins_dir / "schema.json"
        self.plugin_cache = self.plugins_dir / "cache"
        self.plugin_backups = self.plugins_dir / "backups"
        self.config_dir = Path("config") / "plugins"
        
        # Plugin state
        self._plugins: Dict[str, PluginInfo] = {}
        self._loaded_plugins: Dict[str, Any] = {}
        self._plugin_observers: List[callable] = []
        self._plugin_lock = threading.RLock()
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._load_plugins()
        self._setup_file_watcher()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("plugin")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "plugins.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        for directory in [self.plugins_dir, self.plugin_cache, self.plugin_backups, self.config_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def _load_plugins(self):
        """Load all installed plugins"""
        if not self.plugin_config.exists():
            return
            
        with open(self.plugin_config, 'r') as f:
            plugin_data = json.load(f)
            
        for plugin_id, info in plugin_data.items():
            self._plugins[plugin_id] = PluginInfo(**info)
            
    def install_plugin(self, plugin_path: Union[str, Path]) -> Optional[PluginInfo]:
        """Install a new plugin"""
        try:
            plugin_path = Path(plugin_path)
            if not plugin_path.exists():
                raise FileNotFoundError(f"Plugin not found: {plugin_path}")
                
            # Load plugin metadata
            with open(plugin_path / "plugin.json", 'r') as f:
                plugin_data = json.load(f)
                
            # Create plugin info
            plugin_info = self._create_plugin_info(plugin_data)
            
            # Copy plugin files
            target_dir = self.plugins_dir / plugin_info.id
            target_dir.mkdir(exist_ok=True)
            
            # Copy plugin files
            for file in plugin_path.glob("**/*"):
                if file.is_file():
                    target_file = target_dir / file.relative_to(plugin_path)
                    target_file.parent.mkdir(exist_ok=True)
                    target_file.write_bytes(file.read_bytes())
                    
            # Save plugin configuration
            config_file = self.config_dir / f"{plugin_info.id}.json"
            with open(config_file, 'w') as f:
                json.dump(plugin_data, f, indent=2)
                
            # Add to plugins
            self._plugins[plugin_info.id] = plugin_info
            
            # Emit signal
            self.plugin_installed.emit(plugin_info)
            
            return plugin_info
            
        except Exception as e:
            self.logger.error(f"Error installing plugin: {e}")
            return None
            
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin"""
        try:
            if plugin_id not in self._plugins:
                raise ValueError(f"Plugin not found: {plugin_id}")
                
            # Disable plugin if enabled
            if self._plugins[plugin_id].status == PluginStatus.ENABLED:
                self.disable_plugin(plugin_id)
                
            # Remove plugin
            plugin_dir = self.plugins_dir / plugin_id
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
                
            # Remove configuration
            config_file = self.config_dir / f"{plugin_id}.json"
            if config_file.exists():
                config_file.unlink()
                
            # Update plugin info
            del self._plugins[plugin_id]
            
            # Save plugin config
            self._save_plugin_config()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error uninstalling plugin: {e}")
            return False
            
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a plugin"""
        try:
            if plugin_id not in self._plugins:
                raise ValueError(f"Plugin not found: {plugin_id}")
                
            plugin_info = self._plugins[plugin_id]
            
            # Check dependencies
            if not self._check_dependencies(plugin_info.dependencies):
                raise ValueError("Plugin dependencies not met")
                
            # Load plugin
            if plugin_id not in self._loaded_plugins:
                self._load_plugin(plugin_id)
                
            # Update plugin status
            plugin_info.status = PluginStatus.ENABLED
            plugin_info.last_update = datetime.now()
            
            # Save plugin config
            self._save_plugin_config()
            
            # Emit signal
            self.plugin_enabled.emit(plugin_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling plugin: {e}")
            return False
            
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        try:
            if plugin_id not in self._plugins:
                raise ValueError(f"Plugin not found: {plugin_id}")
                
            plugin_info = self._plugins[plugin_id]
            
            # Unload plugin
            if plugin_id in self._loaded_plugins:
                self._unload_plugin(plugin_id)
                
            # Update plugin status
            plugin_info.status = PluginStatus.DISABLED
            plugin_info.last_update = datetime.now()
            
            # Save plugin config
            self._save_plugin_config()
            
            # Emit signal
            self.plugin_disabled.emit(plugin_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling plugin: {e}")
            return False
            
    def update_plugin(self, plugin_id: str) -> bool:
        """Update a plugin"""
        try:
            if plugin_id not in self._plugins:
                raise ValueError(f"Plugin not found: {plugin_id}")
                
            plugin_info = self._plugins[plugin_id]
            plugin_info.status = PluginStatus.UPDATING
            
            # Save configuration
            self._save_plugin_config()
            
            # Disable plugin
            if plugin_info.status == PluginStatus.ENABLED:
                self.disable_plugin(plugin_id)
                
            # Update plugin files
            plugin_dir = self.plugins_dir / plugin_id
            if not plugin_dir.exists():
                raise FileNotFoundError(f"Plugin directory not found: {plugin_dir}")
                
            # Update plugin files
            # Implementation depends on update mechanism (e.g., git, package manager)
            
            # Reload plugin
            if plugin_info.status == PluginStatus.ENABLED:
                self.enable_plugin(plugin_id)
                
            # Update plugin info
            plugin_info.last_update = datetime.now()
            plugin_info.status = PluginStatus.ENABLED
            
            # Save configuration
            self._save_plugin_config()
            
            # Emit signal
            self.plugin_updated.emit(plugin_info)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating plugin: {e}")
            plugin_info.status = PluginStatus.ERROR
            plugin_info.error_message = str(e)
            self._save_plugin_config()
            self.plugin_error.emit(plugin_id, str(e))
            return False
            
    def _load_plugin(self, plugin_id: str):
        """Load a plugin module"""
        plugin_info = self._plugins[plugin_id]
        plugin_dir = self.plugins_dir / plugin_id
        
        # Add plugin directory to Python path
        if str(plugin_dir) not in sys.path:
            sys.path.append(str(plugin_dir))
            
        # Load plugin module
        spec = importlib.util.spec_from_file_location(
            plugin_info.name,
            plugin_dir / plugin_info.entry_point
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self._loaded_plugins[plugin_id] = module
        
    def _unload_plugin(self, plugin_id: str):
        """Unload a plugin module"""
        if plugin_id in self._loaded_plugins:
            del self._loaded_plugins[plugin_id]
            
    def _load_plugin_info(self, plugin_path: Path) -> PluginInfo:
        """Load plugin information from manifest"""
        manifest_path = plugin_path / "manifest.yaml"
        if not manifest_path.exists():
            raise FileNotFoundError("Plugin manifest not found")
            
        with open(manifest_path, 'r') as f:
            manifest = yaml.safe_load(f)
            
        return PluginInfo(
            id=manifest['id'],
            name=manifest['name'],
            version=manifest['version'],
            type=PluginType(manifest['type']),
            status=PluginStatus(manifest.get('status', 'installed')),
            description=manifest['description'],
            author=manifest['author'],
            dependencies=manifest.get('dependencies', []),
            entry_point=manifest['entry_point'],
            config=manifest.get('config', {}),
            install_date=datetime.fromisoformat(manifest.get('install_date', datetime.now().isoformat())),
            last_update=datetime.fromisoformat(manifest.get('last_update', datetime.now().isoformat())),
            error_message=manifest.get('error_message')
        )
        
    def _verify_plugin(self, plugin_info: PluginInfo) -> bool:
        """Verify plugin integrity and compatibility"""
        try:
            # Verify plugin schema
            if not self._verify_plugin_schema(plugin_info):
                return False
                
            # Verify plugin requirements
            if not self._verify_plugin_requirements(plugin_info):
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error verifying plugin: {e}")
            return False
            
    def _verify_plugin_schema(self, plugin_info: PluginInfo) -> bool:
        """Verify plugin against schema"""
        if not self.plugin_schema.exists():
            return True
            
        with open(self.plugin_schema, 'r') as f:
            schema = json.load(f)
            
        try:
            jsonschema.validate(plugin_info.__dict__, schema)
            return True
        except jsonschema.exceptions.ValidationError:
            return False
            
    def _verify_plugin_requirements(self, plugin_info: PluginInfo) -> bool:
        """Verify plugin requirements"""
        for package, version in plugin_info.config.items():
            try:
                importlib.import_module(package)
            except ImportError:
                return False
        return True
        
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all dependencies are met"""
        for dep in dependencies:
            if dep not in self._plugins or self._plugins[dep].status != PluginStatus.ENABLED:
                return False
        return True
        
    def _generate_plugin_id(self, plugin_info: PluginInfo) -> str:
        """Generate a unique plugin ID"""
        return hashlib.md5(f"{plugin_info.name}{plugin_info.version}".encode()).hexdigest()
        
    def _save_plugin_config(self):
        """Save plugin configuration"""
        plugin_data = {
            plugin_id: {
                "id": info.id,
                "name": info.name,
                "version": info.version,
                "type": info.type.value,
                "status": info.status.value,
                "description": info.description,
                "author": info.author,
                "dependencies": info.dependencies,
                "entry_point": info.entry_point,
                "config": info.config,
                "install_date": info.install_date.isoformat(),
                "last_update": info.last_update.isoformat(),
                "error_message": info.error_message
            }
            for plugin_id, info in self._plugins.items()
        }
        
        with open(self.plugin_config, 'w') as f:
            json.dump(plugin_data, f, indent=2)
            
    def _backup_plugin(self, plugin_id: str):
        """Create a backup of a plugin"""
        plugin_dir = self.plugins_dir / plugin_id
        if not plugin_dir.exists():
            return
            
        backup_path = self.plugin_backups / f"{plugin_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in plugin_dir.rglob("*"):
                if file.is_file():
                    zipf.write(file, file.relative_to(plugin_dir))
                    
    def _extract_plugin(self, plugin_path: Path) -> Path:
        """Extract a plugin zip file"""
        temp_dir = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(plugin_path, 'r') as zipf:
            zipf.extractall(temp_dir)
        return temp_dir
        
    def _download_plugin(self, plugin_id: str, version: str) -> Path:
        """Download a plugin version"""
        # Implement plugin download logic
        pass
        
    def _setup_file_watcher(self):
        """Setup file system watcher for plugins"""
        class PluginEventHandler(FileSystemEventHandler):
            def __init__(self, manager):
                self.manager = manager
                
            def on_modified(self, event):
                if event.src_path.endswith('manifest.yaml'):
                    self.manager._handle_plugin_change(event.src_path)
                    
        observer = Observer()
        observer.schedule(PluginEventHandler(self), str(self.plugins_dir), recursive=True)
        observer.start()
        
    def _handle_plugin_change(self, manifest_path: str):
        """Handle plugin manifest changes"""
        try:
            plugin_dir = Path(manifest_path).parent
            plugin_info = self._load_plugin_info(plugin_dir)
            plugin_id = self._generate_plugin_id(plugin_info)
            
            if plugin_id in self._plugins:
                self._plugins[plugin_id] = plugin_info
                self._save_plugin_config()
                
        except Exception as e:
            logging.error(f"Error handling plugin change: {e}")
            
    def _create_plugin_info(self, plugin_data: Dict[str, Any]) -> PluginInfo:
        """Create plugin info from data"""
        return PluginInfo(
            id=plugin_data["id"],
            name=plugin_data["name"],
            version=plugin_data["version"],
            type=PluginType(plugin_data["type"]),
            status=PluginStatus(plugin_data.get("status", "installed")),
            description=plugin_data["description"],
            author=plugin_data["author"],
            dependencies=plugin_data.get("dependencies", []),
            entry_point=plugin_data["entry_point"],
            config=plugin_data.get("config", {}),
            install_date=datetime.fromisoformat(plugin_data.get("install_date", datetime.now().isoformat())),
            last_update=datetime.fromisoformat(plugin_data.get("last_update", datetime.now().isoformat())),
            error_message=plugin_data.get("error_message")
        )
        
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin info"""
        return self._plugins.get(plugin_id)
        
    def get_plugins(self, plugin_type: Optional[PluginType] = None,
                   status: Optional[PluginStatus] = None) -> List[PluginInfo]:
        """Get filtered plugins"""
        plugins = list(self._plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.type == plugin_type]
        if status:
            plugins = [p for p in plugins if p.status == status]
            
        return plugins
        
    def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
        """Get plugin instance"""
        return self._loaded_plugins.get(plugin_id) 