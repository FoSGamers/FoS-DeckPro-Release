# File: modules/command_manager_gui.py

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

COMMANDS_FILE = "modules/chatbot_plus/commands.json"

class CommandManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FoSGamers Command Manager")
        self.commands = []
        self.selected_index = None

        self.setup_widgets()
        self.load_commands()

    def setup_widgets(self):
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
        if os.path.exists(COMMANDS_FILE):
            with open(COMMANDS_FILE, "r") as f:
                self.commands = json.load(f)
        else:
            self.commands = []

        self.refresh_tree()

    def refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for cmd in self.commands:
            self.tree.insert("", "end", values=(cmd['command'], cmd['response'], cmd.get('category', '')))

    def save_command(self):
        command = self.command_entry.get().strip()
        response = self.response_entry.get().strip()
        category = self.category_entry.get().strip()

        if not command or not response:
            messagebox.showerror("Error", "Command and Response are required")
            return

        new_entry = {"command": command, "response": response, "category": category}

        for i, cmd in enumerate(self.commands):
            if cmd['command'] == command:
                self.commands[i] = new_entry
                break
        else:
            self.commands.append(new_entry)

        with open(COMMANDS_FILE, "w") as f:
            json.dump(self.commands, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        messagebox.showinfo("Command Manager", "Commands updated and reloaded.")
        self.load_commands()
        self.clear_entries()

    def delete_command(self):
        selected = self.tree.selection()
        if not selected:
            return
        command = self.tree.item(selected[0])['values'][0]
        self.commands = [cmd for cmd in self.commands if cmd['command'] != command]

        with open(COMMANDS_FILE, "w") as f:
            json.dump(self.commands, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        messagebox.showinfo("Command Manager", "Commands updated and reloaded.")
        self.load_commands()
        self.clear_entries()

    def select_command(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        cmd_data = self.tree.item(selected[0])['values']
        self.command_entry.delete(0, tk.END)
        self.response_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.command_entry.insert(0, cmd_data[0])
        self.response_entry.insert(0, cmd_data[1])
        self.category_entry.insert(0, cmd_data[2])

    def clear_entries(self):
        self.command_entry.delete(0, tk.END)
        self.response_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = CommandManagerApp(root)
    root.mainloop()