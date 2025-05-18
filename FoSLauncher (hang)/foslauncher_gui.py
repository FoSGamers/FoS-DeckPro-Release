import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import json
import threading
import queue
import sys
import asyncio
import websockets
import webbrowser
import logging
import importlib
import pkgutil
from modules.logger import logger
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import importlib.util
from modules.gui.dialogs import AccessCodeDialog
from modules.youtube_login.youtube_client import YouTubeClient
from modules.access.access_manager import AccessManager
import traceback

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class FoSLauncher:
    """Main FoSLauncher application class"""
    
    def __init__(self):
        logger.info("Initializing FoSLauncher")
        self.root = None
        self.config = None
        self.access_manager = None
        self.modules = []
        self._master_code_verified = False
        self._initialized = False
        self.module_instances = {}
        self.module_buttons = {}  # Store button references
        self.module_data = {}  # Store module data
        
    def initialize(self) -> None:
        """Initialize the FoSLauncher application"""
        if self._initialized:
            logger.info("FoSLauncher already initialized")
            return

        try:
            self.root = ctk.CTk()
            self.root.title("FoSLauncher")
            self.root.geometry("800x600")
            
            self.load_config()
            self.create_widgets()
            
            self._initialized = True
            logger.info("FoSLauncher initialized successfully")
            
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}", exc_info=True)
            messagebox.showerror("Initialization Error", str(e))
            sys.exit(1)

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                    logger.info("Configuration loaded successfully")
            else:
                self.config = {}
                logger.warning("No configuration file found, using defaults")
            return self.config
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}", exc_info=True)
            return {}

    def create_widgets(self) -> None:
        """Create the main GUI widgets"""
        try:
            # Main frame
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Title label
            title_label = ctk.CTkLabel(
                main_frame,
                text="FoSLauncher",
                font=("Helvetica", 24, "bold")
            )
            title_label.pack(pady=20)
            
            # Status label
            self.status_label = ctk.CTkLabel(
                main_frame,
                text="Ready",
                font=("Helvetica", 12)
            )
            self.status_label.pack(pady=10)
            
            logger.info("GUI widgets created successfully")
            
        except Exception as e:
            logger.error(f"Error creating widgets: {str(e)}", exc_info=True)
            raise

    def discover_modules(self) -> None:
        """Discover available modules from manifest"""
        try:
            manifest_path = os.path.join("modules", "manifest.json")
            if not os.path.exists(manifest_path):
                logger.error(f"Manifest file not found at {manifest_path}")
                return

            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)

            # Handle both list and dictionary formats
            manifest = manifest_data if isinstance(manifest_data, list) else manifest_data.get("modules", [])
            
            if not isinstance(manifest, list):
                logger.error("Invalid manifest format - expected a list of modules")
                return

            # Process each module
            discovered_modules = []
            for module in manifest:
                if not isinstance(module, dict):
                    continue
                    
                module_id = module.get("ID")
                module_name = module.get("Name")
                module_entry = module.get("Entry")
                
                if not all([module_id, module_name, module_entry]):
                    logger.warning(f"Skipping module with missing required fields: {module}")
                    continue
                    
                # Verify module path exists
                if not os.path.exists(module_entry):
                    logger.warning(f"Module path not found: {module_entry}")
                    continue
                    
                discovered_modules.append(module)
                
            logger.info(f"Discovered {len(discovered_modules)} modules")
            self.modules = discovered_modules
            self.populate_module_list()
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": "module_discovery"})
            
    def initialize_base_modules(self) -> None:
        """Initialize modules that don't require access codes"""
        try:
            for module in self.modules:
                if not module.get("RequiresCode", False):
                    self.initialize_module(module)
        except Exception as e:
            logger.log_error_with_context(e, {"context": "base_module_initialization"})
            
    def initialize_module(self, module: Dict[str, Any]) -> None:
        """Initialize a specific module"""
        try:
            module_id = module["ID"]
            logger.info(f"Starting initialization for module: {module_id}")
            logger.debug(f"Module details: {module}")
            
            if module_id in self.module_instances:
                logger.debug(f"Module {module_id} already initialized")
                return
                
            # Get the module directory and add it to Python path
            module_dir = os.path.dirname(module["Entry"])
            logger.debug(f"Module directory: {module_dir}")
            
            if module_dir not in sys.path:
                sys.path.append(module_dir)
                logger.debug(f"Added {module_dir} to Python path")
            
            # Get the module's parent directory (modules/)
            parent_dir = os.path.dirname(module_dir)
            logger.debug(f"Parent directory: {parent_dir}")
            
            if parent_dir not in sys.path:
                sys.path.append(parent_dir)
                logger.debug(f"Added {parent_dir} to Python path")
            
            # Import the module using the full package path
            module_path = f"modules.{os.path.basename(module_dir)}.{os.path.basename(module['Entry'])[:-3]}"
            logger.debug(f"Attempting to import module: {module_path}")
            
            try:
                module_obj = importlib.import_module(module_path)
                logger.debug(f"Successfully imported module: {module_path}")
                logger.debug(f"Module attributes: {dir(module_obj)}")
            except ImportError as e:
                logger.error(f"Failed to import module {module_id}: {str(e)}")
                logger.error(f"Import error details: {type(e)}")
                logger.error(f"Import error traceback: {traceback.format_exc()}")
                messagebox.showerror("Error", f"Failed to initialize module {module['Name']}: {str(e)}")
                return
                
            # Initialize the module based on its type
            if module_id == "chatbot_plus":
                logger.debug("Initializing chatbot_plus module")
                if hasattr(module_obj, "initialize_components"):
                    logger.debug("Found initialize_components method")
                    if module_obj.initialize_components(self.root):
                        self.module_instances[module_id] = module_obj
                        logger.info(f"Module {module_id} initialized successfully")
                    else:
                        logger.error(f"Failed to initialize components for {module_id}")
                        messagebox.showerror("Error", f"Failed to initialize module {module['Name']}")
                else:
                    self.module_instances[module_id] = module_obj
                    logger.info(f"Module {module_id} loaded successfully")
                    
            elif module_id == "youtube_login":
                logger.debug("Initializing youtube_login module")
                if hasattr(module_obj, "initialize"):
                    logger.debug("Found initialize method")
                    module_obj.initialize(logger)
                    self.module_instances[module_id] = module_obj
                    logger.info(f"Module {module_id} initialized successfully")
                else:
                    self.module_instances[module_id] = module_obj
                    logger.info(f"Module {module_id} loaded successfully")
                    
            elif module_id == "command_manager":
                logger.debug("Initializing command_manager module")
                if hasattr(module_obj, "CommandManager"):
                    logger.debug("Found CommandManager class")
                    self.module_instances[module_id] = module_obj.CommandManager()
                    logger.info(f"Module {module_id} initialized successfully")
                else:
                    logger.error(f"Module {module_id} does not have CommandManager class")
                    messagebox.showerror("Error", f"Failed to initialize module {module['Name']}")
                    
            elif module_id == "chatsplitter":
                logger.debug("Initializing chatsplitter module")
                if hasattr(module_obj, "FoSGamersChatSplitter"):
                    logger.debug("Found FoSGamersChatSplitter class")
                    splitter_root = tk.Tk()
                    self.module_instances[module_id] = module_obj.FoSGamersChatSplitter(splitter_root)
                    logger.info(f"Module {module_id} initialized successfully")
                else:
                    logger.error(f"Module {module_id} does not have FoSGamersChatSplitter class")
                    messagebox.showerror("Error", f"Failed to initialize module {module['Name']}")
                    
            else:
                logger.error(f"Unknown module type: {module_id}")
                messagebox.showerror("Error", "Unknown module type")
            
        except Exception as e:
            logger.error(f"Error initializing module {module['ID']}: {str(e)}", exc_info=True)
            logger.error(f"Error details: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to initialize module {module['Name']}: {str(e)}")
            
    def create_module_button(self, module: Dict[str, Any], master: ctk.CTkFrame) -> ctk.CTkButton:
        """Create a button for a specific module"""
        module_id = module["ID"]
        has_access = self.check_module_access(module)
        
        # Store module data
        self.module_data[module_id] = module
        
        # Create button with direct reference to module
        button = ctk.CTkButton(
            master=master,
            text="Launch" if has_access else "Locked",
            state="normal" if has_access else "disabled",
            command=lambda m=module: self.launch_module(m)  # Pass module directly
        )
        
        # Store button reference
        self.module_buttons[module_id] = button
        return button
        
    def populate_module_list(self) -> None:
        """Populate the module list with discovered modules"""
        try:
            # Clear existing widgets and data
            for widget in self.module_frame.winfo_children():
                widget.destroy()
            self.module_buttons.clear()
            self.module_data.clear()
                
            # Configure grid
            self.module_frame.grid_columnconfigure(0, weight=1)
            self.module_frame.grid_columnconfigure(1, weight=1)
            self.module_frame.grid_columnconfigure(2, weight=1)
            
            # Create module cards
            for i, module in enumerate(self.modules):
                module_id = module["ID"]
                
                # Create card frame
                module_card = ctk.CTkFrame(self.module_frame)
                module_card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
                
                # Module name
                name_label = ctk.CTkLabel(
                    module_card,
                    text=module.get("Name", "Unknown Module"),
                    font=("Arial", 16, "bold")
                )
                name_label.pack(pady=5)
                
                # Module description
                desc_label = ctk.CTkLabel(
                    module_card,
                    text=module.get("Description", "No description available"),
                    wraplength=200
                )
                desc_label.pack(pady=5)
                
                # Check module access
                has_access = self.check_module_access(module)
                
                # Module status
                status = "Unlocked" if has_access else "Locked"
                status_label = ctk.CTkLabel(
                    module_card,
                    text=f"Status: {status}",
                    text_color="green" if has_access else "red"
                )
                status_label.pack(pady=5)
                
                # Create and add launch button
                launch_btn = self.create_module_button(module, module_card)
                launch_btn.pack(pady=10)
                
                # Access code indicator
                if module.get("RequiresCode", False) and not has_access:
                    access_label = ctk.CTkLabel(
                        module_card,
                        text="Access Code Required",
                        text_color="orange"
                    )
                    access_label.pack(pady=5)
                
            logger.debug("Module list populated successfully")
            
        except Exception as e:
            logger.error(f"Error populating module list: {str(e)}", exc_info=True)
            messagebox.showerror("Error", "Failed to populate module list")
            
    def check_module_access(self, module: Dict[str, Any]) -> bool:
        """Check if the current user has access to a module"""
        try:
            module_id = module["ID"]
            
            # Check if module requires an access code
            if not module.get("RequiresCode", False):
                logger.debug(f"Module {module_id} does not require access code")
                return True
                
            # Check if master code is verified
            if self._master_code_verified:
                logger.debug(f"Master code verified, granting access to {module_id}")
                return True
                
            # Check user's access
            has_access = self.access_manager.check_module_access("default", module_id)
            logger.debug(f"Access check for {module_id}: {has_access}")
            return has_access
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": f"access_check_{module['ID']}"})
            return False
            
    def launch_module(self, module: Dict[str, Any]) -> None:
        """Launch a specific module"""
        try:
            module_id = module["ID"]
            logger.info(f"Starting launch process for module: {module_id}")
            logger.debug(f"Module details: {module}")
            
            # Check access again before launching
            if not self.check_module_access(module):
                logger.warning(f"Access denied for module: {module_id}")
                messagebox.showerror("Access Denied", "You do not have access to this module")
                return
                
            # Initialize module if not already done
            if module_id not in self.module_instances:
                logger.debug(f"Module {module_id} not initialized, initializing now")
                self.initialize_module(module)
                
            # Launch the module based on its type
            if module_id in self.module_instances:
                module_obj = self.module_instances[module_id]
                logger.debug(f"Module instance: {module_obj}")
                logger.debug(f"Module attributes: {dir(module_obj)}")
                
                # Handle different module types
                if module_id == "chatbot_plus":
                    logger.debug("Launching chatbot_plus module")
                    if hasattr(module_obj, "main"):
                        logger.debug("Found main method")
                        module_obj.main()
                        logger.info(f"Module {module_id} started successfully")
                    else:
                        logger.error(f"Module {module_id} does not have a main method")
                        messagebox.showerror("Error", "Module cannot be launched")
                        
                elif module_id == "youtube_login":
                    logger.debug("Launching youtube_login module")
                    if hasattr(module_obj, "main"):
                        logger.debug("Found main method")
                        module_obj.main()
                        logger.info(f"Module {module_id} started successfully")
                    else:
                        logger.error(f"Module {module_id} does not have a main method")
                        messagebox.showerror("Error", "Module cannot be launched")
                        
                elif module_id == "command_manager":
                    logger.debug("Launching command_manager module")
                    if hasattr(module_obj, "start"):
                        logger.debug("Found start method")
                        root = module_obj.start()
                        if root:
                            logger.info(f"Module {module_id} started successfully")
                            root.mainloop()
                    else:
                        logger.error(f"Module {module_id} does not have a start method")
                        messagebox.showerror("Error", "Module cannot be launched")
                        
                elif module_id == "chatsplitter":
                    logger.debug("Launching chatsplitter module")
                    if hasattr(module_obj, "root"):
                        logger.debug("Found root window")
                        logger.info(f"Module {module_id} started successfully")
                        module_obj.root.mainloop()
                    else:
                        logger.error(f"Module {module_id} does not have a root window")
                        messagebox.showerror("Error", "Module cannot be launched")
                        
                else:
                    logger.error(f"Unknown module type: {module_id}")
                    messagebox.showerror("Error", "Unknown module type")
                    
            else:
                logger.error(f"Module {module_id} not initialized")
                messagebox.showerror("Error", "Module not initialized")
                
        except Exception as e:
            logger.error(f"Error launching module {module['ID']}: {str(e)}", exc_info=True)
            logger.error(f"Error details: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Failed to launch module: {str(e)}")
            
    def run(self) -> None:
        """Run the FoSLauncher application"""
        try:
            self.initialize()
            self.root.mainloop()
        except Exception as e:
            logger.error("Fatal error in FoSLauncher", exc_info=True)
            messagebox.showerror("Fatal Error", f"FoSLauncher encountered a fatal error: {str(e)}")
            sys.exit(1)
            
def main():
    """Main entry point for FoSLauncher"""
    try:
        app = FoSLauncher()
        app.run()
    except Exception as e:
        logger.error("Fatal error in main", exc_info=True)
        messagebox.showerror("Fatal Error", f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 