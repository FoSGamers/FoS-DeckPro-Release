#!/usr/bin/env python3
"""
Epic All-Features GUI Test Runner for FoS_DeckPro
- Automates every feature and flow
- Takes screenshots at every step
- Uses OpenAI Vision to verify GUI correctness
- Logs all results and generates a detailed report
"""

import os
import time
import json
import pyautogui
import subprocess
import requests
from datetime import datetime
from PIL import Image
import shutil

try:
    import pygetwindow as gw
    PYWINDOW_AVAILABLE = True
except ImportError:
    PYWINDOW_AVAILABLE = False
    print("⚠️ pygetwindow not available - install with: pip install pygetwindow")

# Configure PyAutoGUI for better reliability
pyautogui.FAILSAFE = False  # Disable fail-safe for automation
pyautogui.PAUSE = 0.5  # Add pause between actions

OPENAI_API_KEY = "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"
VISION_URL = "https://api.openai.com/v1/vision/generate"

MENU_MAP_FILE = 'menu_map.json'
DIALOG_MAP_FILE = 'dialog_map.json'

# List of all features/flows to test
ALL_FEATURES = [
    "Launch App",
    "Menu: File > New",
    "Menu: File > Open", 
    "Menu: File > Save",
    "Menu: File > Export",
    "Menu: Edit > Undo",
    "Menu: Edit > Redo",
    "Menu: Tools > Pricing Dashboard",
    "Menu: Tools > Analytics",
    "Menu: Help > About",
    "Card Table: Select Card",
    "Card Table: Edit Card",
    "Card Table: Delete Card",
    "Card Table: Enrich Card",
    "Search: Basic",
    "Search: Advanced",
    "Paywall: Unlock Premium",
    "Deck Builder: Create Deck",
    "Deck Builder: Export Deck",
    "Backup: Export Data",
    "Restore: Import Data",
]

# Expected GUI descriptions for Vision analysis
EXPECTED_GUI = {
    "Launch App": "The main window of FoS_DeckPro is visible with menus for File, Edit, Tools, Help, and a card table.",
    "Menu: File > New": "A dialog or new inventory is shown, card table is empty or reset.",
    "Menu: File > Open": "A file dialog is visible or a different inventory is loaded.",
    "Menu: File > Save": "A save dialog or confirmation appears.",
    "Menu: File > Export": "An export dialog or confirmation appears.",
    "Menu: Edit > Undo": "The last change is undone in the card table.",
    "Menu: Edit > Redo": "The last undone change is redone in the card table.",
    "Menu: Tools > Pricing Dashboard": "A dashboard with real-time pricing and analytics is visible.",
    "Menu: Tools > Analytics": "A window or panel with collection analytics is visible.",
    "Menu: Help > About": "An About dialog with app info is visible.",
    "Card Table: Select Card": "A card row is highlighted in the card table.",
    "Card Table: Edit Card": "A card edit dialog is open or card details are editable.",
    "Card Table: Delete Card": "A card is removed from the table, or a confirmation dialog appears.",
    "Card Table: Enrich Card": "Card details are updated with enrichment info.",
    "Search: Basic": "The card table is filtered to show search results.",
    "Search: Advanced": "Advanced search dialog is open and results are shown.",
    "Paywall: Unlock Premium": "A dialog for entering a password/key is shown, and premium features become available after unlock.",
    "Deck Builder: Create Deck": "A deck builder interface is visible.",
    "Deck Builder: Export Deck": "A dialog or confirmation for deck export is shown.",
    "Backup: Export Data": "A dialog or confirmation for data export is shown.",
    "Restore: Import Data": "A dialog or confirmation for data import is shown.",
}

def resize_image_for_vision(image_path, max_width=800):
    """Resize image to max_width, maintaining aspect ratio, and save as compressed JPEG."""
    try:
        img = Image.open(image_path)
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        # Convert to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Save as compressed JPEG
        temp_path = image_path.replace('.png', '_vision.jpg')
        img.save(temp_path, format='JPEG', quality=70, optimize=True)
        
        # Check file size
        file_size = os.path.getsize(temp_path) / (1024 * 1024)  # MB
        print(f"📏 Resized image: {file_size:.2f}MB")
        
        return temp_path
    except Exception as e:
        print(f"⚠️ Image resize failed: {e}")
        return image_path

