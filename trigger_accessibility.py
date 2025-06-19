#!/usr/bin/env python3
"""
Script to trigger macOS accessibility permission dialog for Python
This will help you add Python to System Settings > Privacy & Security > Accessibility
"""

import subprocess
import sys
import os

def trigger_accessibility_dialog():
    """Trigger the accessibility permission dialog"""
    print("🔧 Triggering macOS Accessibility Permission Dialog")
    print("=" * 50)
    
    # Get the current Python executable path
    python_path = sys.executable
    print(f"Python executable: {python_path}")
    
    # Try to move the mouse cursor (this will trigger the permission dialog)
    try:
        import pyautogui
        print("Attempting to move mouse cursor...")
        print("This should trigger the accessibility permission dialog.")
        print("If you see a dialog asking for accessibility permissions, click 'Allow'")
        
        # Move mouse to current position (should trigger dialog)
        current_pos = pyautogui.position()
        pyautogui.moveTo(current_pos.x + 1, current_pos.y + 1, duration=0.1)
        pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.1)
        
        print("✅ Mouse movement attempted successfully!")
        print("If you didn't see a permission dialog, you may already have permissions.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("This might mean Python needs accessibility permissions.")
        
        # Alternative method - try to take a screenshot
        try:
            print("Attempting to take a screenshot...")
            screenshot = pyautogui.screenshot()
            print("✅ Screenshot taken successfully!")
        except Exception as e2:
            print(f"❌ Screenshot failed: {e2}")
            print("This confirms Python needs accessibility permissions.")

def show_manual_instructions():
    """Show manual instructions for adding Python to accessibility"""
    print("\n📋 Manual Instructions to Add Python to Accessibility:")
    print("=" * 60)
    print("1. Open System Settings (or System Preferences)")
    print("2. Go to Privacy & Security > Accessibility")
    print("3. Click the '+' button to add an application")
    print("4. Navigate to and select these Python executables:")
    print(f"   - {sys.executable}")
    print("   - /usr/bin/python3")
    print("   - /Library/Frameworks/Python.framework/Versions/3.12/bin/python3")
    print("5. Make sure Terminal is also in the list")
    print("6. Restart Terminal after making changes")
    print("7. Run this script again to test")

def test_permissions():
    """Test if permissions are working"""
    print("\n🧪 Testing Accessibility Permissions")
    print("=" * 40)
    
    try:
        import pyautogui
        
        # Test mouse movement
        current_pos = pyautogui.position()
        pyautogui.moveTo(current_pos.x + 10, current_pos.y + 10, duration=0.5)
        pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.5)
        print("✅ Mouse movement test passed!")
        
        # Test screenshot
        screenshot = pyautogui.screenshot()
        print("✅ Screenshot test passed!")
        
        print("\n🎉 All accessibility permissions are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Permission test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Python Accessibility Permission Setup")
    print("=" * 50)
    
    # First, try to trigger the dialog
    trigger_accessibility_dialog()
    
    # Show manual instructions
    show_manual_instructions()
    
    # Test if permissions are working
    if test_permissions():
        print("\n✅ You're all set! You can now run the GUI tests.")
    else:
        print("\n❌ Please follow the manual instructions above to add Python to accessibility permissions.")
        print("Then run this script again to test.") 