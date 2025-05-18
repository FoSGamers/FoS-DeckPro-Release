import customtkinter as ctk
from tkinter import messagebox
from typing import Dict, Any, Optional

class AccessCodeDialog(ctk.CTkToplevel):
    """Dialog for entering access codes"""
    def __init__(self, parent, config: Dict[str, Any]):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.result = None
        self.access_level = None
        
        # Configure window
        self.title("Access Required")
        self.geometry("300x150")
        self.resizable(False, False)
        
        # Create widgets
        self.label = ctk.CTkLabel(
            self,
            text="Please enter your access code:",
            font=("Arial", 14)
        )
        self.label.pack(pady=10)
        
        self.entry = ctk.CTkEntry(
            self,
            width=200,
            show="*"  # Hide password
        )
        self.entry.pack(pady=10)
        
        self.button = ctk.CTkButton(
            self,
            text="Submit",
            command=self.submit
        )
        self.button.pack(pady=10)
        
        # Center the window
        self.center_window()
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Focus the entry
        self.entry.focus_set()
        
        # Bind Enter key to submit
        self.bind("<Return>", lambda e: self.submit())
        
    def center_window(self):
        """Center the dialog on the parent window"""
        self.update_idletasks()
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.geometry(f"+{x}+{y}")
        
    def submit(self):
        """Handle submit button click"""
        code = self.entry.get()
        if not code:
            messagebox.showerror("Error", "Please enter an access code")
            return
            
        # Check against master code first
        master_code = self.config.get("access_codes", {}).get("master", {}).get("code")
        if master_code and code == master_code:
            self.result = code
            self.access_level = "master"
            self.destroy()
            return
            
        # Check against access codes
        access_codes = self.config.get("access_codes", {})
        for level, access_info in access_codes.items():
            if isinstance(access_info, dict) and code == access_info.get("code"):
                self.result = code
                self.access_level = level
                self.destroy()
                return
                
        messagebox.showerror("Error", "Invalid access code")
        self.entry.delete(0, "end")
        self.entry.focus_set() 