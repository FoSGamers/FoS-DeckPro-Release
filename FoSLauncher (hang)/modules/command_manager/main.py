import tkinter as tk
from .gui import CommandManagerApp
from modules.logger.logger import FoSLogger

logger = FoSLogger()

class CommandManager:
    def __init__(self):
        self.app = None
        self.root = None
        logger.log_module_start("command_manager", {})
        
    def start(self):
        """Start the Command Manager GUI"""
        try:
            self.root = tk.Tk()
            self.app = CommandManagerApp(self.root)
            logger.log_module_event("command_manager", "gui_started")
            return self.root
        except Exception as e:
            logger.log_error_with_context(e, {"context": "command_manager_startup"})
            raise
            
    def stop(self):
        """Stop the Command Manager GUI"""
        if self.root:
            self.root.quit()
            self.root = None
            self.app = None
            logger.log_module_stop("command_manager")

if __name__ == "__main__":
    manager = CommandManager()
    manager.start()
    manager.root.mainloop() 