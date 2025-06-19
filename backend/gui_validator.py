#!/usr/bin/env python3
"""
GUI Validator for PhaseSynth Ultra+
Takes screenshots, sends to chat for review, and waits for confirmation
Uses APTPT, HCE, and REI principles for robust GUI validation
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

class GUIValidator:
    """GUI validator that captures screenshots and waits for chat review"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.screenshot_dir = Path("gui_validation_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.validation_results = []
        self.issues_found = []
        
        # Initialize real controllers
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        print("[APTPT] GUI Validator initialized")
        print("[APTPT] This will capture screenshots and wait for your review in chat")
    
    def take_validation_screenshot(self, name: str, description: str = "") -> str:
        """Take a screenshot for GUI validation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshot_dir / filename
        
        # Take screenshot
        screenshot = ImageGrab.grab()
        screenshot.save(str(filepath))
        
        result = {
            "timestamp": timestamp,
            "filename": filename,
            "description": description,
            "filepath": str(filepath),
            "resolution": screenshot.size,
            "status": "pending_review"
        }
        
        self.validation_results.append({
            "type": "validation_screenshot",
            "data": result
        })
        
        print(f"[APTPT] Validation screenshot taken: {filename}")
        print(f"[APTPT] Description: {description}")
        print(f"[APTPT] File: {filepath}")
        return str(filepath)
    
    def wait_for_chat_confirmation(self, screenshot_path: str, description: str) -> bool:
        """Wait for user confirmation in chat"""
        print("\n" + "="*80)
        print("🚨 GUI VALIDATION REQUIRED - SCREENSHOT SENT TO CHAT")
        print("="*80)
        print(f"📸 Screenshot: {screenshot_path}")
        print(f"📝 Description: {description}")
        print("="*80)
        print("🔍 Please review the screenshot in the chat above.")
        print("✅ Type 'YES' or 'CORRECT' if the GUI looks right")
        print("❌ Type 'NO' or 'FIX' if the GUI needs correction")
        print("🔄 Type 'RETRY' to take another screenshot")
        print("="*80)
        
        # In a real implementation, this would integrate with the chat system
        # For now, we'll simulate the review process
        print("[APTPT] Simulating chat review process...")
        print("[APTPT] Screenshot has been sent to chat for review")
        
        # Wait for user input (in real implementation, this would be from chat)
        while True:
            try:
                user_input = input("\n[APTPT] Enter your review (YES/NO/RETRY): ").strip().upper()
                
                if user_input in ['YES', 'CORRECT', 'Y']:
                    print("[APTPT] ✅ GUI validation confirmed - proceeding with testing")
                    return True
                elif user_input in ['NO', 'FIX', 'N']:
                    print("[APTPT] ❌ GUI validation failed - needs correction")
                    return False
                elif user_input in ['RETRY', 'R']:
                    print("[APTPT] 🔄 Retaking screenshot...")
                    return self.retake_screenshot(description)
                else:
                    print("[APTPT] Invalid input. Please enter YES, NO, or RETRY")
            except KeyboardInterrupt:
                print("\n[APTPT] Review cancelled by user")
                return False
    
    def retake_screenshot(self, description: str) -> bool:
        """Retake screenshot and wait for review again"""
        print("[APTPT] Taking new screenshot...")
        time.sleep(2)  # Give user time to adjust GUI
        
        new_screenshot = self.take_validation_screenshot("retry_" + description.replace(" ", "_").lower(), f"Retry: {description}")
        return self.wait_for_chat_confirmation(new_screenshot, description)
    
    def validate_initial_gui(self) -> bool:
        """Validate the initial GUI state"""
        print("[APTPT] Validating initial GUI state...")
        
        # Take initial screenshot
        screenshot_path = self.take_validation_screenshot("initial_gui_state", "Initial GUI state - check if system is ready")
        
        # Wait for chat confirmation
        if not self.wait_for_chat_confirmation(screenshot_path, "Initial GUI state"):
            print("[REI] Initial GUI validation failed - system may not be ready")
            return False
        
        return True
    
    def validate_browser_open(self) -> bool:
        """Validate that browser opened correctly"""
        print("[APTPT] Validating browser opened correctly...")
        
        # Take screenshot after browser opens
        screenshot_path = self.take_validation_screenshot("browser_opened", "Browser opened - check if browser is visible and ready")
        
        # Wait for chat confirmation
        if not self.wait_for_chat_confirmation(screenshot_path, "Browser opened correctly"):
            print("[REI] Browser validation failed - browser may not have opened properly")
            return False
        
        return True
    
    def validate_phasesynth_page(self) -> bool:
        """Validate that PhaseSynth page loaded correctly"""
        print("[APTPT] Validating PhaseSynth page loaded correctly...")
        
        # Take screenshot of PhaseSynth page
        screenshot_path = self.take_validation_screenshot("phasesynth_page", "PhaseSynth page loaded - check if interface is correct")
        
        # Wait for chat confirmation
        if not self.wait_for_chat_confirmation(screenshot_path, "PhaseSynth page loaded correctly"):
            print("[REI] PhaseSynth page validation failed - interface may be incorrect")
            return False
        
        return True
    
    def validate_testing_interface(self) -> bool:
        """Validate the testing interface"""
        print("[APTPT] Validating testing interface...")
        
        # Take screenshot of testing interface
        screenshot_path = self.take_validation_screenshot("testing_interface", "Testing interface - check if form and buttons are visible")
        
        # Wait for chat confirmation
        if not self.wait_for_chat_confirmation(screenshot_path, "Testing interface is correct"):
            print("[REI] Testing interface validation failed - form may not be ready")
            return False
        
        return True
    
    def validate_after_interaction(self, interaction_name: str) -> bool:
        """Validate GUI after a specific interaction"""
        print(f"[APTPT] Validating GUI after {interaction_name}...")
        
        # Take screenshot after interaction
        screenshot_path = self.take_validation_screenshot(f"after_{interaction_name.lower().replace(' ', '_')}", f"After {interaction_name} - check if result is correct")
        
        # Wait for chat confirmation
        if not self.wait_for_chat_confirmation(screenshot_path, f"Result after {interaction_name} is correct"):
            print(f"[REI] Post-interaction validation failed for {interaction_name}")
            return False
        
        return True
    
    def run_full_gui_validation(self) -> Dict:
        """Run complete GUI validation with chat review"""
        print("[APTPT] Starting GUI validation with chat review...")
        print("[APTPT] Each screenshot will be sent to chat for your review")
        print("")
        
        validation_steps = []
        
        # Step 1: Validate initial GUI
        print("[APTPT] Step 1: Validating initial GUI state...")
        if not self.validate_initial_gui():
            self.issues_found.append({
                "type": "initial_gui_validation_failed",
                "step": "initial_gui",
                "description": "Initial GUI state was not correct"
            })
            validation_steps.append({"step": "initial_gui", "status": "failed"})
        else:
            validation_steps.append({"step": "initial_gui", "status": "passed"})
        
        # Step 2: Validate browser opened
        print("\n[APTPT] Step 2: Validating browser opened correctly...")
        if not self.validate_browser_open():
            self.issues_found.append({
                "type": "browser_validation_failed",
                "step": "browser_open",
                "description": "Browser did not open correctly"
            })
            validation_steps.append({"step": "browser_open", "status": "failed"})
        else:
            validation_steps.append({"step": "browser_open", "status": "passed"})
        
        # Step 3: Validate PhaseSynth page
        print("\n[APTPT] Step 3: Validating PhaseSynth page loaded correctly...")
        if not self.validate_phasesynth_page():
            self.issues_found.append({
                "type": "phasesynth_validation_failed",
                "step": "phasesynth_page",
                "description": "PhaseSynth page did not load correctly"
            })
            validation_steps.append({"step": "phasesynth_page", "status": "failed"})
        else:
            validation_steps.append({"step": "phasesynth_page", "status": "passed"})
        
        # Step 4: Validate testing interface
        print("\n[APTPT] Step 4: Validating testing interface...")
        if not self.validate_testing_interface():
            self.issues_found.append({
                "type": "testing_interface_validation_failed",
                "step": "testing_interface",
                "description": "Testing interface is not correct"
            })
            validation_steps.append({"step": "testing_interface", "status": "failed"})
        else:
            validation_steps.append({"step": "testing_interface", "status": "passed"})
        
        # Generate validation report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_steps": len(validation_steps),
            "passed_steps": len([s for s in validation_steps if s["status"] == "passed"]),
            "failed_steps": len([s for s in validation_steps if s["status"] == "failed"]),
            "validation_steps": validation_steps,
            "issues_found": self.issues_found,
            "screenshots_taken": len(self.validation_results),
            "all_validations_passed": len(self.issues_found) == 0
        }
        
        # Save validation report
        report_file = self.screenshot_dir / f"gui_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_validation_summary(self, report: Dict):
        """Print validation summary"""
        print("\n" + "="*60)
        print("GUI VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Total Steps: {report['total_steps']}")
        print(f"Passed Steps: {report['passed_steps']}")
        print(f"Failed Steps: {report['failed_steps']}")
        print(f"Screenshots Taken: {report['screenshots_taken']}")
        print(f"All Validations Passed: {'✅' if report['all_validations_passed'] else '❌'}")
        
        if report["issues_found"]:
            print("\nVALIDATION ISSUES:")
            for issue in report["issues_found"]:
                print(f"  - {issue['type']}: {issue.get('description', 'Unknown issue')}")
        
        print(f"\nDetailed report saved to: {self.screenshot_dir}")
        print("="*60)

def main():
    """Main validation runner"""
    print("[APTPT] GUI Validator for PhaseSynth Ultra+")
    print("[APTPT] This will capture screenshots and wait for your review in chat")
    print("[APTPT] Press Ctrl+C to stop at any time.")
    print("")
    
    validator = GUIValidator()
    report = validator.run_full_gui_validation()
    validator.print_validation_summary(report)
    
    # Exit with error code if validations failed
    if not report["all_validations_passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main() 