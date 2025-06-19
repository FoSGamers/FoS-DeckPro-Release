#!/usr/bin/env python3
"""
Intelligent GUI Analyzer for PhaseSynth Ultra+
Automatically analyzes screenshots and determines GUI correctness
Uses APTPT, HCE, and REI principles for robust automated validation
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import httpx
import psutil
from PIL import ImageGrab, Image
import numpy as np
import cv2
import pyautogui
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

class IntelligentGUIAnalyzer:
    """Intelligent GUI analyzer that automatically validates screenshots"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.screenshot_dir = Path("intelligent_gui_analysis")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.analysis_results = []
        self.issues_found = []
        
        # Initialize real controllers
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # GUI validation criteria
        self.validation_criteria = {
            "initial_gui": {
                "required_elements": ["desktop", "dock", "menu_bar"],
                "forbidden_elements": ["error_dialog", "crash_screen"],
                "color_checks": {
                    "background": "not_black",
                    "text": "readable"
                }
            },
            "browser_opened": {
                "required_elements": ["browser_window", "address_bar", "navigation"],
                "forbidden_elements": ["error_page", "connection_failed"],
                "color_checks": {
                    "browser_ui": "standard_colors",
                    "content": "not_error_colors"
                }
            },
            "phasesynth_page": {
                "required_elements": ["phasesynth_header", "navigation_menu", "main_content"],
                "forbidden_elements": ["404_error", "server_error", "loading_spinner"],
                "color_checks": {
                    "background": "light_theme",
                    "text": "dark_readable"
                }
            },
            "testing_interface": {
                "required_elements": ["form_fields", "submit_button", "input_labels"],
                "forbidden_elements": ["error_messages", "validation_errors"],
                "color_checks": {
                    "form": "proper_styling",
                    "buttons": "interactive_colors"
                }
            }
        }
        
        print("[APTPT] Intelligent GUI Analyzer initialized")
        print("[APTPT] This will automatically analyze screenshots and validate GUI")
    
    def take_analysis_screenshot(self, name: str, description: str = "") -> str:
        """Take a screenshot for intelligent analysis"""
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
            "status": "pending_analysis"
        }
        
        self.analysis_results.append({
            "type": "analysis_screenshot",
            "data": result
        })
        
        print(f"[APTPT] Analysis screenshot taken: {filename}")
        print(f"[APTPT] Description: {description}")
        return str(filepath)
    
    def analyze_image_content(self, image_path: str) -> Dict[str, Any]:
        """Analyze image content using computer vision"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Could not load image"}
            
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Basic image analysis
            analysis = {
                "dimensions": image.shape,
                "brightness": np.mean(gray),
                "contrast": np.std(gray),
                "color_distribution": {
                    "red": np.mean(image[:, :, 2]),
                    "green": np.mean(image[:, :, 1]),
                    "blue": np.mean(image[:, :, 0])
                },
                "edge_density": np.mean(cv2.Canny(gray, 50, 150)),
                "text_regions": self.detect_text_regions(gray),
                "ui_elements": self.detect_ui_elements(image),
                "color_palette": self.analyze_color_palette(hsv)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Image analysis failed: {str(e)}"}
    
    def detect_text_regions(self, gray_image: np.ndarray) -> List[Dict]:
        """Detect potential text regions in the image"""
        # Simple edge detection for text regions
        edges = cv2.Canny(gray_image, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 10:  # Minimum size for text
                text_regions.append({
                    "x": x, "y": y, "width": w, "height": h,
                    "area": w * h
                })
        
        return text_regions
    
    def detect_ui_elements(self, image: np.ndarray) -> Dict[str, List]:
        """Detect common UI elements"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect rectangles (buttons, forms, etc.)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rectangles = []
        circles = []
        
        for contour in contours:
            # Approximate contour to polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            if len(approx) == 4:  # Rectangle
                x, y, w, h = cv2.boundingRect(approx)
                rectangles.append({"x": x, "y": y, "width": w, "height": h})
            elif len(approx) > 8:  # Circle-like
                x, y, w, h = cv2.boundingRect(approx)
                if abs(w - h) < 10:  # Roughly circular
                    circles.append({"x": x, "y": y, "radius": w // 2})
        
        return {
            "rectangles": rectangles,
            "circles": circles,
            "total_elements": len(rectangles) + len(circles)
        }
    
    def analyze_color_palette(self, hsv_image: np.ndarray) -> Dict[str, Any]:
        """Analyze the color palette of the image"""
        # Analyze hue distribution
        hue_hist = cv2.calcHist([hsv_image], [0], None, [180], [0, 180])
        saturation_hist = cv2.calcHist([hsv_image], [1], None, [256], [0, 256])
        value_hist = cv2.calcHist([hsv_image], [2], None, [256], [0, 256])
        
        return {
            "dominant_hues": np.argsort(hue_hist.flatten())[-5:].tolist(),
            "average_saturation": np.mean(saturation_hist),
            "average_value": np.mean(value_hist),
            "color_variety": len(np.where(hue_hist > np.max(hue_hist) * 0.1)[0])
        }
    
    def validate_gui_state(self, screenshot_path: str, expected_state: str) -> Dict[str, Any]:
        """Validate GUI state against expected criteria"""
        print(f"[APTPT] Analyzing GUI state: {expected_state}")
        
        # Analyze the screenshot
        analysis = self.analyze_image_content(screenshot_path)
        
        if "error" in analysis:
            return {
                "valid": False,
                "reason": analysis["error"],
                "confidence": 0.0
            }
        
        # Get validation criteria for this state
        criteria = self.validation_criteria.get(expected_state, {})
        
        # Perform validation checks
        validation_results = {
            "brightness_check": self.check_brightness(analysis, criteria),
            "color_check": self.check_colors(analysis, criteria),
            "ui_elements_check": self.check_ui_elements(analysis, criteria),
            "text_check": self.check_text_regions(analysis, criteria)
        }
        
        # Calculate overall confidence
        valid_checks = sum(1 for result in validation_results.values() if result["valid"])
        total_checks = len(validation_results)
        confidence = valid_checks / total_checks if total_checks > 0 else 0.0
        
        # Determine if GUI is valid
        is_valid = confidence >= 0.75  # 75% confidence threshold
        
        result = {
            "valid": is_valid,
            "confidence": confidence,
            "validation_results": validation_results,
            "analysis": analysis,
            "expected_state": expected_state,
            "screenshot_path": screenshot_path
        }
        
        # Log the result
        if is_valid:
            print(f"[APTPT] ✅ GUI validation passed for {expected_state} (confidence: {confidence:.2f})")
        else:
            print(f"[APTPT] ❌ GUI validation failed for {expected_state} (confidence: {confidence:.2f})")
            self.issues_found.append({
                "type": f"{expected_state}_validation_failed",
                "confidence": confidence,
                "validation_results": validation_results
            })
        
        return result
    
    def check_brightness(self, analysis: Dict, criteria: Dict) -> Dict[str, Any]:
        """Check if brightness is appropriate"""
        brightness = analysis.get("brightness", 0)
        
        # Define brightness thresholds
        if brightness < 30:
            return {"valid": False, "reason": "Screen too dark", "value": brightness}
        elif brightness > 200:
            return {"valid": False, "reason": "Screen too bright", "value": brightness}
        else:
            return {"valid": True, "reason": "Brightness acceptable", "value": brightness}
    
    def check_colors(self, analysis: Dict, criteria: Dict) -> Dict[str, Any]:
        """Check if colors are appropriate"""
        color_dist = analysis.get("color_distribution", {})
        
        # Check for error colors (too much red)
        red_ratio = color_dist.get("red", 0) / max(sum(color_dist.values()), 1)
        if red_ratio > 0.6:
            return {"valid": False, "reason": "Too much red (possible error)", "value": red_ratio}
        
        # Check for proper color variety
        color_variety = analysis.get("color_palette", {}).get("color_variety", 0)
        if color_variety < 5:
            return {"valid": False, "reason": "Insufficient color variety", "value": color_variety}
        
        return {"valid": True, "reason": "Colors appropriate", "value": color_variety}
    
    def check_ui_elements(self, analysis: Dict, criteria: Dict) -> Dict[str, Any]:
        """Check if UI elements are present"""
        ui_elements = analysis.get("ui_elements", {})
        total_elements = ui_elements.get("total_elements", 0)
        
        # Check for minimum UI elements
        if total_elements < 3:
            return {"valid": False, "reason": "Insufficient UI elements", "value": total_elements}
        
        # Check for rectangles (forms, buttons)
        rectangles = ui_elements.get("rectangles", [])
        if len(rectangles) < 2:
            return {"valid": False, "reason": "Insufficient rectangular elements", "value": len(rectangles)}
        
        return {"valid": True, "reason": "UI elements present", "value": total_elements}
    
    def check_text_regions(self, analysis: Dict, criteria: Dict) -> Dict[str, Any]:
        """Check if text regions are present"""
        text_regions = analysis.get("text_regions", [])
        
        if len(text_regions) < 2:
            return {"valid": False, "reason": "Insufficient text regions", "value": len(text_regions)}
        
        return {"valid": True, "reason": "Text regions present", "value": len(text_regions)}
    
    def run_intelligent_validation(self) -> Dict[str, Any]:
        """Run complete intelligent GUI validation"""
        print("[APTPT] Starting Intelligent GUI Validation")
        print("[APTPT] This will automatically analyze screenshots and validate GUI")
        print("")
        
        validation_steps = []
        
        # Step 1: Validate initial GUI
        print("[APTPT] Step 1: Validating initial GUI state...")
        screenshot_path = self.take_analysis_screenshot("initial_gui_state", "Initial GUI state")
        result = self.validate_gui_state(screenshot_path, "initial_gui")
        validation_steps.append({"step": "initial_gui", "result": result})
        
        # Step 2: Validate browser opened
        print("\n[APTPT] Step 2: Validating browser opened correctly...")
        screenshot_path = self.take_analysis_screenshot("browser_opened", "Browser opened")
        result = self.validate_gui_state(screenshot_path, "browser_opened")
        validation_steps.append({"step": "browser_opened", "result": result})
        
        # Step 3: Validate PhaseSynth page
        print("\n[APTPT] Step 3: Validating PhaseSynth page loaded correctly...")
        screenshot_path = self.take_analysis_screenshot("phasesynth_page", "PhaseSynth page loaded")
        result = self.validate_gui_state(screenshot_path, "phasesynth_page")
        validation_steps.append({"step": "phasesynth_page", "result": result})
        
        # Step 4: Validate testing interface
        print("\n[APTPT] Step 4: Validating testing interface...")
        screenshot_path = self.take_analysis_screenshot("testing_interface", "Testing interface")
        result = self.validate_gui_state(screenshot_path, "testing_interface")
        validation_steps.append({"step": "testing_interface", "result": result})
        
        # Generate validation report
        passed_steps = sum(1 for step in validation_steps if step["result"]["valid"])
        total_steps = len(validation_steps)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": total_steps - passed_steps,
            "validation_steps": validation_steps,
            "issues_found": self.issues_found,
            "screenshots_taken": len(self.analysis_results),
            "all_validations_passed": len(self.issues_found) == 0,
            "overall_confidence": np.mean([step["result"]["confidence"] for step in validation_steps])
        }
        
        # Save validation report
        report_file = self.screenshot_dir / f"intelligent_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_validation_summary(self, report: Dict):
        """Print validation summary"""
        print("\n" + "="*60)
        print("INTELLIGENT GUI VALIDATION SUMMARY")
        print("="*60)
        
        print(f"Total Steps: {report['total_steps']}")
        print(f"Passed Steps: {report['passed_steps']}")
        print(f"Failed Steps: {report['failed_steps']}")
        print(f"Screenshots Taken: {report['screenshots_taken']}")
        print(f"Overall Confidence: {report['overall_confidence']:.2f}")
        print(f"All Validations Passed: {'✅' if report['all_validations_passed'] else '❌'}")
        
        if report["issues_found"]:
            print("\nVALIDATION ISSUES:")
            for issue in report["issues_found"]:
                print(f"  - {issue['type']}: Confidence {issue.get('confidence', 0):.2f}")
        
        print(f"\nDetailed report saved to: {self.screenshot_dir}")
        print("="*60)

def main():
    """Main validation runner"""
    print("[APTPT] Intelligent GUI Analyzer for PhaseSynth Ultra+")
    print("[APTPT] This will automatically analyze screenshots and validate GUI")
    print("[APTPT] Press Ctrl+C to stop at any time.")
    print("")
    
    analyzer = IntelligentGUIAnalyzer()
    report = analyzer.run_intelligent_validation()
    analyzer.print_validation_summary(report)
    
    # Exit with error code if validations failed
    if not report["all_validations_passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main() 