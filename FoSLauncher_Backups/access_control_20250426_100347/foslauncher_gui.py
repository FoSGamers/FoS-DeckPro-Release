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
from modules.logger.logger import FoSLogger
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import importlib.util
from modules.gui.dialogs import AccessCodeDialog
from modules.youtube_login.youtube_client import YouTubeClient
from modules.access.access_manager import AccessManager

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = FoSLogger()

class FoSLauncher:
    """Main FoSLauncher application class"""
    
    def __init__(self):
        self.root = None
        self.config = None
        self.access_manager = AccessManager()
        self.modules = []
        self._master_code_verified = False
        logger.log_module_start("foslauncher", {})
        
    def initialize(self) -> None:
        """Initialize the FoSLauncher application"""
        try:
            # Create main window
            self.root = ctk.CTk()
            self.root.title("FoSLauncher")
            self.root.geometry("800x600")
            
            # Load configurations
            self.config = self.load_config()
            
            # Create GUI
            self.create_widgets()
            self.discover_modules()
            
            logger.info("FoSLauncher initialized successfully")
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": "foslauncher_initialization"})
            raise
            
    def load_config(self) -> Dict[str, Any]:
        """Load main configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            logger.warning("No config file found, using defaults")
            return {}
        except Exception as e:
            logger.log_error_with_context(e, {"context": "config_loading"})
            return {}
            
    def create_widgets(self) -> None:
        """Create the main GUI widgets"""
        try:
            # Create main container
            self.main_container = ctk.CTkFrame(self.root)
            self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create title
            title_label = ctk.CTkLabel(
                self.main_container,
                text="FoSLauncher",
                font=("Arial", 24, "bold")
            )
            title_label.pack(pady=10)
            
            # Create module grid
            self.module_frame = ctk.CTkFrame(self.main_container)
            self.module_frame.pack(fill="both", expand=True)
            
            logger.debug("GUI widgets created successfully")
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": "widget_creation"})
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
            
    def populate_module_list(self) -> None:
        """Populate the module list with discovered modules"""
        try:
            # Clear existing widgets
            for widget in self.module_frame.winfo_children():
                widget.destroy()
                
            # Configure grid
            self.module_frame.grid_columnconfigure(0, weight=1)
            self.module_frame.grid_columnconfigure(1, weight=1)
            self.module_frame.grid_columnconfigure(2, weight=1)
            
            for i, module in enumerate(self.modules):
                if not module.get("enabled", True):
                    continue
                    
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
                
                # Module status
                status = "Enabled" if module.get("enabled", True) else "Disabled"
                status_label = ctk.CTkLabel(
                    module_card,
                    text=f"Status: {status}",
                    text_color="green" if module.get("enabled", True) else "red"
                )
                status_label.pack(pady=5)
                
                # Launch button
                launch_btn = ctk.CTkButton(
                    module_card,
                    text="Launch",
                    command=lambda m=module: self.launch_module(m)
                )
                launch_btn.pack(pady=10)
                
                # Access code indicator
                if module.get("RequiresCode", False):
                    access_label = ctk.CTkLabel(
                        module_card,
                        text="🔒 Requires Access Code",
                        font=("Arial", 10)
                    )
                    access_label.pack(pady=5)
                
            logger.debug("Modules populated successfully")
                
        except Exception as e:
            logger.log_error_with_context(e, {"context": "module_list_population"})
            
    def verify_access_code(self) -> bool:
        """Verify access code for modules"""
        try:
            # If master code was already verified, grant access
            if self._master_code_verified:
                logger.debug("Master code already verified, granting access")
                return True
                
            dialog = AccessCodeDialog(self.root, self.config)
            code = dialog.get_input()
            
            if not code:
                logger.debug("No access code entered")
                return False
                
            # Check if it's the master code
            if code == "FoSGamers2024":
                self._master_code_verified = True
                logger.info("Master code verified")
                return True
                
            # Check if it's a valid access code
            if self.access_manager.validate_access_code(code):
                logger.info("Access code verified")
                return True
                
            logger.warning("Invalid access code")
            return False
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": "access_code_verification"})
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to verify access code: {str(e)}"))
            return False
            
    def check_module_access(self, module: Dict[str, Any]) -> bool:
        """Check if user has access to a module"""
        try:
            module_id = module.get("ID", "")
            
            # If module doesn't require code, grant access
            if not module.get("RequiresCode", False):
                logger.debug(f"Module {module_id} doesn't require access code")
                return True
                
            # If master code was verified, grant access
            if self._master_code_verified:
                logger.debug("Master code verified, granting access")
                return True
                
            # Check module-specific access
            access = self.access_manager.check_module_access("default", module_id)
            logger.debug(f"Module access check for {module_id}: {access}")
            return access
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": "module_access_check", "module": module.get("ID", "unknown")})
            return False
            
    def launch_module(self, module: Dict[str, Any]) -> None:
        """Launch a module with proper access level"""
        try:
            module_name = module.get("Name", "Unknown")
            module_id = module.get("ID", "")
            logger.log_module_event("foslauncher", "launching_module", {"module": module_name})
            
            # Check module access
            if not self.check_module_access(module):
                if not self.verify_access_code():
                    logger.warning(f"Access denied for module {module_name}")
                    self.root.after(0, lambda: messagebox.showerror("Access Denied", 
                        f"Access denied for {module_name}. Please enter a valid access code."))
                    return
                    
            # Get module path
            module_abs_path = os.path.join(os.path.dirname(__file__), module.get("Entry", ""))
            if not os.path.isfile(module_abs_path):
                logger.error(f"Module path not found: {module_abs_path}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Module {module_name} not found at {module_abs_path}"))
                return
                
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"modules.{module_id}.main",
                module_abs_path
            )
            if spec is None:
                logger.error(f"Could not load module spec for {module_name}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Could not load module {module_name}"))
                return
                
            module_obj = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                logger.error(f"Module loader not found for {module_name}")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Module loader not found for {module_name}"))
                return
                
            # Add the module to sys.modules
            sys.modules[f"modules.{module_id}.main"] = module_obj
            spec.loader.exec_module(module_obj)
            
            # Check if module has a main function
            if not hasattr(module_obj, "main"):
                logger.error(f"Module {module_name} has no main function")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Module {module_name} has no main function"))
                return
                
            # Launch module
            logger.log_module_event("foslauncher", "module_started", {"module": module_name})
            module_obj.main()
            
        except Exception as e:
            logger.log_error_with_context(e, {"context": "module_launch", "module": module.get("Name", "Unknown")})
            error_msg = f"Failed to launch module: {str(e)}"
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
            
    def run(self) -> None:
        """Run the FoSLauncher application"""
        try:
            self.initialize()
            self.root.mainloop()
        except Exception as e:
            logger.log_error_with_context(e, {"context": "foslauncher_run"})
            raise
        finally:
            logger.log_module_stop("foslauncher")

def main():
    """Main entry point for FoSLauncher"""
    try:
        launcher = FoSLauncher()
        launcher.run()
    except Exception as e:
        logger.critical("Fatal error in FoSLauncher", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 