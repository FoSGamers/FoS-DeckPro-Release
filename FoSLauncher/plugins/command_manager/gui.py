# File: modules/command_manager_gui.py

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import logging
import pandas as pd

# Set up logging with debug level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CommandManagerApp:
    def __init__(self, parent, base_dir=None):
        logger.info("Initializing CommandManagerApp")
        self.parent = parent
        self.base_dir = base_dir or os.path.join("plugins", "command_manager")
        self.commands_file = os.path.join(self.base_dir, "commands.json")
        
        # Ensure commands directory exists
        os.makedirs(os.path.dirname(self.commands_file), exist_ok=True)
        logger.info(f"Created directory for commands file: {os.path.dirname(self.commands_file)}")
        
        # Initialize variables
        self.commands = {}
        self.command_var = tk.StringVar()
        self.response_var = tk.StringVar()
        self.enabled_var = tk.BooleanVar(value=True)
        
        logger.debug("Initialized variables")
        self.setup_widgets()
        self.load_commands()

    def setup_widgets(self):
        """Set up GUI widgets"""
        logger.info("Setting up GUI widgets")
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.parent)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create command tree
        tree_frame = ctk.CTkFrame(self.main_frame)
        tree_frame.pack(expand=True, fill="both", pady=(0, 10))
        
        # Create treeview
        self.tree = ttk.Treeview(tree_frame, columns=("command", "response", "enabled"), show="headings")
        self.tree.heading("command", text="Command")
        self.tree.heading("response", text="Response")
        self.tree.heading("enabled", text="Enabled")
        self.tree.column("command", width=150)
        self.tree.column("response", width=400)
        self.tree.column("enabled", width=50)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Create command form frame
        form_frame = ctk.CTkFrame(self.main_frame)
        form_frame.pack(fill="x", pady=(0, 10))
        
        # Command field
        command_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        command_frame.pack(fill="x", pady=5)
        
        command_label = ctk.CTkLabel(command_frame, text="Command:", width=100)
        command_label.pack(side="left", padx=5)
        
        self.command_entry = ctk.CTkEntry(command_frame, textvariable=self.command_var)
        self.command_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        # Response field
        response_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        response_frame.pack(fill="x", pady=5)
        
        response_label = ctk.CTkLabel(response_frame, text="Response:", width=100)
        response_label.pack(side="left", padx=5)
        
        self.response_entry = ctk.CTkEntry(response_frame, textvariable=self.response_var)
        self.response_entry.pack(side="left", expand=True, fill="x", padx=5)
        
        # Enabled field
        enabled_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        enabled_frame.pack(fill="x", pady=5)
        
        enabled_label = ctk.CTkLabel(enabled_frame, text="Enabled:", width=100)
        enabled_label.pack(side="left", padx=5)
        
        self.enabled_check = ctk.CTkCheckBox(enabled_frame, text="", variable=self.enabled_var)
        self.enabled_check.pack(side="left", padx=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        # Save button
        save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_command)
        save_button.pack(side="right", padx=5)
        
        # Delete button
        delete_button = ctk.CTkButton(button_frame, text="Delete", command=self.delete_command)
        delete_button.pack(side="right", padx=5)
        
        # Import button
        import_button = ctk.CTkButton(button_frame, text="Import CSV", command=self.import_csv)
        import_button.pack(side="left", padx=5)
        
        # Export button
        export_button = ctk.CTkButton(button_frame, text="Export CSV", command=self.export_csv)
        export_button.pack(side="left", padx=5)
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.select_command)
        
        # Set minimum window size
        self.parent.minsize(800, 600)

    def load_commands(self):
        """Load commands from file"""
        try:
            if os.path.exists(self.commands_file):
                with open(self.commands_file, "r") as f:
                    self.commands = json.load(f)
                logger.debug(f"Loaded {len(self.commands)} commands")
            else:
                self.commands = {}
                self.save_commands()
            
            self.refresh_tree()
            
        except Exception as e:
            logger.error(f"Error loading commands: {str(e)}")
            self.commands = {}

    def refresh_tree(self):
        """Refresh the command tree"""
        logger.debug("Refreshing command tree")
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Add all commands
            for command, data in self.commands.items():
                try:
                    self.tree.insert("", "end", values=(
                        command,
                        data.get("response", ""),
                        data.get("enabled", True)
                    ))
                except Exception as e:
                    logger.error(f"Error adding command to tree: {command} - {str(e)}")
                    logger.exception("Full traceback:")
                    
            logger.debug(f"Tree refreshed with {len(self.commands)} commands")
            logger.debug(f"Current commands: {self.commands}")
        except Exception as e:
            logger.error(f"Error refreshing tree: {str(e)}")
            logger.exception("Full traceback:")

    def save_command(self):
        """Save the current command"""
        try:
            # Get values from variables
            command = self.command_entry.get()
            response = self.response_entry.get()
            enabled = self.enabled_var.get()
            
            # Debug the exact state
            logger.debug(f"Raw values - Command: '{command}' (type: {type(command)}), Response: '{response}' (type: {type(response)})")
            
            # Strip whitespace
            command = command.strip() if command else ""
            response = response.strip() if response else ""
            
            # Debug after stripping
            logger.debug(f"Stripped values - Command: '{command}', Response: '{response}'")
            
            # Validate command and response
            if not command or not response:
                logger.warning(f"Validation failed - Command empty: {not command}, Response empty: {not response}")
                messagebox.showerror("Error", "Both command and response are required")
                return
            
            # Check if we're editing an existing command
            selected = self.tree.selection()
            if selected:
                old_command = self.tree.item(selected[0])["values"][0]
                if old_command != command:
                    if old_command in self.commands:
                        del self.commands[old_command]
            
            # Add or update the command
            self.commands[command] = {
                "response": response,
                "enabled": enabled
            }
            
            # Save to file
            self.save_commands()
            # Refresh the display
            self.refresh_tree()
            # Clear the form
            self.clear_entries()
            
        except Exception as e:
            logger.error(f"Error saving command: {str(e)}")
            messagebox.showerror("Error", f"Failed to save command: {str(e)}")

    def save_commands(self):
        """Save commands to file"""
        try:
            # Use atomic write to prevent corruption
            temp_file = self.commands_file + ".tmp"
            with open(temp_file, "w") as f:
                json.dump(self.commands, f)
            # Atomic rename
            os.replace(temp_file, self.commands_file)
            logger.debug("Commands saved successfully")
        except Exception as e:
            logger.error(f"Error saving commands: {str(e)}")

    def delete_command(self):
        """Delete the selected command"""
        try:
            selected = self.tree.selection()
            if not selected:
                return
                
            command = self.tree.item(selected[0])["values"][0]
            if command in self.commands:
                del self.commands[command]
                self.save_commands()
                self.refresh_tree()
                self.clear_entries()
                
        except Exception as e:
            logger.error(f"Error deleting command: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete command: {str(e)}")

    def select_command(self, event):
        """Select a command from the tree"""
        try:
            selected = self.tree.selection()
            if not selected:
                return
                
            values = self.tree.item(selected[0])["values"]
            if values and len(values) >= 3:
                # Clear any existing selection
                self.clear_entries()
                # Set the values
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, values[0])
                self.response_entry.delete(0, tk.END)
                self.response_entry.insert(0, values[1])
                self.enabled_var.set(values[2])
                logger.debug(f"Selected command - Command: '{values[0]}', Response: '{values[1]}', Enabled: {values[2]}")
                
        except Exception as e:
            logger.error(f"Error selecting command: {str(e)}")

    def clear_entries(self):
        """Clear the entry fields and selection"""
        try:
            self.command_entry.delete(0, tk.END)
            self.response_entry.delete(0, tk.END)
            self.enabled_var.set(True)
            # Clear any selection in the tree
            for item in self.tree.selection():
                self.tree.selection_remove(item)
            logger.debug("Form entries cleared")
        except Exception as e:
            logger.error(f"Error clearing entries: {str(e)}")

    def import_csv(self):
        """Import commands from CSV file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select CSV file",
                filetypes=[("CSV files", "*.csv")]
            )
            
            if not file_path:
                return
                
            df = pd.read_csv(file_path)
            
            # Validate required columns
            if "command" not in df.columns or "response" not in df.columns:
                messagebox.showerror("Error", "CSV must contain 'command' and 'response' columns")
                return
                
            # Import commands
            for _, row in df.iterrows():
                command = str(row["command"]).strip()
                response = str(row["response"]).strip()
                enabled = bool(row.get("enabled", True))
                
                if command and response:
                    self.commands[command] = {
                        "response": response,
                        "enabled": enabled
                    }
            
            self.save_commands()
            self.refresh_tree()
            messagebox.showinfo("Success", "Commands imported successfully")
            
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")

    def export_csv(self):
        """Export commands to CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Save CSV file",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")]
            )
            
            if not file_path:
                return
                
            # Create DataFrame
            data = []
            for command, info in self.commands.items():
                data.append({
                    "command": command,
                    "response": info["response"],
                    "enabled": info["enabled"]
                })
            
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", "Commands exported successfully")
            
        except Exception as e:
            logger.error(f"Error exporting CSV: {str(e)}")
            messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    def get_command_response(self, command: str) -> str:
        """Get response for a command"""
        try:
            # Remove ! prefix and convert to lowercase for case-insensitive matching
            command = command.lstrip('!').lower()
            
            # Direct dictionary lookup for O(1) performance
            if command in self.commands:
                cmd_data = self.commands[command]
                if cmd_data.get('enabled', True):
                    return cmd_data.get('response', '')
                return f"Command '{command}' is disabled"
            
            return f"Unknown command: {command}. Type !help for available commands."
            
        except Exception as e:
            logger.error(f"Error getting command response: {str(e)}")
            return "An error occurred while processing the command."

    def cleanup(self):
        """Clean up resources when the plugin is stopped"""
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()