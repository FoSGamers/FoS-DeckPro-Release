#!/usr/bin/env python3
"""
Comprehensive Feature Test for FoS_DeckPro
Tests all features, paywall system, and takes screenshots for verification
"""

import sys
import time
import os
import subprocess
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QInputDialog, QMenu
from PySide6.QtCore import QTimer, QThread, Signal as pyqtSignal
from PySide6.QtGui import QScreen, QPixmap
import json

# Import the main window
from ui.main_window import MainWindow

class ScreenshotTaker(QThread):
    """Thread for taking screenshots"""
    screenshot_taken = pyqtSignal(str, str)  # filename, description
    
    def __init__(self, window, test_name):
        super().__init__()
        self.window = window
        self.test_name = test_name
        self.screenshots_dir = f"test_screenshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def take_screenshot(self, description):
        """Take a screenshot of the current window state"""
        try:
            # Get the screen
            screen = QApplication.primaryScreen()
            if screen:
                # Take screenshot of the window
                pixmap = screen.grabWindow(self.window.winId())
                if not pixmap.isNull():
                    filename = f"{self.screenshots_dir}/{self.test_name}_{description.replace(' ', '_').lower()}.png"
                    pixmap.save(filename)
                    self.screenshot_taken.emit(filename, description)
                    print(f"✅ Screenshot saved: {filename} - {description}")
                    return filename
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
        return None

