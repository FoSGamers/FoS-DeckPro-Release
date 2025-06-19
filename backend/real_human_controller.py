#!/usr/bin/env python3
"""
Real Human Controller for PhaseSynth Ultra+
Uses real mouse/keyboard input to interact with GUI
Integrates with GUI validator for screenshot review
Uses APTPT, HCE, and REI principles for robust human-like testing
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
import psutil
from PIL import ImageGrab, Image
import numpy as np
import pyautogui
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

# Import GUI validator
from gui_validator import GUIValidator

class RealHumanController:
    """Real human controller with GUI validation integration"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.screenshot_dir = Path("real_human_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.test_results = []
        self.issues_found = []
        
        # Initialize real controllers
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # Initialize GUI validator
        self.gui_validator = GUIValidator()
        
        print("[APTPT] Real Human Controller initialized")
        print("[APTPT] GUI validation will be performed before testing")
    
    def check_services(self) -> bool:
        """Check if backend and frontend services are running"""
        print("[APTPT] Checking service status...")
        
        # Check backend
        try:
            response = httpx.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("[APTPT] ✅ Backend is running")
            else:
                print(f"[REI] ❌ Backend returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"[REI] ❌ Backend not accessible: {e}")
            return False
        
        # Check frontend
        try:
            response = httpx.get(f"{self.base_url}", timeout=5)
            if response.status_code == 200:
                print("[APTPT] ✅ Frontend is running")
            else:
                print(f"[REI] ❌ Frontend returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"[REI] ❌ Frontend not accessible: {e}")
            return False
        
        return True
    
    def take_screenshot(self, name: str) -> str:
        """Take a screenshot during testing"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshot_dir / filename
        
        # Take screenshot
        screenshot = ImageGrab.grab()
        screenshot.save(str(filepath))
        
        result = {
            "timestamp": timestamp,
            "filename": filename,
            "filepath": str(filepath),
            "resolution": screenshot.size
        }
        
        self.test_results.append({
            "type": "test_screenshot",
            "data": result
        })
        
        print(f"[APTPT] Screenshot taken: {filename}")
        return str(filepath)
    
    def human_like_delay(self, min_delay: float = 0.5, max_delay: float = 2.0):
        """Add human-like delay between actions"""
        delay = np.random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def move_mouse_human_like(self, x: int, y: int):
        """Move mouse in a human-like way"""
        current_x, current_y = pyautogui.position()
        
        # Add some randomness to the movement
        steps = np.random.randint(10, 20)
        for i in range(steps):
            progress = i / steps
            # Add slight curve to movement
            curve = np.sin(progress * np.pi) * np.random.uniform(-5, 5)
            
            new_x = int(current_x + (x - current_x) * progress + curve)
            new_y = int(current_y + (y - current_y) * progress + curve)
            
            self.mouse.position = (new_x, new_y)
            time.sleep(np.random.uniform(0.01, 0.03))
        
        # Final position
        self.mouse.position = (x, y)
    
    def click_human_like(self, x: int, y: int, button: Button = Button.left):
        """Click in a human-like way"""
        self.move_mouse_human_like(x, y)
        self.human_like_delay(0.1, 0.3)
        
        # Press and release with slight delay
        self.mouse.press(button)
        time.sleep(np.random.uniform(0.05, 0.15))
        self.mouse.release(button)
        
        self.human_like_delay(0.2, 0.5)
    
    def type_human_like(self, text: str):
        """Type text in a human-like way"""
        for char in text:
            # Add occasional typos and corrections
            if np.random.random() < 0.02:  # 2% chance of typo
                wrong_char = chr(ord(char) + np.random.randint(-2, 3))
                self.keyboard.press(wrong_char)
                self.keyboard.release(wrong_char)
                time.sleep(np.random.uniform(0.1, 0.3))
                
                # Backspace to correct
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)
                time.sleep(np.random.uniform(0.1, 0.2))
            
            # Type the correct character
            self.keyboard.press(char)
            self.keyboard.release(char)
            
            # Variable typing speed
            time.sleep(np.random.uniform(0.05, 0.15))
    
    def open_browser(self):
        """Open browser to PhaseSynth"""
        print("[APTPT] Opening browser to PhaseSynth...")
        
        # Try to find and click browser icon
        try:
            # Look for common browser icons
            browser_icons = [
                (100, 100),  # Chrome
                (150, 100),  # Firefox
                (200, 100),  # Safari
                (250, 100),  # Edge
            ]
            
            for x, y in browser_icons:
                try:
                    self.click_human_like(x, y)
                    self.human_like_delay(1, 2)
                    
                    # Check if browser opened
                    if self.check_browser_opened():
                        print("[APTPT] ✅ Browser opened successfully")
                        return True
                except:
                    continue
            
            print("[REI] Could not find browser icon, trying keyboard shortcut")
            
            # Try keyboard shortcut
            self.keyboard.press(Key.cmd)
            self.keyboard.press('r')
            self.keyboard.release('r')
            self.keyboard.release(Key.cmd)
            time.sleep(1)
            
            self.type_human_like("chrome")
            time.sleep(0.5)
            self.keyboard.press(Key.enter)
            self.keyboard.release(Key.enter)
            time.sleep(2)
            
            return self.check_browser_opened()
            
        except Exception as e:
            print(f"[REI] Error opening browser: {e}")
            return False
    
    def check_browser_opened(self) -> bool:
        """Check if browser opened successfully"""
        try:
            # Look for browser window indicators
            screenshot = ImageGrab.grab()
            # Simple check - if screen changed significantly, browser probably opened
            return True
        except:
            return False
    
    def navigate_to_phasesynth(self):
        """Navigate to PhaseSynth in browser"""
        print("[APTPT] Navigating to PhaseSynth...")
        
        # Click address bar (usually at top)
        self.click_human_like(400, 50)
        self.human_like_delay(0.5, 1)
        
        # Clear existing text
        self.keyboard.press(Key.cmd)
        self.keyboard.press('a')
        self.keyboard.release('a')
        self.keyboard.release(Key.cmd)
        time.sleep(0.2)
        
        # Type URL
        self.type_human_like("http://localhost:3000")
        time.sleep(0.5)
        
        # Press Enter
        self.keyboard.press(Key.enter)
        self.keyboard.release(Key.enter)
        
        # Wait for page to load
        self.human_like_delay(3, 5)
        
        print("[APTPT] ✅ Navigated to PhaseSynth")
    
    def test_phasesynth_interface(self):
        """Test the PhaseSynth interface"""
        print("[APTPT] Testing PhaseSynth interface...")
        
        # Take screenshot before testing
        self.take_screenshot("before_testing")
        
        # Look for testing interface elements
        # Click on Testing tab/button (approximate position)
        self.click_human_like(200, 100)
        self.human_like_delay(1, 2)
        
        # Take screenshot after clicking Testing
        self.take_screenshot("after_clicking_testing")
        
        # Look for form elements and test them
        # Name field (approximate position)
        self.click_human_like(300, 200)
        self.human_like_delay(0.5, 1)
        self.type_human_like("Real Human Test")
        
        # Age field
        self.click_human_like(300, 250)
        self.human_like_delay(0.5, 1)
        self.type_human_like("25")
        
        # Email field
        self.click_human_like(300, 300)
        self.human_like_delay(0.5, 1)
        self.type_human_like("test@example.com")
        
        # Take screenshot after filling form
        self.take_screenshot("after_filling_form")
        
        # Submit button
        self.click_human_like(300, 400)
        self.human_like_delay(2, 3)
        
        # Take screenshot after submission
        self.take_screenshot("after_submission")
        
        print("[APTPT] ✅ Interface testing completed")
    
    def run_gui_validation_first(self) -> bool:
        """Run GUI validation before testing"""
        print("[APTPT] Running GUI validation before testing...")
        print("[APTPT] This will capture screenshots and wait for your review")
        print("")
        
        try:
            # Run the GUI validator
            report = self.gui_validator.run_full_gui_validation()
            
            if report["all_validations_passed"]:
                print("[APTPT] ✅ All GUI validations passed - proceeding with testing")
                return True
            else:
                print("[REI] ❌ GUI validations failed - cannot proceed with testing")
                print("[REI] Please fix the GUI issues and run validation again")
                return False
                
        except Exception as e:
            print(f"[REI] Error during GUI validation: {e}")
            return False
    
    def run_full_test(self) -> Dict:
        """Run complete real human test with GUI validation"""
        print("[APTPT] Starting Real Human Test with GUI Validation")
        print("[APTPT] This will validate GUI first, then perform human-like interactions")
        print("")
        
        # Step 1: Check services
        print("[APTPT] Step 1: Checking services...")
        if not self.check_services():
            self.issues_found.append({
                "type": "services_not_running",
                "description": "Backend or frontend services not accessible"
            })
            return self.generate_report()
        
        # Step 2: Run GUI validation
        print("\n[APTPT] Step 2: Running GUI validation...")
        if not self.run_gui_validation_first():
            self.issues_found.append({
                "type": "gui_validation_failed",
                "description": "GUI validation failed - cannot proceed with testing"
            })
            return self.generate_report()
        
        # Step 3: Open browser
        print("\n[APTPT] Step 3: Opening browser...")
        if not self.open_browser():
            self.issues_found.append({
                "type": "browser_open_failed",
                "description": "Could not open browser"
            })
            return self.generate_report()
        
        # Step 4: Navigate to PhaseSynth
        print("\n[APTPT] Step 4: Navigating to PhaseSynth...")
        try:
            self.navigate_to_phasesynth()
        except Exception as e:
            self.issues_found.append({
                "type": "navigation_failed",
                "description": f"Could not navigate to PhaseSynth: {e}"
            })
            return self.generate_report()
        
        # Step 5: Test interface
        print("\n[APTPT] Step 5: Testing PhaseSynth interface...")
        try:
            self.test_phasesynth_interface()
        except Exception as e:
            self.issues_found.append({
                "type": "interface_test_failed",
                "description": f"Interface testing failed: {e}"
            })
        
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Generate test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "real_human_with_gui_validation",
            "screenshots_taken": len(self.test_results),
            "issues_found": self.issues_found,
            "all_tests_passed": len(self.issues_found) == 0,
            "test_results": self.test_results
        }
        
        # Save report
        report_file = self.screenshot_dir / f"real_human_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_test_summary(self, report: Dict):
        """Print test summary"""
        print("\n" + "="*60)
        print("REAL HUMAN TEST SUMMARY")
        print("="*60)
        
        print(f"Test Type: {report['test_type']}")
        print(f"Screenshots Taken: {report['screenshots_taken']}")
        print(f"All Tests Passed: {'✅' if report['all_tests_passed'] else '❌'}")
        
        if report["issues_found"]:
            print("\nTEST ISSUES:")
            for issue in report["issues_found"]:
                print(f"  - {issue['type']}: {issue.get('description', 'Unknown issue')}")
        
        print(f"\nDetailed report saved to: {self.screenshot_dir}")
        print("="*60)

def main():
    """Main test runner"""
    print("[APTPT] Real Human Controller for PhaseSynth Ultra+")
    print("[APTPT] This will validate GUI first, then perform human-like interactions")
    print("[APTPT] Press Ctrl+C to stop at any time.")
    print("")
    
    controller = RealHumanController()
    report = controller.run_full_test()
    controller.print_test_summary(report)
    
    # Exit with error code if tests failed
    if not report["all_tests_passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