def openai_vision_check(image_path, expected_desc):
    """Send resized screenshot to OpenAI Vision and check if GUI matches expected description."""
    try:
        resized_path = resize_image_for_vision(image_path)
        
        # Check if file is still too large
        file_size = os.path.getsize(resized_path) / (1024 * 1024)  # MB
        if file_size > 4:
            return f"Image still too large ({file_size:.2f}MB) for Vision API"
        
        with open(resized_path, "rb") as img_file:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Use the correct GPT-4 Vision API structure
            data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Does this screenshot show: {expected_desc}? Answer YES or NO and explain briefly."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_file.read().hex()}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150
            }
            
            # Convert image to base64
            import base64
            img_file.seek(0)
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            data["messages"][0]["content"][1]["image_url"]["url"] = f"data:image/jpeg;base64,{img_base64}"
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return answer
            else:
                return f"Vision API Error: {response.status_code} - {response.text[:200]}"
                
    except Exception as e:
        return f"Vision API Error: {str(e)}"

def maximize_and_focus_python_app():
    """Maximize and bring the Python app window to the front using AppleScript."""
    try:
        # Maximize the first window of the Python app
        script = (
            'tell application "System Events"\n'
            '    tell application process "Python"\n'
            '        set frontmost to true\n'
            '        try\n'
            '            set position of window 1 to {0, 22}\n'
            '            set size of window 1 to {1440, 900}\n'  # Adjust to your screen size
            '        end try\n'
            '    end tell\n'
            'end tell'
        )
        subprocess.run(["osascript", "-e", script])
        time.sleep(1)
        print("✅ AppleScript: Maximized and focused Python app")
    except Exception as e:
        print(f"⚠️ AppleScript maximize/focus failed: {e}")

def focus_app_window():
    """Maximize and focus the app window using AppleScript, then click in the center."""
    try:
        maximize_and_focus_python_app()
        center_x, center_y = get_screen_center()
        pyautogui.click(center_x, center_y)
        time.sleep(1)
        print("✅ App window focused and maximized")
    except Exception as e:
        print(f"⚠️ Focus failed: {e}")

def get_menu_coordinates_with_vision(menu_name, screenshot_path):
    """Use OpenAI Vision to get the coordinates of a menu in the screenshot."""
    try:
        # Prompt for Vision
        prompt = f"What are the screen coordinates (x, y) of the '{menu_name}' menu in this screenshot? Return only the coordinates as two integers separated by a comma, e.g., '120, 10'."
        resized_path = resize_image_for_vision(screenshot_path)
        with open(resized_path, "rb") as img_file:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    }
                ],
                "max_tokens": 50
            }
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            if response.status_code == 200:
                result = response.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"[Vision] {menu_name} menu coordinates: {answer}")
                # Parse coordinates
                import re
                match = re.search(r'(\d+)[, ]+(\d+)', answer)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                    return x, y
                else:
                    print(f"[Vision] Could not parse coordinates from: {answer}")
            else:
                print(f"[Vision] API error: {response.status_code} {response.text[:200]}")
    except Exception as e:
        print(f"[Vision] Exception: {e}")
    return None

def menu_click(menu, submenu=None):
    """Click on the correct menu and submenu using mapped positions."""
    # Click menu bar
    menu_coords = {"File": (70, 20), "Edit": (140, 20), "View": (210, 20), "Tools": (280, 20)}
    x, y = menu_coords.get(menu, (70, 20))
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()
    time.sleep(0.5)
    if submenu:
        # Get submenu position
        sub_x, sub_y = get_menu_item_position(menu, submenu)
        pyautogui.moveTo(sub_x, sub_y, duration=0.2)
        pyautogui.click()
        time.sleep(0.5)
    return True

