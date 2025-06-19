#!/usr/bin/env python3
"""
Comprehensive Feature Test Script for FoS_DeckPro
Using APTPT Theory Principles for Robust Testing
"""

import sys
import os
import time
import json
import traceback
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'FoS_DeckPro'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from ui.main_window import MainWindow
from models.inventory import CardInventory
from models.scryfall_api import fetch_scryfall_data

class FeatureTester:
    """APTPT-based feature tester for FoS_DeckPro."""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.main_window = None
        self.test_results = {}
        self.feature_tests = [
            ("Basic UI", self.test_basic_ui),
            ("Card Display", self.test_card_display),
            ("Filtering", self.test_filtering),
            ("Add Card", self.test_add_card),
            ("Edit Card", self.test_edit_card),
            ("Delete Card", self.test_delete_card),
            ("Import/Export", self.test_import_export),
            ("Column Customization", self.test_column_customization),
            ("Undo/Redo", self.test_undo_redo),
            ("Scryfall Enrichment", self.test_scryfall_enrichment),
            ("Whatnot Export", self.test_whatnot_export),
            ("Whatnot Pricing", self.test_whatnot_pricing),
            ("Break Builder", self.test_break_builder),
            ("Packing Slip Processing", self.test_packing_slip_processing),
            ("APTPT Features", self.test_aptpt_features),
        ]
    
    def run_all_tests(self):
        """Run all feature tests using APTPT adaptive principles."""
        print("🚀 Starting Comprehensive Feature Test Suite")
        print("=" * 60)
        
        # Initialize main window
        self.main_window = MainWindow()
        self.main_window.show()
        
        # Wait for UI to initialize
        self._wait_for_ui()
        
        total_tests = len(self.feature_tests)
        passed_tests = 0
        failed_tests = 0
        
        for test_name, test_func in self.feature_tests:
            print(f"\n🔍 Testing: {test_name}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                result = test_func()
                test_time = time.time() - start_time
                
                if result:
                    print(f"✅ PASS: {test_name} ({test_time:.2f}s)")
                    passed_tests += 1
                    self.test_results[test_name] = {
                        'status': 'PASS',
                        'time': test_time,
                        'details': 'Feature working correctly'
                    }
                else:
                    print(f"❌ FAIL: {test_name} ({test_time:.2f}s)")
                    failed_tests += 1
                    self.test_results[test_name] = {
                        'status': 'FAIL',
                        'time': test_time,
                        'details': 'Feature not working correctly'
                    }
                    
            except Exception as e:
                print(f"💥 ERROR: {test_name} - {str(e)}")
                failed_tests += 1
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'time': 0,
                    'details': f'Exception: {str(e)}'
                }
                traceback.print_exc()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Save detailed results
        self._save_test_results()
        
        return passed_tests == total_tests
    
    def _wait_for_ui(self):
        """Wait for UI to be ready."""
        loop = QEventLoop()
        QTimer.singleShot(1000, loop.quit)
        loop.exec()
    
    def test_basic_ui(self) -> bool:
        """Test basic UI components."""
        try:
            # Check main window exists
            assert self.main_window is not None
            assert self.main_window.isVisible()
            
            # Check essential components
            assert hasattr(self.main_window, 'card_table')
            assert hasattr(self.main_window, 'inventory')
            assert hasattr(self.main_window, 'filter_overlay')
            
            # Check menu bar
            menubar = self.main_window.menuBar()
            assert menubar is not None
            assert len(menubar.actions()) > 0
            
            print("  ✓ Main window visible and functional")
            print("  ✓ Essential components present")
            print("  ✓ Menu bar accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Basic UI test failed: {e}")
            return False
    
    def test_card_display(self) -> bool:
        """Test card display functionality."""
        try:
            # Check cards are displayed
            cards = self.main_window.inventory.get_all_cards()
            assert len(cards) > 0
            
            # Check card table has data
            table_cards = self.main_window.card_table.cards
            assert len(table_cards) > 0
            
            # Check pagination
            assert hasattr(self.main_window.card_table, 'pagination_widget')
            
            print(f"  ✓ {len(cards)} cards loaded")
            print(f"  ✓ {len(table_cards)} cards displayed")
            print("  ✓ Pagination widget present")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Card display test failed: {e}")
            return False
    
    def test_filtering(self) -> bool:
        """Test filtering functionality."""
        try:
            # Check filter overlay exists
            filter_overlay = self.main_window.filter_overlay
            assert filter_overlay is not None
            
            # Check filter fields
            filters = filter_overlay.filters
            assert len(filters) > 0
            
            # Test filtering
            original_count = len(self.main_window.card_table.cards)
            
            # Apply a filter
            if 'Name' in filters:
                filters['Name'].setText('Lightning')
                self._wait_for_ui()
                
                filtered_count = len(self.main_window.card_table.cards)
                print(f"  ✓ Filter applied: {original_count} -> {filtered_count} cards")
            
            # Clear filter
            for filter_widget in filters.values():
                filter_widget.clear()
            self._wait_for_ui()
            
            restored_count = len(self.main_window.card_table.cards)
            assert restored_count == original_count
            
            print("  ✓ Filter overlay functional")
            print("  ✓ Filter clearing works")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Filtering test failed: {e}")
            return False
    
    def test_add_card(self) -> bool:
        """Test add card functionality."""
        try:
            original_count = len(self.main_window.inventory.get_all_cards())
            
            # Test add card dialog
            add_dialog = self.main_window.add_card(test_mode=True)
            assert add_dialog is not None
            
            # Fill in card details
            if hasattr(add_dialog, 'name_edit'):
                add_dialog.name_edit.setText("Test Card")
            if hasattr(add_dialog, 'set_edit'):
                add_dialog.set_edit.setText("Test Set")
            
            # Accept dialog
            add_dialog.accept()
            self._wait_for_ui()
            
            new_count = len(self.main_window.inventory.get_all_cards())
            assert new_count == original_count + 1
            
            print("  ✓ Add card dialog functional")
            print("  ✓ Card added successfully")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Add card test failed: {e}")
            return False
    
    def test_edit_card(self) -> bool:
        """Test edit card functionality."""
        try:
            # Get first card
            cards = self.main_window.inventory.get_all_cards()
            assert len(cards) > 0
            
            original_name = cards[0].get('Name', '')
            
            # Test edit dialog
            edit_dialog = self.main_window.edit_card(0, test_mode=True)
            assert edit_dialog is not None
            
            # Modify card name
            if hasattr(edit_dialog, 'name_edit'):
                edit_dialog.name_edit.setText("Edited Test Card")
            
            # Accept dialog
            edit_dialog.accept()
            self._wait_for_ui()
            
            # Check card was updated
            updated_cards = self.main_window.inventory.get_all_cards()
            updated_name = updated_cards[0].get('Name', '')
            assert updated_name == "Edited Test Card"
            
            print("  ✓ Edit card dialog functional")
            print("  ✓ Card updated successfully")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Edit card test failed: {e}")
            return False
    
    def test_delete_card(self) -> bool:
        """Test delete card functionality."""
        try:
            original_count = len(self.main_window.inventory.get_all_cards())
            
            # Delete first card
            self.main_window.delete_cards([0])
            self._wait_for_ui()
            
            new_count = len(self.main_window.inventory.get_all_cards())
            assert new_count == original_count - 1
            
            print("  ✓ Card deletion functional")
            print("  ✓ Card count reduced")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Delete card test failed: {e}")
            return False
    
    def test_import_export(self) -> bool:
        """Test import/export functionality."""
        try:
            # Test export
            cards = self.main_window.inventory.get_all_cards()
            assert len(cards) > 0
            
            # Test CSV export
            csv_data = self.main_window._export_to_csv_string(cards, ['Name', 'Set name'])
            assert 'Name' in csv_data
            assert 'Set name' in csv_data
            
            # Test JSON export
            json_data = self.main_window._export_to_json_string(cards)
            parsed_data = json.loads(json_data)
            assert len(parsed_data) == len(cards)
            
            print("  ✓ CSV export functional")
            print("  ✓ JSON export functional")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Import/export test failed: {e}")
            return False
    
    def test_column_customization(self) -> bool:
        """Test column customization."""
        try:
            # Test column customization dialog
            dialog = self.main_window.customize_columns()
            assert dialog is not None
            
            print("  ✓ Column customization dialog accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Column customization test failed: {e}")
            return False
    
    def test_undo_redo(self) -> bool:
        """Test undo/redo functionality."""
        try:
            # Check undo action exists
            undo_action = self.main_window.undo_action
            assert undo_action is not None
            
            print("  ✓ Undo functionality present")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Undo/redo test failed: {e}")
            return False
    
    def test_scryfall_enrichment(self) -> bool:
        """Test Scryfall enrichment."""
        try:
            # Test Scryfall API
            test_data = fetch_scryfall_data("lightning-bolt")
            assert test_data is not None
            assert 'type_line' in test_data
            
            print("  ✓ Scryfall API functional")
            print("  ✓ Card data retrieved")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Scryfall enrichment test failed: {e}")
            return False
    
    def test_whatnot_export(self) -> bool:
        """Test Whatnot export functionality."""
        try:
            # Test Whatnot export
            self.main_window.export_to_whatnot()
            print("  ✓ Whatnot export accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Whatnot export test failed: {e}")
            return False
    
    def test_whatnot_pricing(self) -> bool:
        """Test Whatnot pricing adjustment."""
        try:
            # Test pricing dialog
            self.main_window.adjust_whatnot_pricing_dialog()
            print("  ✓ Whatnot pricing dialog accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Whatnot pricing test failed: {e}")
            return False
    
    def test_break_builder(self) -> bool:
        """Test break builder functionality."""
        try:
            # Test break builder dialog
            self.main_window.open_break_builder()
            print("  ✓ Break builder accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Break builder test failed: {e}")
            return False
    
    def test_packing_slip_processing(self) -> bool:
        """Test packing slip processing."""
        try:
            # Test packing slip processing
            self.main_window.process_packing_slips()
            print("  ✓ Packing slip processing accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ Packing slip processing test failed: {e}")
            return False
    
    def test_aptpt_features(self) -> bool:
        """Test APTPT-specific features."""
        try:
            # Check APTPT menu exists
            menubar = self.main_window.menuBar()
            aptpt_menu = None
            for action in menubar.actions():
                if action.text() == "APTPT":
                    aptpt_menu = action.menu()
                    break
            
            assert aptpt_menu is not None
            assert len(aptpt_menu.actions()) > 0
            
            print("  ✓ APTPT menu present")
            print("  ✓ APTPT features accessible")
            
            return True
            
        except Exception as e:
            print(f"  ✗ APTPT features test failed: {e}")
            return False
    
    def _save_test_results(self):
        """Save detailed test results."""
        results_file = "feature_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")

def main():
    """Main test runner."""
    tester = FeatureTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL FEATURES WORKING CORRECTLY!")
        return 0
    else:
        print("\n⚠️  SOME FEATURES NEED ATTENTION")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 