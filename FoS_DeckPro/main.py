import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Import unified system manager
try:
    from aptpt_pyside6_kit.unified_system_manager import unified_manager
    UNIFIED_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_SYSTEM_AVAILABLE = False
    print("Warning: Unified APTPT/REI/HCE system not available")

def main():
    app = QApplication(sys.argv)
    
    # Start unified control system if available
    if UNIFIED_SYSTEM_AVAILABLE:
        try:
            unified_manager.start_unified_control()
            print("✅ Unified APTPT/REI/HCE control system started")
        except Exception as e:
            print(f"Warning: Failed to start unified control system: {e}")
    
    window = MainWindow()
    window.show()
    
    # Run the application
    exit_code = app.exec()
    
    # Stop unified control system on exit
    if UNIFIED_SYSTEM_AVAILABLE:
        try:
            unified_manager.stop_unified_control()
            print("✅ Unified APTPT/REI/HCE control system stopped")
        except Exception as e:
            print(f"Warning: Failed to stop unified control system: {e}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
