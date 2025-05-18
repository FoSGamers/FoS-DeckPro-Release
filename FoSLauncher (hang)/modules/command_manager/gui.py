# File: modules/command_manager_gui.py

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

COMMANDS_FILE = "modules/command_manager/commands.json"

class CommandManagerApp:
    def __init__(self, root):
        logger.info("Initializing CommandManagerApp")
        self.root = root
        self.root.title("FoSGamers Command Manager")
        self.commands = []
        self.selected_index = None

        # Ensure commands directory exists
        try:
            os.makedirs(os.path.dirname(COMMANDS_FILE), exist_ok=True)
            logger.info(f"Created directory for commands file: {os.path.dirname(COMMANDS_FILE)}")
        except Exception as e:
            logger.error(f"Failed to create commands directory: {str(e)}")
            messagebox.showerror("Error", f"Failed to create commands directory: {str(e)}")
        
        # Initialize empty commands file if it doesn't exist
        if not os.path.exists(COMMANDS_FILE):
            try:
                with open(COMMANDS_FILE, "w") as f:
                    json.dump([], f)
                logger.info(f"Created new commands file: {COMMANDS_FILE}")
            except Exception as e:
                logger.error(f"Failed to create commands file: {str(e)}")
                messagebox.showerror("Error", f"Failed to create commands file: {str(e)}")

        self.setup_widgets()
        self.load_commands()

    def setup_widgets(self):
        logger.info("Setting up GUI widgets")
        self.frame = ttk.Frame(self.root, padding=10)
        self.frame.grid(row=0, column=0, sticky="nsew")

        self.tree = ttk.Treeview(self.frame, columns=("Command", "Response", "Category"), show="headings")
        self.tree.heading("Command", text="Command")
        self.tree.heading("Response", text="Response")
        self.tree.heading("Category", text="Category")
        self.tree.grid(row=0, column=0, columnspan=4, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=4, sticky="ns")

        ttk.Label(self.frame, text="Command:").grid(row=1, column=0, sticky="e")
        self.command_entry = ttk.Entry(self.frame, width=20)
        self.command_entry.grid(row=1, column=1, sticky="w")

        ttk.Label(self.frame, text="Response:").grid(row=2, column=0, sticky="e")
        self.response_entry = ttk.Entry(self.frame, width=50)
        self.response_entry.grid(row=2, column=1, columnspan=3, sticky="w")

        ttk.Label(self.frame, text="Category:").grid(row=3, column=0, sticky="e")
        self.category_entry = ttk.Entry(self.frame, width=20)
        self.category_entry.grid(row=3, column=1, sticky="w")

        ttk.Button(self.frame, text="Add/Update", command=self.save_command).grid(row=4, column=0)
        ttk.Button(self.frame, text="Delete", command=self.delete_command).grid(row=4, column=1)
        ttk.Button(self.frame, text="Reload", command=self.load_commands).grid(row=4, column=2)
        ttk.Button(self.frame, text="Exit", command=self.root.quit).grid(row=4, column=3)

        self.tree.bind("<<TreeviewSelect>>", self.select_command)

    def load_commands(self):
        logger.info("Loading commands from file")
        try:
            if os.path.exists(COMMANDS_FILE):
                with open(COMMANDS_FILE, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.commands = data
                        logger.info(f"Loaded {len(self.commands)} commands")
                    else:
                        self.commands = []
                        logger.warning("Commands file contained invalid data, initializing empty list")
            else:
                self.commands = []
                logger.warning("Commands file not found, initializing empty list")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.commands = []
            logger.error(f"Error loading commands: {str(e)}")
            messagebox.showerror("Error", f"Failed to load commands: {str(e)}")

        self.refresh_tree()

    def refresh_tree(self):
        logger.info("Refreshing command tree")
        for i in self.tree.get_children():
            self.tree.delete(i)
        for cmd in self.commands:
            if isinstance(cmd, dict):
                self.tree.insert("", "end", values=(
                    cmd.get('command', ''),
                    cmd.get('response', ''),
                    cmd.get('category', '')
                ))

    def save_command(self):
        command = self.command_entry.get().strip()
        response = self.response_entry.get().strip()
        category = self.category_entry.get().strip()

        if not command or not response:
            logger.warning("Attempted to save command with missing required fields")
            messagebox.showerror("Error", "Command and Response are required")
            return

        new_entry = {"command": command, "response": response, "category": category}
        logger.info(f"Saving command: {command}")

        for i, cmd in enumerate(self.commands):
            if isinstance(cmd, dict) and cmd.get('command') == command:
                self.commands[i] = new_entry
                logger.info(f"Updated existing command: {command}")
                break
        else:
            self.commands.append(new_entry)
            logger.info(f"Added new command: {command}")

        try:
            with open(COMMANDS_FILE, "w") as f:
                json.dump(self.commands, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            logger.info("Successfully saved commands to file")
        except Exception as e:
            logger.error(f"Failed to save commands: {str(e)}")
            messagebox.showerror("Error", f"Failed to save commands: {str(e)}")
            return

        messagebox.showinfo("Command Manager", "Commands updated and reloaded.")
        self.load_commands()
        self.clear_entries()

    def delete_command(self):
        selected = self.tree.selection()
        if not selected:
            return
        command = self.tree.item(selected[0])['values'][0]
        logger.info(f"Deleting command: {command}")
        self.commands = [cmd for cmd in self.commands if isinstance(cmd, dict) and cmd.get('command') != command]
        
        try:
            with open(COMMANDS_FILE, "w") as f:
                json.dump(self.commands, f, indent=2)
            logger.info("Successfully saved commands after deletion")
        except Exception as e:
            logger.error(f"Failed to save commands after deletion: {str(e)}")
            messagebox.showerror("Error", f"Failed to save commands: {str(e)}")
            return
            
        self.load_commands()
        self.clear_entries()

    def select_command(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0])['values']
        self.command_entry.delete(0, tk.END)
        self.command_entry.insert(0, values[0])
        self.response_entry.delete(0, tk.END)
        self.response_entry.insert(0, values[1])
        self.category_entry.delete(0, tk.END)
        self.category_entry.insert(0, values[2])

    def clear_entries(self):
        self.command_entry.delete(0, tk.END)
        self.response_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

def main():
    root = tk.Tk()
    app = CommandManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()