import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
import json
import os
import logging
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger("FoSLauncher")

class CommandManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.commands = {}
        self.commands_file = os.path.join("plugins", "command_manager", "commands.json")
        self.load_commands()

    def load_commands(self) -> None:
        """Load commands from commands.json file"""
        try:
            logger.debug(f"Looking for commands file at: {self.commands_file}")
            logger.debug(f"Commands file exists: {os.path.exists(self.commands_file)}")
            
            if not os.path.exists(self.commands_file):
                logger.warning(f"Commands file not found at {self.commands_file}")
                logger.info("Initializing with default commands")
                self._init_default_commands()
                return
                
            logger.debug("Reading commands file")
            with open(self.commands_file, 'r') as f:
                data = json.load(f)
                logger.debug(f"Raw commands data: {data}")
                
            # Initialize with default structure
            self.commands = {
                'youtube': {},
                'chat': {},
                'commands': {},
                'help': {},
                'general': {}
            }
                
            # Handle the current format where commands are in a dictionary with categories
            if isinstance(data, dict):
                logger.debug("Processing commands dictionary")
                for category, commands in data.items():
                    if not isinstance(commands, dict):
                        continue
                    for name, cmd_info in commands.items():
                        if isinstance(cmd_info, dict):
                            self.commands[category][name] = {
                                'description': cmd_info.get('description', ''),
                                'usage': cmd_info.get('usage', f"!{name}"),
                                'permission_level': cmd_info.get('permission_level', 'basic'),
                                'enabled': cmd_info.get('enabled', True),
                                'response': cmd_info.get('response', '')  # Add response field
                            }
            else:
                logger.warning("Invalid commands format, initializing with default commands")
                self._init_default_commands()
                
            logger.info(f"Commands loaded successfully. Total categories: {len(self.commands)}")
            
        except Exception as e:
            logger.error(f"Error loading commands: {str(e)}")
            self._init_default_commands()

    def _init_default_commands(self) -> None:
        """Initialize with default commands"""
        self.commands = {
            'general': {
                'help': {
                    'description': 'Show available commands',
                    'usage': '!help',
                    'permission_level': 'basic',
                    'enabled': True,
                    'response': 'Available commands: !help, !commands'
                },
                'commands': {
                    'description': 'List all commands',
                    'usage': '!commands',
                    'permission_level': 'basic',
                    'enabled': True,
                    'response': 'Available commands: !help, !commands'
                }
            },
            'youtube': {},
            'chat': {},
            'commands': {},
            'help': {}
        }
        
        # Save the default commands
        try:
            os.makedirs(os.path.dirname(self.commands_file), exist_ok=True)
            with open(self.commands_file, 'w') as f:
                json.dump(self.commands, f, indent=4)
            logger.info("Default commands saved to file")
        except Exception as e:
            logger.error(f"Error saving default commands: {str(e)}")

    def _convert_old_format(self, data: dict) -> None:
        """Convert old commands format to new format"""
        logger.debug("Converting old command format to new format")
        self.commands = {
            'youtube': {},
            'help': {},
            'general': {}
        }
        
        for cmd in data.get('commands', []):
            if not isinstance(cmd, dict):
                continue
                
            command = cmd.get('command', '')
            if not command:
                continue
                
            # Strip the ! from the command
            command = command.lstrip('!')
            
            # Determine category from command
            if command.startswith('youtube '):
                category = 'youtube'
                name = command[8:]  # Remove 'youtube ' prefix
            elif command == 'help':
                category = 'help'
                name = command
            else:
                category = 'general'
                name = command
                
            self.commands[category][name] = {
                'description': cmd.get('response', ''),
                'usage': f"!{command}",
                'permission_level': 'premium' if cmd.get('requires_premium', False) else 'basic',
                'enabled': True
            }
            
        logger.debug("Command format conversion complete")

    def save_commands(self) -> None:
        """Save commands to JSON file"""
        try:
            with open(self.commands_file, 'w') as f:
                json.dump(self.commands, f, indent=4)
            logger.info("Commands saved successfully")
        except Exception as e:
            logger.error(f"Error saving commands: {e}")

    def import_from_csv(self, csv_path: str) -> bool:
        """Import commands from CSV file"""
        try:
            if not os.path.exists(csv_path):
                logger.error(f"CSV file not found: {csv_path}")
                return False
                
            df = pd.read_csv(csv_path)
            
            # Validate required columns
            required_columns = ['category', 'name']
            if not all(col in df.columns for col in required_columns):
                logger.error(f"CSV missing required columns: {required_columns}")
                return False
                
            for _, row in df.iterrows():
                category = str(row.get('category', 'general')).strip()
                name = str(row.get('name', '')).strip()
                
                if not name:
                    logger.warning("Row missing name, skipping")
                    continue
                    
                if category not in self.commands:
                    self.commands[category] = {}
                    
                self.commands[category][name] = {
                    'description': str(row.get('description', '')).strip(),
                    'usage': str(row.get('usage', '')).strip(),
                    'permission_level': str(row.get('permission_level', 'basic')).strip(),
                    'enabled': bool(row.get('enabled', True))
                }
            
            self.save_commands()
            logger.info(f"Successfully imported commands from {csv_path}")
            return True
        except pd.errors.EmptyDataError:
            logger.error("CSV file is empty")
            return False
        except pd.errors.ParserError:
            logger.error("Invalid CSV format")
            return False
        except Exception as e:
            logger.error(f"Error importing commands from CSV: {e}")
            return False

    def export_to_csv(self, csv_path: str) -> bool:
        """Export commands to CSV file"""
        try:
            data = []
            for category, commands in self.commands.items():
                for name, details in commands.items():
                    data.append({
                        'category': category,
                        'name': name,
                        'description': details.get('description', ''),
                        'usage': details.get('usage', ''),
                        'permission_level': details.get('permission_level', 'basic'),
                        'enabled': details.get('enabled', True)
                    })
            
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            logger.info(f"Successfully exported commands to {csv_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting commands to CSV: {e}")
            return False

    def add_command(self, category: str, name: str, description: str, 
                   usage: str, permission_level: str = 'basic', enabled: bool = True) -> bool:
        """Add a new command"""
        try:
            if category not in self.commands:
                self.commands[category] = {}
            
            self.commands[category][name] = {
                'description': description,
                'usage': usage,
                'permission_level': permission_level,
                'enabled': enabled
            }
            
            self.save_commands()
            logger.info(f"Added command: {category}.{name}")
            return True
        except Exception as e:
            logger.error(f"Error adding command: {e}")
            return False

    def remove_command(self, category: str, name: str) -> bool:
        """Remove a command"""
        try:
            if category in self.commands and name in self.commands[category]:
                del self.commands[category][name]
                if not self.commands[category]:
                    del self.commands[category]
                self.save_commands()
                logger.info(f"Removed command: {category}.{name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing command: {e}")
            return False

    def get_command(self, category: str, name: str) -> dict:
        """Get a specific command"""
        return self.commands.get(category, {}).get(name, {})

    def get_category_commands(self, category: str) -> dict:
        """Get commands in a specific category"""
        return self.commands.get(category, {})

    def get_all_commands(self) -> dict:
        """Get all commands"""
        return self.commands

    def is_command_enabled(self, category: str, name: str) -> bool:
        """Check if a command is enabled"""
        return self.commands.get(category, {}).get(name, {}).get('enabled', True)

    def get_command_permission_level(self, category: str, name: str) -> str:
        """Get the permission level required for a command"""
        return self.commands.get(category, {}).get(name, {}).get('permission_level', 'basic')

    def get_command_response(self, command: str) -> str:
        """Get the response for a command"""
        try:
            # Remove the ! prefix if present
            command = command.lstrip('!')
            
            # Check all categories for the command
            for category, commands in self.commands.items():
                if command in commands:
                    cmd_info = commands[command]
                    
                    # Check if command is enabled
                    if not cmd_info.get('enabled', True):
                        return f"Command '{command}' is currently disabled."
                    
                    # Return the command's response
                    return cmd_info.get('response', '')
            
            return f"Unknown command: {command}. Type !help for available commands."
            
        except Exception as e:
            logger.error(f"Error getting command response: {str(e)}")
            return "An error occurred while processing the command."

def main():
    root = ctk.CTk()
    root.title("FoSLauncher Command Manager")
    root.geometry("800x600")
    
    # Load configuration
    try:
        # Try to load from main config first
        main_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")
        module_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        
        config = {}
        
        # Load main config
        if os.path.exists(main_config_path):
            with open(main_config_path, "r") as f:
                config.update(json.load(f))
        
        # Load module config
        if os.path.exists(module_config_path):
            with open(module_config_path, "r") as f:
                config.update(json.load(f))
                
        manager = CommandManager(config.get("base_dir", os.path.dirname(__file__)))
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        manager = CommandManager(os.path.dirname(__file__))
        
    root.mainloop()
    
if __name__ == "__main__":
    main() 