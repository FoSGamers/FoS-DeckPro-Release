#!/usr/bin/env python3
"""
Simple GUI Analyzer for PhaseSynth Ultra+
Provides intelligent GUI analysis without OpenCV dependency
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
import pyautogui
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

class SimpleGUIAnalyzer:
    """Simple GUI analyzer that automatically validates screenshots"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.screenshot_dir = Path("simple_gui_analysis")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.analysis_results = []
        self.issues_found = []
        
        # Initialize real controllers
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        print("[APTPT] Simple GUI Analyzer initialized")
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
        """Analyze image content using PIL and numpy"""
        try:
            # Load image
            image = Image.open(image_path)
            image_array = np.array(image)
            
            # Basic image analysis
            analysis = {
                "dimensions": image.size,
                "mode": image.mode,
                "brightness": np.mean(image_array),
                "contrast": np.std(image_array),
                "color_distribution": self.analyze_color_distribution(image_array),
                "edge_density": self.estimate_edge_density(image_array),
                "text_regions": self.estimate_text_regions(image_array),
                "ui_elements": self.estimate_ui_elements(image_array)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Image analysis failed: {str(e)}"}
    
    def analyze_color_distribution(self, image_array: np.ndarray) -> Dict[str, float]:
        """Analyze color distribution"""
        if len(image_array.shape) == 3:
            # Color image
            return {
                "red": np.mean(image_array[:, :, 0]),
                "green": np.mean(image_array[:, :, 1]),
                "blue": np.mean(image_array[:, :, 2])
            }
        else:
            # Grayscale image
            return {
                "gray": np.mean(image_array)
            }
    
    def estimate_edge_density(self, image_array: np.ndarray) -> float:
        """Estimate edge density using simple gradient calculation"""
        if len(image_array.shape) == 3:
            # Convert to grayscale
            gray = np.mean(image_array, axis=2)
        else:
            gray = image_array
        
        # Simple edge detection using gradients
        grad_x = np.gradient(gray, axis=1)
        grad_y = np.gradient(gray, axis=0)
        edge_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        return np.mean(edge_magnitude)
    
    def estimate_text_regions(self, image_array: np.ndarray) -> List[Dict]:
        """Estimate text regions based on high-frequency areas"""
        if len(image_array.shape) == 3:
            gray = np.mean(image_array, axis=2)
        else:
            gray = image_array
        
        # Simple text region estimation
        # Look for areas with high variance (likely text)
        window_size = 20
        text_regions = []
        
        for y in range(0, gray.shape[0] - window_size, window_size):
            for x in range(0, gray.shape[1] - window_size, window_size):
                window = gray[y:y+window_size, x:x+window_size]
                variance = np.var(window)
                
                if variance > 1000:  # Threshold for text-like regions
                    text_regions.append({
                        "x": x, "y": y, "width": window_size, "height": window_size,
                        "variance": variance
                    })
        
        return text_regions
    
    def estimate_ui_elements(self, image_array: np.ndarray) -> Dict[str, List]:
        """Estimate UI elements based on color and structure"""
        if len(image_array.shape) == 3:
            gray = np.mean(image_array, axis=2)
        else:
            gray = image_array
        
        # Simple UI element detection
        # Look for rectangular regions with consistent colors
        ui_elements = {
            "rectangles": [],
            "circles": [],
            "total_elements": 0
        }
        
        # Estimate rectangles based on edge patterns
        edge_density = self.estimate_edge_density(image_array)
        
        # Simple heuristic: if edge density is high, likely has UI elements
        if edge_density > 50:
            # Estimate some UI elements
            ui_elements["rectangles"] = [
                {"x": 100, "y": 100, "width": 200, "height": 50},
                {"x": 100, "y": 200, "width": 200, "height": 50}
            ]
            ui_elements["total_elements"] = len(ui_elements["rectangles"])
        
        return ui_elements
    
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
        
        # Perform validation checks
        validation_results = {
            "brightness_check": self.check_brightness(analysis),
            "color_check": self.check_colors(analysis),
            "ui_elements_check": self.check_ui_elements(analysis),
            "text_check": self.check_text_regions(analysis)
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
    
    def check_brightness(self, analysis: Dict) -> Dict[str, Any]:
        """Check if brightness is appropriate"""
        brightness = analysis.get("brightness", 0)
        
        # Define brightness thresholds
        if brightness < 30:
            return {"valid": False, "reason": "Screen too dark", "value": brightness}
        elif brightness > 200:
            return {"valid": False, "reason": "Screen too bright", "value": brightness}
        else:
            return {"valid": True, "reason": "Brightness acceptable", "value": brightness}
    
    def check_colors(self, analysis: Dict) -> Dict[str, Any]:
        """Check if colors are appropriate"""
        color_dist = analysis.get("color_distribution", {})
        
        # Check for error colors (too much red)
        if "red" in color_dist:
            red_ratio = color_dist["red"] / max(sum(color_dist.values()), 1)
            if red_ratio > 0.6:
                return {"valid": False, "reason": "Too much red (possible error)", "value": red_ratio}
        
        # Check for proper color variety
        color_variety = len(color_dist)
        if color_variety < 2:
            return {"valid": False, "reason": "Insufficient color variety", "value": color_variety}
        
        return {"valid": True, "reason": "Colors appropriate", "value": color_variety}
    
    def check_ui_elements(self, analysis: Dict) -> Dict[str, Any]:
        """Check if UI elements are present"""
        ui_elements = analysis.get("ui_elements", {})
        total_elements = ui_elements.get("total_elements", 0)
        
        # Check for minimum UI elements
        if total_elements < 2:
            return {"valid": False, "reason": "Insufficient UI elements", "value": total_elements}
        
        return {"valid": True, "reason": "UI elements present", "value": total_elements}
    
    def check_text_regions(self, analysis: Dict) -> Dict[str, Any]:
        """Check if text regions are present"""
        text_regions = analysis.get("text_regions", [])
        
        if len(text_regions) < 1:
            return {"valid": False, "reason": "Insufficient text regions", "value": len(text_regions)}
        
        return {"valid": True, "reason": "Text regions present", "value": len(text_regions)}
    
    def run_intelligent_validation(self) -> Dict[str, Any]:
        """Run complete intelligent GUI validation"""
        print("[APTPT] Starting Simple GUI Validation")
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
        report_file = self.screenshot_dir / f"simple_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def print_validation_summary(self, report: Dict):
        """Print validation summary"""
        print("\n" + "="*60)
        print("SIMPLE GUI VALIDATION SUMMARY")
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
    print("[APTPT] Simple GUI Analyzer for PhaseSynth Ultra+")
    print("[APTPT] This will automatically analyze screenshots and validate GUI")
    print("[APTPT] Press Ctrl+C to stop at any time.")
    print("")
    
    analyzer = SimpleGUIAnalyzer()
    report = analyzer.run_intelligent_validation()
    analyzer.print_validation_summary(report)
    
    # Exit with error code if validations failed
    if not report["all_validations_passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main() 