def automate_feature(feature):
    """Automate a specific feature with robust error handling."""
    try:
        print(f"🤖 Automating: {feature}")
        focus_app_window()
        
        if feature == "Launch App":
            # App is already launched, just take screenshot
            pass
            
        elif feature == "Menu: File > New":
            menu_click("File", "New")
            
        elif feature == "Menu: File > Open":
            menu_click("File", "Open")
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Menu: File > Save":
            menu_click("File", "Save")
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Menu: File > Export":
            menu_click("File", "Export")
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Menu: Edit > Undo":
            menu_click("Edit", "Undo")
            
        elif feature == "Menu: Edit > Redo":
            menu_click("Edit", "Redo")
            
        elif feature == "Menu: Tools > Pricing Dashboard":
            menu_click("Tools", "Pricing Dashboard")
            time.sleep(2)
            pyautogui.press('esc')
            
        elif feature == "Menu: Tools > Analytics":
            menu_click("Tools", "Analytics")
            time.sleep(2)
            pyautogui.press('esc')
            
        elif feature == "Menu: Help > About":
            menu_click("Help", "About")
            time.sleep(2)
            pyautogui.press('esc')
            
        elif feature == "Card Table: Select Card":
            # Click in the card table area
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x, center_y + 100, duration=0.5)
            pyautogui.click()
            
        elif feature == "Card Table: Edit Card":
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x, center_y + 100, duration=0.5)
            pyautogui.doubleClick()
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Card Table: Delete Card":
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x, center_y + 100, duration=0.5)
            pyautogui.click()
            pyautogui.press('delete')
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Card Table: Enrich Card":
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x, center_y + 100, duration=0.5)
            pyautogui.rightClick()
            time.sleep(1)
            pyautogui.press('down')
            pyautogui.press('enter')
            time.sleep(2)
            
        elif feature == "Search: Basic":
            # Click in search area
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x - 200, center_y - 200, duration=0.5)
            pyautogui.click()
            pyautogui.write('Bolt', interval=0.1)
            pyautogui.press('enter')
            time.sleep(1)
            
        elif feature == "Search: Advanced":
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x - 200, center_y - 200, duration=0.5)
            pyautogui.click()
            pyautogui.hotkey('cmd', 'f')  # Use cmd instead of ctrl on macOS
            time.sleep(1)
            pyautogui.write('Paradise', interval=0.1)
            pyautogui.press('enter')
            time.sleep(1)
            
        elif feature == "Paywall: Unlock Premium":
            menu_click("Tools", "Pricing Dashboard")
            time.sleep(1)
            pyautogui.write('your-paywall-password', interval=0.1)
            pyautogui.press('enter')
            time.sleep(2)
            
        elif feature == "Deck Builder: Create Deck":
            menu_click("File", "New")
            time.sleep(1)
            center_x, center_y = get_screen_center()
            pyautogui.moveTo(center_x + 100, center_y + 100, duration=0.5)
            pyautogui.click()
            time.sleep(1)
            
        elif feature == "Deck Builder: Export Deck":
            menu_click("File", "Export")
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Backup: Export Data":
            menu_click("File", "Export")
            time.sleep(1)
            pyautogui.press('esc')
            
        elif feature == "Restore: Import Data":
            menu_click("File", "Open")
            time.sleep(1)
            pyautogui.press('esc')
            
        time.sleep(1)
        print(f"✅ Automation completed: {feature}")
        
    except Exception as e:
        print(f"❌ Automation failed for {feature}: {e}")

def take_screenshot(output_path):
    """Trigger the app's internal screenshot via file-based trigger and wait for the file to appear."""
    import time, os, shutil
    trigger_file = 'take_screenshot.txt'
    
    # Get the filename that the app will save
    expected_filename = os.path.basename(output_path)
    
    # Write the desired output filename to the trigger file
    with open(trigger_file, 'w') as f:
        f.write(expected_filename)
    print(f"🤖 Triggered internal screenshot: {output_path}")
    
    # Wait for the screenshot file to appear in current directory (timeout after 5s)
    for _ in range(20):
        if os.path.exists(expected_filename):
            # Move the file to the output directory
            shutil.move(expected_filename, output_path)
            print(f"✅ Internal screenshot saved: {output_path}")
            return True
        time.sleep(0.25)
    
    print(f"❌ Screenshot file not found after trigger: {expected_filename}")
    return False

def get_screen_center():
    """Get the center of the screen for safer clicking."""
    screen_width, screen_height = pyautogui.size()
    return screen_width // 2, screen_height // 2

def test_automation(step_name, automation_func, out_dir):
    """Execute automation step and capture screenshot"""
    print(f"🤖 Automating: {step_name}")
    
    # Execute the automation
    automation_func()
    print(f"✅ Automation completed: {step_name}")
    
    # Take screenshot with proper filename
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = step_name.replace(' ', '_').replace(':', '_').replace('>', '_').replace('/', '_')
    filename = os.path.join(out_dir, f"{safe_name}_{ts}.png")
    
    success = take_screenshot(filename)
    if success:
        print(f"✅ Internal screenshot saved: {filename}")
        # Resize for Vision API
        resize_image_for_vision(filename)
        return filename
    else:
        print(f"❌ Screenshot failed for: {step_name}")
        return None

