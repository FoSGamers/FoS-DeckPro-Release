import customtkinter as ctk
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging
import os
import tkinter as tk
import tkinter.messagebox as messagebox
from typing import ClassVar

if TYPE_CHECKING:
    from .launcher import Launcher

class GUILauncher:
    """GUI launcher that manages plugin access and launching"""
    
    _instance: ClassVar[Optional['GUILauncher']] = None
    
    def __init__(self, launcher: 'Launcher'):
        self.logger = logging.getLogger("gui_launcher")
        self.launcher = launcher
        self.window = None
        self.password_window = None
        GUILauncher._instance = self
        
    @classmethod
    def get_main_window(cls) -> Optional[tk.Tk]:
        """Get the main application window"""
        if cls._instance is None:
            return None
        return cls._instance.window
        
    def show_password_dialog(self):
        """Show password entry dialog"""
        try:
            # Create password dialog
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("FoS Launcher - Password Required")
            dialog.geometry("400x200")
            dialog.configure(fg_color="#1a1a1a")
            dialog.resizable(False, False)
            
            # Center the window
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'{width}x{height}+{x}+{y}')
            
            # Make dialog modal
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Create main frame
            main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            main_frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Add title
            title = ctk.CTkLabel(main_frame,
                               text="Enter Master Password",
                               font=("Arial", 20, "bold"),
                               text_color="#ffffff")
            title.pack(pady=(0, 20))
            
            # Add password entry
            password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            password_frame.pack(fill="x", pady=(0, 20))
            
            password_label = ctk.CTkLabel(password_frame,
                                        text="Password:",
                                        font=("Arial", 12),
                                        text_color="#ffffff")
            password_label.pack(side="left", padx=(0, 10))
            
            password_entry = ctk.CTkEntry(password_frame,
                                        show="*",
                                        width=200,
                                        fg_color="#2b2b2b",
                                        border_color="#1f538d",
                                        text_color="#ffffff")
            password_entry.pack(side="left", expand=True, fill="x")
            
            # Add error label (hidden initially)
            error_label = ctk.CTkLabel(main_frame,
                                     text="",
                                     font=("Arial", 12),
                                     text_color="#e74c3c")
            error_label.pack()
            error_label.pack_forget()
            
            # Variable to track verification result
            self.password_verified = False
            
            def verify_password():
                password = password_entry.get()
                if password == "FoSGamers2024":  # Master password
                    self.logger.info("Master access granted")
                    self.launcher.set_master_access(True)
                    self.password_verified = True
                    dialog.quit()
                    dialog.destroy()
                    return
                
                # Check access codes
                access_codes = self.launcher.config.get("access_codes", {})
                if password in access_codes:
                    self.logger.info(f"Access granted with code: {password}")
                    self.password_verified = True
                    dialog.quit()
                    dialog.destroy()
                    return
                
                # Invalid password
                self.logger.warning("Invalid password")
                error_label.configure(text="Invalid password")
                error_label.pack()
                password_entry.delete(0, tk.END)
                password_entry.focus_set()
            
            # Bind Enter key to verify_password
            password_entry.bind("<Return>", lambda e: verify_password())
            
            # Add verify button
            verify_button = ctk.CTkButton(main_frame,
                                        text="Verify",
                                        command=verify_password,
                                        width=100,
                                        height=32,
                                        fg_color="#2ecc71",
                                        hover_color="#27ae60")
            verify_button.pack(side="right", padx=5)
            
            # Add cancel button
            cancel_button = ctk.CTkButton(main_frame,
                                        text="Cancel",
                                        command=lambda: (dialog.quit(), dialog.destroy()),
                                        width=100,
                                        height=32,
                                        fg_color="#e74c3c",
                                        hover_color="#c0392b")
            cancel_button.pack(side="right", padx=5)
            
            # Make window unclosable by X button
            dialog.protocol("WM_DELETE_WINDOW", lambda: None)
            
            # Focus password entry
            password_entry.focus_set()
            
            # Wait for dialog
            dialog.wait_visibility()
            dialog.grab_set()
            dialog.mainloop()
            
            # If password was verified, create main GUI
            if self.password_verified:
                self.create_gui()
            else:
                self.root.quit()
            
        except Exception as e:
            self.logger.error(f"Failed to show password dialog: {str(e)}")
            self.root.quit()
            
    def create_gui(self):
        """Create the launcher GUI"""
        try:
            # Create main layout
            main_layout = ctk.CTkFrame(self.window, fg_color="#1a1a1a")
            main_layout.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Create header
            header = ctk.CTkFrame(main_layout, fg_color="transparent")
            header.pack(fill="x", pady=(0, 30))
            
            title = ctk.CTkLabel(header, text="FoSLauncher", 
                               font=("Arial", 28, "bold"),
                               text_color="#ffffff")
            title.pack(side="left", padx=20)
            
            # Add plugin management button if master access
            if self.launcher.master_access:
                manage_button = ctk.CTkButton(header,
                                            text="Manage Plugins",
                                            command=self.show_plugin_management,
                                            width=120,
                                            height=32,
                                            fg_color="#3498db",
                                            hover_color="#2980b9")
                manage_button.pack(side="right", padx=20)
            
            # Create plugin section title
            plugin_title = ctk.CTkLabel(main_layout, text="Available Plugins", 
                                      font=("Arial", 18, "bold"),
                                      text_color="#4a9eff")
            plugin_title.pack(pady=(0, 15), padx=20, anchor="w")
            
            # Create scrollable plugin frame
            container = ctk.CTkScrollableFrame(main_layout, fg_color="transparent")
            container.pack(expand=True, fill="both", padx=10)
            
            # Add plugins
            for plugin_name in self.launcher.plugin_manager.get_loaded_plugins():
                self.add_plugin_to_gui(container, plugin_name)
            
            # Create footer
            footer = ctk.CTkFrame(main_layout, fg_color="transparent")
            footer.pack(fill="x", pady=20)
            
            stop_button = ctk.CTkButton(footer, text="Exit Launcher", 
                                      command=self.stop,
                                      width=120, height=32,
                                      fg_color="#e74c3c",
                                      hover_color="#c0392b")
            stop_button.pack(side="right", padx=20)
            
            # Make window unclosable by X button (must use Exit button)
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)
            
            self.logger.info("GUI created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create GUI: {str(e)}")
            raise
    
    def add_plugin_to_gui(self, parent, plugin_name):
        """Add a plugin to the GUI"""
        try:
            plugin = self.launcher.get_plugin(plugin_name)
            if not plugin:
                return
            
            # Check if user has access to this specific plugin
            has_access = self.launcher.has_plugin_access(plugin_name)
            
            # Create frame with border
            frame = ctk.CTkFrame(parent, fg_color="#363636", corner_radius=6)
            frame.pack(fill="x", padx=5, pady=5)
            
            # Create info frame
            info_frame = ctk.CTkFrame(frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)
            
            # Set text color based on access
            text_color = "#ffffff" if has_access else "#666666"
            description_color = "#cccccc" if has_access else "#666666"
            
            name_label = ctk.CTkLabel(info_frame, 
                                    text=plugin.get_name().replace("_", " ").title(), 
                                    font=("Arial", 16, "bold"),
                                    text_color=text_color)
            name_label.pack(anchor="w")
            
            version_label = ctk.CTkLabel(info_frame, 
                                       text=f"Version {plugin.get_version()}",
                                       font=("Arial", 12),
                                       text_color=text_color)
            version_label.pack(anchor="w")
            
            description_label = ctk.CTkLabel(info_frame, 
                                          text=plugin.get_description(),
                                          wraplength=400,
                                          font=("Arial", 12),
                                          text_color=description_color)
            description_label.pack(anchor="w", pady=(5, 0))
            
            # Create button frame
            button_frame = ctk.CTkFrame(frame, fg_color="transparent")
            button_frame.pack(side="right", padx=10)
            
            if has_access:
                # User has access - show normal buttons
                start_button = ctk.CTkButton(button_frame, 
                                           text="Launch", 
                                           command=lambda: self.launch_plugin(plugin_name),
                                           width=80, height=28,
                                           fg_color="#2ecc71",
                                           hover_color="#27ae60")
                start_button.pack(pady=(0, 5))
                
                stop_button = ctk.CTkButton(button_frame, 
                                          text="Stop",
                                          command=lambda: self.stop_plugin(plugin_name),
                                          width=80, height=28,
                                          fg_color="#e74c3c",
                                          hover_color="#c0392b")
                stop_button.pack()
            else:
                # User doesn't have access - show disabled state
                access_label = ctk.CTkLabel(button_frame,
                                          text="Subscription Required",
                                          text_color="#666666",
                                          font=("Arial", 12))
                access_label.pack(pady=10)
            
        except Exception as e:
            self.logger.error(f"Failed to add plugin {plugin_name} to GUI: {str(e)}")
    
    def launch_plugin(self, plugin_name):
        """Launch a plugin in its own window"""
        try:
            plugin = self.launcher.get_plugin(plugin_name)
            if not plugin:
                self.logger.error(f"Plugin {plugin_name} not found")
                self.show_error_message("Plugin not found")
                return
                
            if self.launcher.plugin_manager.start_plugin(plugin_name):
                self.logger.info(f"Launched plugin: {plugin_name}")
            else:
                self.logger.error(f"Failed to launch plugin: {plugin_name}")
                self.show_error_message(f"Failed to launch {plugin_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to launch plugin {plugin_name}: {str(e)}")
            self.show_error_message(f"Error launching {plugin_name}: {str(e)}")
    
    def stop_plugin(self, plugin_name):
        """Stop a plugin"""
        try:
            if self.launcher.plugin_manager.stop_plugin(plugin_name):
                self.logger.info(f"Stopped plugin: {plugin_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to stop plugin {plugin_name}: {str(e)}")
    
    def show_error_message(self, message):
        """Show an error message to the user"""
        try:
            error_window = ctk.CTkToplevel(self.window)
            error_window.title("Error")
            error_window.geometry("400x150")
            error_window.configure(fg_color="#1a1a1a")
            
            # Center the window
            error_window.update_idletasks()
            width = error_window.winfo_width()
            height = error_window.winfo_height()
            x = (error_window.winfo_screenwidth() // 2) - (width // 2)
            y = (error_window.winfo_screenheight() // 2) - (height // 2)
            error_window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Create main frame
            main_frame = ctk.CTkFrame(error_window, fg_color="transparent")
            main_frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Add error message
            error_label = ctk.CTkLabel(main_frame,
                                     text=message,
                                     text_color="#e74c3c",
                                     font=("Arial", 14),
                                     wraplength=350)
            error_label.pack(pady=(0, 20))
            
            # Add close button
            close_button = ctk.CTkButton(main_frame,
                                       text="Close",
                                       command=error_window.destroy,
                                       width=100,
                                       height=32,
                                       fg_color="#e74c3c",
                                       hover_color="#c0392b")
            close_button.pack()
            
            # Make window modal
            error_window.grab_set()
            
        except Exception as e:
            self.logger.error(f"Failed to show error message: {str(e)}")
    
    def show_plugin_management(self):
        """Show plugin management window"""
        try:
            # Create management window
            management_window = ctk.CTkToplevel(self.window)
            management_window.title("Plugin Management")
            management_window.geometry("600x400")
            management_window.configure(fg_color="#1a1a1a")
            
            # Center the window
            management_window.update_idletasks()
            width = management_window.winfo_width()
            height = management_window.winfo_height()
            x = (management_window.winfo_screenwidth() // 2) - (width // 2)
            y = (management_window.winfo_screenheight() // 2) - (height // 2)
            management_window.geometry(f'{width}x{height}+{x}+{y}')
            
            # Create main frame
            main_frame = ctk.CTkFrame(management_window, fg_color="transparent")
            main_frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Add title
            title = ctk.CTkLabel(main_frame,
                               text="Plugin Management",
                               font=("Arial", 24, "bold"),
                               text_color="#ffffff")
            title.pack(pady=(0, 20))
            
            # Create plugin list frame
            list_frame = ctk.CTkFrame(main_frame, fg_color="#363636")
            list_frame.pack(expand=True, fill="both", pady=(0, 20))
            
            # Add plugin list
            for plugin_name in self.launcher.plugin_manager.get_loaded_plugins():
                plugin_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
                plugin_frame.pack(fill="x", padx=10, pady=5)
                
                name_label = ctk.CTkLabel(plugin_frame,
                                        text=plugin_name.replace("_", " ").title(),
                                        font=("Arial", 14),
                                        text_color="#ffffff")
                name_label.pack(side="left", padx=10)
                
                uninstall_button = ctk.CTkButton(plugin_frame,
                                               text="Uninstall",
                                               command=lambda p=plugin_name: self.uninstall_plugin(p),
                                               width=100,
                                               height=28,
                                               fg_color="#e74c3c",
                                               hover_color="#c0392b")
                uninstall_button.pack(side="right", padx=10)
            
            # Add install section
            install_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            install_frame.pack(fill="x", pady=(0, 20))
            
            install_label = ctk.CTkLabel(install_frame,
                                       text="Install New Plugin:",
                                       font=("Arial", 14),
                                       text_color="#ffffff")
            install_label.pack(side="left", padx=10)
            
            plugin_entry = ctk.CTkEntry(install_frame,
                                      placeholder_text="Plugin name",
                                      width=200,
                                      height=32)
            plugin_entry.pack(side="left", padx=10)
            
            install_button = ctk.CTkButton(install_frame,
                                         text="Install",
                                         command=lambda: self.install_plugin(plugin_entry.get()),
                                         width=100,
                                         height=32,
                                         fg_color="#2ecc71",
                                         hover_color="#27ae60")
            install_button.pack(side="left", padx=10)
            
            # Make window modal
            management_window.grab_set()
            
        except Exception as e:
            self.logger.error(f"Failed to show plugin management: {str(e)}")
            self.show_error_message(f"Failed to show plugin management: {str(e)}")
            
    def install_plugin(self, plugin_name):
        """Install a new plugin"""
        try:
            if not plugin_name:
                self.show_error_message("Please enter a plugin name")
                return
                
            # Create default config
            config = {
                "enabled": True,
                "auto_start": False,
                "requires_code": True,
                "access_level": "basic"
            }
            
            if self.launcher.install_plugin(plugin_name, config):
                self.logger.info(f"Installed plugin: {plugin_name}")
                self.show_error_message(f"Successfully installed {plugin_name}")
            else:
                self.logger.error(f"Failed to install plugin: {plugin_name}")
                self.show_error_message(f"Failed to install {plugin_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to install plugin {plugin_name}: {str(e)}")
            self.show_error_message(f"Error installing {plugin_name}: {str(e)}")
            
    def uninstall_plugin(self, plugin_name):
        """Uninstall a plugin"""
        try:
            if self.launcher.uninstall_plugin(plugin_name):
                self.logger.info(f"Uninstalled plugin: {plugin_name}")
                self.show_error_message(f"Successfully uninstalled {plugin_name}")
            else:
                self.logger.error(f"Failed to uninstall plugin: {plugin_name}")
                self.show_error_message(f"Failed to uninstall {plugin_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to uninstall plugin {plugin_name}: {str(e)}")
            self.show_error_message(f"Error uninstalling {plugin_name}: {str(e)}")
    
    def start(self) -> bool:
        """Start the GUI launcher"""
        try:
            # Create main window
            self.window = ctk.CTk()
            self.window.title("FoS Launcher")
            self.window.geometry("800x800")
            self.window.configure(fg_color="#1a1a1a")
            
            # Set appearance mode and color theme
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            
            # Show password dialog
            if not self.verify_password():
                self.window.destroy()
                return False
            
            # Create main GUI
            self.create_gui()
            
            # Start main loop
            self.window.mainloop()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start GUI launcher: {str(e)}")
            return False
    
    def verify_password(self) -> bool:
        """Verify the password and return True if valid"""
        try:
            # Create password dialog
            dialog = ctk.CTkToplevel(self.window)
            dialog.title("FoS Launcher - Password Required")
            dialog.geometry("400x200")
            dialog.configure(fg_color="#1a1a1a")
            dialog.resizable(False, False)
            
            # Center the window
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f'{width}x{height}+{x}+{y}')
            
            # Make dialog modal
            dialog.transient(self.window)
            dialog.grab_set()
            
            # Create main frame
            main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            main_frame.pack(expand=True, fill="both", padx=20, pady=20)
            
            # Add title
            title = ctk.CTkLabel(main_frame,
                               text="Enter Master Password",
                               font=("Arial", 20, "bold"),
                               text_color="#ffffff")
            title.pack(pady=(0, 20))
            
            # Add password entry
            password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            password_frame.pack(fill="x", pady=(0, 20))
            
            password_label = ctk.CTkLabel(password_frame,
                                        text="Password:",
                                        font=("Arial", 12),
                                        text_color="#ffffff")
            password_label.pack(side="left", padx=(0, 10))
            
            password_entry = ctk.CTkEntry(password_frame,
                                        show="*",
                                        width=200,
                                        fg_color="#2b2b2b",
                                        border_color="#1f538d",
                                        text_color="#ffffff")
            password_entry.pack(side="left", expand=True, fill="x")
            
            # Add error label (hidden initially)
            error_label = ctk.CTkLabel(main_frame,
                                     text="",
                                     font=("Arial", 12),
                                     text_color="#e74c3c")
            error_label.pack()
            error_label.pack_forget()
            
            # Variable to track verification result
            password_verified = False
            
            def verify():
                nonlocal password_verified
                password = password_entry.get()
                
                # Check master password
                if password == self.launcher.config.get("global", {}).get("security", {}).get("master_code", "FoSGamers2024"):
                    self.logger.info("Master access granted")
                    self.launcher.set_master_access(True)
                    password_verified = True
                    dialog.destroy()
                    return
                
                # Check access codes
                access_codes = self.launcher.config.get("global", {}).get("security", {}).get("access_codes", {})
                for code_type, code_info in access_codes.items():
                    if password == code_info.get("code"):
                        self.logger.info(f"Access granted with {code_type} code")
                        self.launcher.set_master_access(True)  # Grant full access for now
                        password_verified = True
                        dialog.destroy()
                        return
                
                # Invalid password
                self.logger.warning("Invalid password")
                error_label.configure(text="Invalid password")
                error_label.pack()
                password_entry.delete(0, tk.END)
                password_entry.focus_set()
            
            # Bind Enter key to verify
            password_entry.bind("<Return>", lambda e: verify())
            
            # Add verify button
            verify_button = ctk.CTkButton(main_frame,
                                        text="Verify",
                                        command=verify,
                                        width=100,
                                        height=32,
                                        fg_color="#2ecc71",
                                        hover_color="#27ae60")
            verify_button.pack(side="right", padx=5)
            
            # Add cancel button
            cancel_button = ctk.CTkButton(main_frame,
                                        text="Cancel",
                                        command=dialog.destroy,
                                        width=100,
                                        height=32,
                                        fg_color="#e74c3c",
                                        hover_color="#c0392b")
            cancel_button.pack(side="right", padx=5)
            
            # Focus password entry
            password_entry.focus_set()
            
            # Wait for dialog
            dialog.wait_window()
            
            return password_verified
            
        except Exception as e:
            self.logger.error(f"Failed to verify password: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the GUI launcher"""
        try:
            # Stop all active plugins first
            for plugin_name in self.launcher.plugin_manager.get_loaded_plugins():
                self.stop_plugin(plugin_name)
            
            # Stop the launcher
            if not self.launcher.stop():
                return False
            
            # Cleanup windows
            if self.window:
                try:
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
                    
                    # Finally quit the main window
                    try:
                        self.window.quit()
                    except Exception:
                        pass
                    
                except Exception as e:
                    self.logger.warning(f"Non-critical error during window cleanup: {str(e)}")
            
            # Cleanup root window
            if hasattr(self, 'root') and self.root:
                try:
                    # Cancel any pending after callbacks
                    for after_id in self.root.tk.call('after', 'info'):
                        try:
                            self.root.after_cancel(after_id)
                        except Exception:
                            pass
                    # Destroy root window
                    self.root.destroy()
                except Exception as e:
                    self.logger.warning(f"Non-critical error during root window cleanup: {str(e)}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop GUI launcher: {str(e)}")
            return False 