import sys
from PySide6.QtWidgets import QApplication
from FoS_DeckPro.ui.main_window import MainWindow
import time

def main():
    """Main entry point for the application."""
    print("[APTPT] Entered main()")
    app = QApplication(sys.argv)
    print("[APTPT] QApplication created")
    try:
        print("[APTPT] About to create MainWindow...")
        window = MainWindow()
        print("[APTPT] MainWindow created")
        time.sleep(1)  # Add a delay to see if the app is hanging
        print("[APTPT] About to show window...")
        window.show()
        print("[APTPT] Window shown")
    except Exception as e:
        print(f"[APTPT] Error: {e}")
        import traceback
        traceback.print_exc()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 