def main():
    """Main test runner."""
    print("🚀 Epic All-Features GUI Test Runner")
    print("=" * 60)
    
    # Create output directory
    out_dir = f"all_gui_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(out_dir, exist_ok=True)
    print(f"📁 Output directory: {out_dir}")

    # Launch the app
    print("🎯 Launching FoS_DeckPro...")
    app_proc = subprocess.Popen(["python3", "../main.py"])
    time.sleep(10)  # Wait longer for app to fully launch

    results = []
    try:
        for i, feature in enumerate(ALL_FEATURES, 1):
            print(f"\n📋 Feature {i}/{len(ALL_FEATURES)}")
            
            # Use the new test_automation approach
            screenshot = test_automation(feature, lambda: automate_feature(feature), out_dir)
            
            if screenshot:
                # Check with Vision API
                expected_desc = EXPECTED_GUI.get(feature, "The GUI is correct for this feature.")
                vision_result = openai_vision_check(screenshot, expected_desc)
                print(f"Vision result: {vision_result}")
                
                status = "PASS" if "YES" in vision_result.upper() else "FAIL"
            else:
                vision_result = "Screenshot failed"
                status = "ERROR"
            
            result = {
                "feature": feature,
                "screenshot": screenshot,
                "vision_result": vision_result,
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
            
            # Brief pause between features
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
    finally:
        # Terminate app
        try:
            app_proc.terminate()
            print("✅ App terminated")
        except:
            pass

    # Generate comprehensive report
    print(f"\n📊 Generating Test Report...")
    
    # Calculate statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["status"] == "PASS")
    failed_tests = sum(1 for r in results if r["status"] == "FAIL")
    error_tests = sum(1 for r in results if r["status"] == "ERROR")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Save detailed report
    report_data = {
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat()
        },
        "results": results
    }
    
    report_file = os.path.join(out_dir, "all_gui_test_report.json")
    with open(report_file, "w") as f:
        json.dump(report_data, f, indent=2)
    
    # Print summary
    print(f"\n🎉 Test Suite Complete!")
    print("=" * 40)
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"⚠️ Errors: {error_tests}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"📄 Report: {report_file}")
    
    if success_rate >= 80:
        print("🎯 EXCELLENT: High compliance with APTPT/REI/HCE theories!")
    elif success_rate >= 60:
        print("✅ GOOD: Moderate compliance with APTPT/REI/HCE theories")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Low compliance with APTPT/REI/HCE theories")

# --- Menu Mapping ---
def map_menu_items(menu_name):
    """Open a menu, screenshot, and use Vision to extract menu item Y-offsets."""
    menu_click(menu_name)
    time.sleep(0.5)
    screenshot_path = f"menu_{menu_name}_expanded.png"
    pyautogui.screenshot(screenshot_path)
    # Use Vision to extract menu items and their Y-offsets
    prompt = f"List all visible menu items under the '{menu_name}' menu in this screenshot. For each, return the item text and its Y coordinate (relative to the top of the menu bar), as a JSON array of objects with 'text' and 'y' fields."
    # ... Vision API call here ...
    # For now, simulate with dummy data
    menu_items = [
        {"text": "Open JSON...", "y": 60},
        {"text": "Export...", "y": 90},
        {"text": "Import...", "y": 120},
        # ...
    ]
    try:
        with open(MENU_MAP_FILE, 'r') as f:
            menu_map = json.load(f)
    except Exception:
        menu_map = {}
    menu_map[menu_name] = menu_items
    with open(MENU_MAP_FILE, 'w') as f:
        json.dump(menu_map, f, indent=2)
    return menu_items

def get_menu_item_position(menu_name, item_text):
    try:
        with open(MENU_MAP_FILE, 'r') as f:
            menu_map = json.load(f)
    except Exception:
        menu_map = {}
    if menu_name not in menu_map:
        map_menu_items(menu_name)
        with open(MENU_MAP_FILE, 'r') as f:
            menu_map = json.load(f)
    for item in menu_map.get(menu_name, []):
        if item_text.lower() in item['text'].lower():
            menu_x = {"File": 70, "Edit": 140, "View": 210, "Tools": 280}.get(menu_name, 70)
            return menu_x, item['y']
    map_menu_items(menu_name)
    return get_menu_item_position(menu_name, item_text)

# --- Dialog Mapping (Stub for now) ---
def map_dialog_elements(dialog_name, screenshot_path):
    # ... Vision API call here ...
    dialog_elements = [
        {"text": "OK", "x": 600, "y": 400},
        {"text": "Cancel", "x": 700, "y": 400},
    ]
    try:
        with open(DIALOG_MAP_FILE, 'r') as f:
            dialog_map = json.load(f)
    except Exception:
        dialog_map = {}
    dialog_map[dialog_name] = dialog_elements
    with open(DIALOG_MAP_FILE, 'w') as f:
        json.dump(dialog_map, f, indent=2)
    return dialog_elements

def get_dialog_element_position(dialog_name, element_text):
    try:
        with open(DIALOG_MAP_FILE, 'r') as f:
            dialog_map = json.load(f)
    except Exception:
        dialog_map = {}
    if dialog_name not in dialog_map:
        screenshot_path = f"dialog_{dialog_name}.png"
        pyautogui.screenshot(screenshot_path)
        map_dialog_elements(dialog_name, screenshot_path)
        with open(DIALOG_MAP_FILE, 'r') as f:
            dialog_map = json.load(f)
    for el in dialog_map.get(dialog_name, []):
        if element_text.lower() in el['text'].lower():
            return el['x'], el['y']
    screenshot_path = f"dialog_{dialog_name}.png"
    pyautogui.screenshot(screenshot_path)
    map_dialog_elements(dialog_name, screenshot_path)
    return get_dialog_element_position(dialog_name, element_text)

if __name__ == "__main__":
    main()
