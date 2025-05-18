import os
import sys
import importlib
import logging
from typing import Dict, List, Type, Optional, Any
from .plugin_interface import PluginInterface, PluginDependency

class PluginManager:
    """Manages the loading and lifecycle of plugins with dependency resolution"""
    
    def __init__(self, config: Dict[str, Any], event_system: Any):
        self.logger = logging.getLogger("plugin_manager")
        self.config = config
        self.event_system = event_system
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_configs: Dict[str, dict] = {}
        self.plugin_versions: Dict[str, str] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
        
        # Add plugin directory to Python path
        if config.get("plugin_dir") not in sys.path:
            sys.path.append(config.get("plugin_dir"))
    
    def load_plugin(self, plugin_name: str, config: dict) -> bool:
        """Load a plugin by name with dependency resolution"""
        try:
            # Check if plugin is already loaded
            if plugin_name in self.plugins:
                self.logger.warning(f"Plugin {plugin_name} is already loaded")
                return True
            
            # Import the plugin module
            module_path = f"plugins.{plugin_name}"
            if module_path not in sys.modules:
                module = importlib.import_module(module_path)
            else:
                module = sys.modules[module_path]
            
            # Try different naming conventions for the plugin class
            plugin_class = None
            class_names = [
                plugin_name.title().replace("_", "") + "Plugin",  # YouTubeLoginPlugin
                plugin_name.title().replace("_", ""),  # YouTubeLogin
                plugin_name.replace("_", "").title(),  # Youtubelogin
                plugin_name.title(),  # Youtube_Login
            ]
            
            for class_name in class_names:
                try:
                    plugin_class = getattr(module, class_name)
                    break
                except AttributeError:
                    continue
            
            if plugin_class is None:
                raise AttributeError(f"Could not find plugin class in module {module_path}")
            
            # Initialize the plugin
            plugin = plugin_class(config)
            
            # Check dependencies
            if not self._check_dependencies(plugin):
                return False
            
            # Store the plugin
            self.plugins[plugin_name] = plugin
            self.plugin_configs[plugin_name] = config
            self.plugin_versions[plugin_name] = plugin.version
            
            # Update dependency graph
            self._update_dependency_graph(plugin)
            
            self.logger.info(f"Loaded plugin: {plugin_name} v{plugin.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {str(e)}")
            return False
    
    def _check_dependencies(self, plugin: PluginInterface) -> bool:
        """Check if all plugin dependencies are satisfied"""
        for dep in plugin.dependencies:
            if dep.name not in self.plugins:
                if dep.optional:
                    self.logger.warning(f"Optional dependency {dep.name} not found for {plugin.get_name()}")
                    continue
                self.logger.error(f"Required dependency {dep.name} not found for {plugin.get_name()}")
                return False
            
            # Check version compatibility
            installed_version = self.plugin_versions[dep.name]
            if not self._is_version_compatible(installed_version, dep.version):
                self.logger.error(f"Version mismatch for dependency {dep.name}: "
                                f"required {dep.version}, found {installed_version}")
                return False
        
        return True
    
    def _is_version_compatible(self, installed: str, required: str) -> bool:
        """Check if installed version is compatible with required version"""
        # Simple version comparison - can be enhanced with proper semver parsing
        return installed == required
    
    def _update_dependency_graph(self, plugin: PluginInterface) -> None:
        """Update the dependency graph"""
        self.dependency_graph[plugin.get_name()] = [
            dep.name for dep in plugin.dependencies
            if not dep.optional and dep.name in self.plugins
        ]
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin by name"""
        try:
            if plugin_name in self.plugins:
                # Check if other plugins depend on this one
                dependents = self._get_dependents(plugin_name)
                if dependents:
                    self.logger.error(f"Cannot unload {plugin_name}: "
                                    f"required by {', '.join(dependents)}")
                    return False
                
                # Stop the plugin
                self.plugins[plugin_name].stop()
                
                # Remove from storage
                del self.plugins[plugin_name]
                del self.plugin_configs[plugin_name]
                del self.plugin_versions[plugin_name]
                del self.dependency_graph[plugin_name]
                
                self.logger.info(f"Unloaded plugin: {plugin_name}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {str(e)}")
            return False
    
    def _get_dependents(self, plugin_name: str) -> List[str]:
        """Get list of plugins that depend on the given plugin"""
        return [
            name for name, deps in self.dependency_graph.items()
            if plugin_name in deps
        ]
    
    def start_plugin(self, plugin_name: str) -> bool:
        """Start a loaded plugin"""
        try:
            if plugin_name in self.plugins:
                # Ensure dependencies are started
                for dep in self.plugins[plugin_name].dependencies:
                    if not dep.optional and dep.name in self.plugins:
                        if not self.plugins[dep.name].is_running():
                            if not self.start_plugin(dep.name):
                                return False
                
                return self.plugins[plugin_name].start()
            return False
        except Exception as e:
            self.logger.error(f"Failed to start plugin {plugin_name}: {str(e)}")
            return False
    
    def stop_plugin(self, plugin_name: str) -> bool:
        """Stop a running plugin"""
        try:
            if plugin_name in self.plugins:
                # Stop dependents first
                for dependent in self._get_dependents(plugin_name):
                    if self.plugins[dependent].is_running():
                        if not self.stop_plugin(dependent):
                            return False
                
                return self.plugins[plugin_name].stop()
            return False
        except Exception as e:
            self.logger.error(f"Failed to stop plugin {plugin_name}: {str(e)}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a plugin instance by name"""
        return self.plugins.get(plugin_name)
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names"""
        return list(self.plugins.keys())
    
    def broadcast_event(self, event_name: str, data: Any) -> None:
        """Broadcast an event to all plugins"""
        for plugin in self.plugins.values():
            try:
                plugin.handle_event(event_name, data)
            except Exception as e:
                self.logger.error(f"Error handling event {event_name} in plugin {plugin.get_name()}: {str(e)}") 