import customtkinter as ctk
from .gui import CommandManagerApp
import logging
from typing import Dict, Any, Optional, List
from core.plugins.plugin_interface import PluginInterface, PluginDependency
import tkinter as tk
import os
import json

class CommandManager(PluginInterface):
    """Command Manager plugin for FoSLauncher"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.app = None
        self.window = None
        self.base_dir = config.get('base_dir', "plugins/command_manager")
        self.logger = logging.getLogger("command_manager")
        self.logger.info("Command manager initialized")
        
        # Load commands directly
        self.commands_file = os.path.join(self.base_dir, config.get('settings', {}).get('commands_file', 'commands.json'))
        self.commands = self._load_commands()
        
        # Initialize built-in commands
        self._init_builtin_commands()

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def dependencies(self) -> List[PluginDependency]:
        return []

    def get_name(self) -> str:
        return "command_manager"

    def is_running(self) -> bool:
        return self._running

    def _init_builtin_commands(self):
        """Initialize built-in commands"""
        if "general" not in self.commands:
            self.commands["general"] = {}
            
        # Add help command if it doesn't exist
        if "help" not in self.commands["general"]:
            self.commands["general"]["help"] = {
                "response": self._get_help_message(),
                "enabled": True
            }
            self.logger.debug("Initialized help command")
            
    def _load_commands(self) -> Dict[str, Any]:
        """Load commands from file"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, "r") as f:
                    commands = json.load(f)
                    
                    # Check if commands are in flat format (no categories)
                    if any(cmd.startswith('!') for cmd in commands.keys()):
                        self.logger.debug("Converting flat command structure to categorized")
                        # Convert flat structure to categorized
                        categorized = {"general": {}}
                        for cmd, data in commands.items():
                            # Remove ! prefix for storage
                            cmd_name = cmd.lstrip('!')
                            categorized["general"][cmd_name] = data
                        commands = categorized
                    
                    # Ensure we have the general category
                    if "general" not in commands:
                        commands["general"] = {}
                        
                    self.logger.debug(f"Loaded {len(commands)} command categories")
                    self.logger.debug(f"Commands: {json.dumps(commands, indent=2)}")
                    return commands
                    
            self.logger.debug("No commands file found, using empty commands")
            return {"general": {}}
        except Exception as e:
            self.logger.error(f"Error loading commands: {str(e)}")
            return {"general": {}}
            
    def get_command_response(self, command: str) -> str:
        """Get response for a command"""
        try:
            # Remove ! prefix and convert to lowercase for case-insensitive matching
            command = command.lstrip('!').lower()
            self.logger.debug(f"Processing command: {command}")
            self.logger.debug(f"Available commands: {json.dumps(self.commands, indent=2)}")
            
            # Check if it's a built-in command
            if command == "help":
                return self._get_help_message()
            
            # Search through all categories for the command
            for category, commands in self.commands.items():
                if command in commands:
                    cmd_data = commands[command]
                    if cmd_data.get('enabled', True):
                        self.logger.debug(f"Found command '{command}' in category '{category}'")
                        return cmd_data.get('response', '')
                    self.logger.debug(f"Command '{command}' is disabled")
                    return f"Command '{command}' is disabled"
            
            self.logger.debug(f"Unknown command: {command}")
            return f"Unknown command: {command}. Type !help for available commands."
            
        except Exception as e:
            self.logger.error(f"Error getting command response: {str(e)}")
            return "An error occurred while processing the command."
            
    def _get_help_message(self) -> str:
        """Get formatted help message"""
        try:
            help_message = "Available commands:\n"
            
            # Get all commands from all categories
            for category, commands in self.commands.items():
                for cmd, data in commands.items():
                    if data.get('enabled', True):
                        help_message += f"!{cmd} - {data.get('response', 'No description')}\n"
            
            self.logger.debug("Generated help message")
            return help_message
        except Exception as e:
            self.logger.error(f"Error getting help message: {str(e)}")
            return "An error occurred while getting help information."
            
    async def _get_help_message(self) -> str:
        """Get formatted help message"""
        try:
            help_message = "Available commands:\n"
            
            # Get all commands from all categories
            for category, commands in self.commands.items():
                for cmd, data in commands.items():
                    if data.get('enabled', True):
                        help_message += f"!{cmd} - {data.get('response', 'No description')}\n"
            
            return help_message
        except Exception as e:
            self.logger.error(f"Error getting help message: {str(e)}")
            return "An error occurred while getting help information."
            
    def start(self) -> bool:
        """Start the Command Manager GUI"""
        try:
            if self._running:
                self.logger.warning("Command manager is already running")
                return False

            # Create new window
            self.window = ctk.CTkToplevel()
            self.window.title("Command Manager")
            self.window.geometry("800x600")
            self.window.configure(fg_color="#1a1a1a")
            
            # Make window unclosable by X button (must use Stop button)
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Create app in the window
            self.app = CommandManagerApp(self.window, self.base_dir)
            
            # Bring window to front
            self.window.lift()
            self.window.focus_force()
            
            self._running = True
            self.logger.info("Command manager GUI started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start command manager: {str(e)}")
            return False
            
    def stop(self) -> bool:
        """Stop the Command Manager GUI"""
        try:
            if not self._running:
                self.logger.warning("Command manager is not running")
                return False

            if self.window:
                try:
                    # Cleanup app first
                    if self.app:
                        self.app.cleanup()
                        self.app = None
                    
                    # Get all windows before we start destroying them
                    windows = [(w, w.tk.call('after', 'info')) for w in self.window.winfo_children() 
                             if isinstance(w, (ctk.CTkToplevel, tk.Toplevel))]
                    windows.append((self.window, self.window.tk.call('after', 'info')))
                    
                    # Cancel callbacks and destroy windows in reverse order
                    for window, after_ids in reversed(windows):
                        try:
                            # Cancel any pending after callbacks
                            for after_id in after_ids:
                                try:
                                    window.after_cancel(after_id)
                                except Exception:
                                    pass
                            # Destroy the window
                            window.destroy()
                        except Exception:
                            pass
                    
                    self.window = None
                    self._running = False
                    self.logger.info("Command manager stopped")
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"Non-critical error during window cleanup: {str(e)}")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop command manager: {str(e)}")
            return False
            
    def get_description(self) -> str:
        """Get the plugin description"""
        return "Manage custom commands and responses"
        
    def get_config_schema(self) -> Dict[str, Any]:
        """Get the plugin's configuration schema"""
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Enable the command manager plugin",
                    "default": True
                },
                "base_dir": {
                    "type": "string",
                    "description": "Base directory for plugin files",
                    "default": "plugins/command_manager"
                },
                "requires_code": {
                    "type": "boolean",
                    "description": "Whether the plugin requires a code to run",
                    "default": True
                },
                "access_level": {
                    "type": "string",
                    "enum": ["none", "basic", "advanced", "master"],
                    "description": "Required access level to use the plugin",
                    "default": "basic"
                },
                "settings": {
                    "type": "object",
                    "properties": {
                        "commands_file": {
                            "type": "string",
                            "description": "Path to the commands JSON file",
                            "default": "commands.json"
                        },
                        "auto_save": {
                            "type": "boolean",
                            "description": "Automatically save commands when modified",
                            "default": True
                        }
                    },
                    "required": ["commands_file"],
                    "additionalProperties": false
                }
            },
            "required": ["enabled", "base_dir", "settings"],
            "additionalProperties": false
        }
        
    def handle_event(self, event_name: str, data: Any) -> Optional[Any]:
        """Handle events from other plugins or the launcher"""
        pass

if __name__ == "__main__":
    # For standalone testing
    root = ctk.CTk()
    manager = CommandManager({"base_dir": "plugins/command_manager"})
    manager.start()
    root.mainloop() 