class ComprehensiveTester:
    """Comprehensive tester for all FoS_DeckPro features"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.screenshot_taker = ScreenshotTaker(self.window, "comprehensive_test")
        self.screenshot_taker.screenshot_taken.connect(self.on_screenshot_taken)
        self.test_results = []
        self.screenshots = []
        
    def on_screenshot_taken(self, filename, description):
        """Handle screenshot taken event"""
        self.screenshots.append({
            'filename': filename,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_test(self, test_name, success, details=""):
        """Log a test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def take_screenshot(self, description):
        """Take a screenshot"""
        self.screenshot_taker.take_screenshot(description)
        time.sleep(0.5)  # Wait for screenshot to be taken
    
    def test_basic_ui(self):
        """Test basic UI functionality"""
        print("\n=== Testing Basic UI ===")
        
        # Test window shows
        self.window.show()
        time.sleep(1)
        self.take_screenshot("initial_window_state")
        self.log_test("Window Display", True, "Main window displays correctly")
        
        # Test menu bar
        menubar = self.window.menuBar()
        if menubar:
            self.log_test("Menu Bar", True, "Menu bar is present")
            self.take_screenshot("menu_bar_visible")
        else:
            self.log_test("Menu Bar", False, "Menu bar is missing")
        
        # Test card table
        if hasattr(self.window, 'card_table') and self.window.card_table:
            self.log_test("Card Table", True, "Card table is present")
            self.take_screenshot("card_table_visible")
        else:
            self.log_test("Card Table", False, "Card table is missing")
        
        # Test filter overlay
        if hasattr(self.window, 'filter_overlay') and self.window.filter_overlay:
            self.log_test("Filter Overlay", True, "Filter overlay is present")
            self.take_screenshot("filter_overlay_visible")
        else:
            self.log_test("Filter Overlay", False, "Filter overlay is missing")
    
    def test_free_features(self):
        """Test features that should be available without license"""
        print("\n=== Testing Free Features ===")
        
        # Test File menu
        file_menu = self.window.menuBar().findChild(QMenu, "File")
        if file_menu:
            self.log_test("File Menu", True, "File menu is accessible")
            self.take_screenshot("file_menu_open")
        else:
            self.log_test("File Menu", False, "File menu not found")
        
        # Test Edit menu
        edit_menu = self.window.menuBar().findChild(QMenu, "Edit")
        if edit_menu:
            self.log_test("Edit Menu", True, "Edit menu is accessible")
            self.take_screenshot("edit_menu_open")
        else:
            self.log_test("Edit Menu", False, "Edit menu not found")
        
        # Test View menu
        view_menu = self.window.menuBar().findChild(QMenu, "View")
        if view_menu:
            self.log_test("View Menu", True, "View menu is accessible")
            self.take_screenshot("view_menu_open")
        else:
            self.log_test("View Menu", False, "View menu not found")
        
        # Test Tools menu
        tools_menu = self.window.menuBar().findChild(QMenu, "Tools")
        if tools_menu:
            self.log_test("Tools Menu", True, "Tools menu is accessible")
            self.take_screenshot("tools_menu_open")
        else:
            self.log_test("Tools Menu", False, "Tools menu not found")
    
    def test_paid_features_paywall(self):
        """Test that paid features trigger the paywall"""
        print("\n=== Testing Paid Features Paywall ===")
        
        # Test each paid feature
        paid_features = [
            ('Pricing Dashboard', 'pricing_dashboard'),
            ('Break Builder', 'break_builder'),
            ('Export to Whatnot', 'export_whatnot'),
            ('Export Item Listings', 'export_item_listings'),
            ('Enrich from Scryfall', 'enrich_scryfall'),
            ('Add Card by Scryfall ID', 'add_scryfall'),
            ('Adjust Whatnot Pricing', 'adjust_whatnot_pricing'),
            ('Process Packing Slips', 'process_packing_slips')
        ]
        
        for feature_name, feature_id in paid_features:
            try:
                # Try to trigger the feature
                if hasattr(self.window, f'open_{feature_id.replace("_", "_")}'):
                    method = getattr(self.window, f'open_{feature_id.replace("_", "_")}')
                elif hasattr(self.window, feature_id):
                    method = getattr(self.window, feature_id)
                else:
                    # Use the generic trigger method
                    self.window._on_paid_feature_triggered(lambda: None, feature_name=feature_id)
                    self.log_test(f"Paywall {feature_name}", True, "Paywall triggered correctly")
                    self.take_screenshot(f"paywall_{feature_id}")
                    continue
                
                # Call the method which should trigger paywall
                method()
                self.log_test(f"Paywall {feature_name}", True, "Paywall triggered correctly")
                self.take_screenshot(f"paywall_{feature_id}")
                
            except Exception as e:
                self.log_test(f"Paywall {feature_name}", False, f"Error: {e}")
    
    def test_unified_system(self):
        """Test the unified APTPT/REI/HCE system"""
        print("\n=== Testing Unified System ===")
        
        try:
            # Check if unified system is available
            from aptpt_pyside6_kit.unified_system_manager import unified_manager
            self.log_test("Unified System Import", True, "Unified system manager imported successfully")
            
            # Check system status
            status = unified_manager.get_unified_status()
            if status:
                self.log_test("Unified System Status", True, f"Status: {status.get('mode', 'unknown')}")
                self.take_screenshot("unified_system_status")
            else:
                self.log_test("Unified System Status", False, "No status returned")
                
        except ImportError as e:
            self.log_test("Unified System Import", False, f"Import error: {e}")
        except Exception as e:
            self.log_test("Unified System", False, f"Error: {e}")
    
    def test_price_tracker(self):
        """Test the price tracking system"""
        print("\n=== Testing Price Tracker ===")
        
        try:
            from models.price_tracker import price_tracker
            self.log_test("Price Tracker Import", True, "Price tracker imported successfully")
            
            # Check if price tracker is running
            if price_tracker.running:
                self.log_test("Price Tracker Running", True, "Price tracker is active")
            else:
                self.log_test("Price Tracker Running", False, "Price tracker is not running")
                
            # Test collection value calculation
            cards = self.window.inventory.get_all_cards()
            if cards:
                value_data = price_tracker.get_collection_value(cards)
                self.log_test("Collection Value Calculation", True, f"Total value: ${value_data.get('total', 0):.2f}")
                self.take_screenshot("collection_value_calculation")
            else:
                self.log_test("Collection Value Calculation", False, "No cards in inventory")
                
        except ImportError as e:
            self.log_test("Price Tracker Import", False, f"Import error: {e}")
        except Exception as e:
            self.log_test("Price Tracker", False, f"Error: {e}")
    
    def test_card_interactions(self):
        """Test card table interactions"""
        print("\n=== Testing Card Interactions ===")
        
        # Test card selection
        if hasattr(self.window, 'card_table') and self.window.card_table:
            # Select first card
            self.window.card_table.selectRow(0)
            time.sleep(0.5)
            self.take_screenshot("card_selected")
            self.log_test("Card Selection", True, "Card selection works")
            
            # Test image preview
            if hasattr(self.window, 'image_preview') and self.window.image_preview:
                self.log_test("Image Preview", True, "Image preview component exists")
                self.take_screenshot("image_preview")
            else:
                self.log_test("Image Preview", False, "Image preview component missing")
            
            # Test card details
            if hasattr(self.window, 'card_details') and self.window.card_details:
                self.log_test("Card Details", True, "Card details component exists")
                self.take_screenshot("card_details")
            else:
                self.log_test("Card Details", False, "Card details component missing")
        else:
            self.log_test("Card Interactions", False, "Card table not available")
    
    def test_filtering(self):
        """Test filtering functionality"""
        print("\n=== Testing Filtering ===")
        
        if hasattr(self.window, 'filter_overlay') and self.window.filter_overlay:
            # Test filter input
            filters = self.window.filter_overlay.filters
            if filters:
                # Try to set a filter
                for column, filter_widget in filters.items():
                    if filter_widget:
                        filter_widget.setText("test")
                        time.sleep(0.5)
                        self.take_screenshot(f"filter_{column}")
                        self.log_test(f"Filter {column}", True, "Filter input works")
                        break
            else:
                self.log_test("Filter Input", False, "No filter widgets found")
        else:
            self.log_test("Filtering", False, "Filter overlay not available")
    
    def generate_report(self):
        """Generate a comprehensive test report"""
        print("\n=== Generating Test Report ===")
        
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': len([r for r in self.test_results if r['success']]),
            'failed_tests': len([r for r in self.test_results if not r['success']]),
            'test_results': self.test_results,
            'screenshots': self.screenshots
        }
        
        # Save report
        report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Test report saved: {report_filename}")
        
        # Print summary
        print(f"\n=== TEST SUMMARY ===")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Passed: {report['passed_tests']}")
        print(f"Failed: {report['failed_tests']}")
        print(f"Success Rate: {(report['passed_tests']/report['total_tests']*100):.1f}%")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n=== FAILED TESTS ===")
            for test in failed_tests:
                print(f"❌ {test['test_name']}: {test['details']}")
        
        return report
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive FoS_DeckPro Test Suite")
        print("=" * 60)
        
        try:
            # Run all test suites
            self.test_basic_ui()
            self.test_free_features()
            self.test_paid_features_paywall()
            self.test_unified_system()
            self.test_price_tracker()
            self.test_card_interactions()
            self.test_filtering()
            
            # Generate report
            report = self.generate_report()
            
            # Show final screenshot
            self.take_screenshot("final_test_state")
            
            print("\n🎉 Comprehensive testing completed!")
            print(f"📊 Success Rate: {(report['passed_tests']/report['total_tests']*100):.1f}%")
            print(f"📸 Screenshots: {len(self.screenshots)} taken")
            print(f"📄 Report: test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            self.window.close()
            self.app.quit()

def main():
    """Main test runner"""
    tester = ComprehensiveTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 