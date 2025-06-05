from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStatusBar, QMenuBar, QFileDialog, QMessageBox, QSplitter, QSizePolicy, QDialog, QPushButton, QTextEdit, QInputDialog, QRadioButton, QButtonGroup, QLineEdit, QProgressDialog
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from ui.card_table import CardTableView
from ui.filter_overlay import FilterOverlay
from ui.image_preview import ImagePreview
from ui.card_details import CardDetails
from ui.dialogs.export_columns import ExportColumnsDialog
from models.inventory import CardInventory
import json
import os
from utils.config import save_last_file, load_last_file
import csv
from ui.dialogs.import_column_mapping import ImportColumnMappingDialog
import copy
from ui.dialogs.edit_card import EditCardDialog
import datetime
from ui.dialogs.column_customization import ColumnCustomizationDialog
from ui.dialogs.bulk_edit_remove import BulkEditRemoveDialog
from models.scryfall_api import fetch_scryfall_data
import time
from ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
import pandas as pd
import re
from ui.dialogs.break_builder import BreakBuilderDialog
from ui.columns_config import DEFAULT_COLUMNS
import pdfplumber
import traceback
from utils.packing_slip_file_manager import find_new_packing_slips, move_and_rename_packing_slip
from logic.whatnot_packing_slip_parser import WhatnotPackingSlipParser
from logic.whatnot_inventory_removal import remove_sold_cards_from_inventory
from logic.whatnot_buyer_db import WhatnotBuyerDB
from ui.dialogs.packing_slip_summary import PackingSlipSummaryDialog
from utils import license

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FoS-DeckPro")
        self.setMinimumSize(1200, 700)

        # Expanded columns for display and filtering
        self.columns = DEFAULT_COLUMNS.copy()
        self.visible_columns = DEFAULT_COLUMNS.copy()
        self.inventory = CardInventory()
        # Load sample data for now
        sample_cards = [
            {"Name": "Paradise Plume", "Set name": "Time Spiral Remastered", "Set code": "TSR", "Collector number": "271", "Rarity": "uncommon", "Condition": "near_mint", "Foil": "normal", "Language": "en", "Purchase price": "$0.25", "Whatnot price": "$1"},
            {"Name": "Lightning Bolt", "Set name": "Magic 2011", "Set code": "M11", "Collector number": "145", "Rarity": "common", "Condition": "near_mint", "Foil": "foil", "Language": "en", "Purchase price": "$2.00", "Whatnot price": "$2"},
        ]
        self.inventory.load_cards(sample_cards)
        self._update_columns_from_inventory()

        # Menu bar and File > Open
        menubar = self.menuBar()  # Use native menu bar for macOS robustness
        file_menu = menubar.addMenu("File")
        open_action = file_menu.addAction("Open JSON...")
        open_action.triggered.connect(self.open_json_file)
        export_action = file_menu.addAction("Export...")
        export_action.triggered.connect(self.export_cards)
        import_action = file_menu.addAction("Import...")
        import_action.triggered.connect(self.import_cards)
        add_action = file_menu.addAction("Add Card...")
        add_action.triggered.connect(self.add_card)
        self.auto_save_action = file_menu.addAction("Auto-Save Changes")
        self.auto_save_action.setCheckable(True)
        self.auto_save_action.setChecked(False)
        self.auto_save_action.triggered.connect(self.toggle_auto_save)
        save_action = file_menu.addAction("Save")
        save_action.triggered.connect(self.save_inventory)
        save_as_action = file_menu.addAction("Save As...")
        save_as_action.triggered.connect(self.save_inventory_as)
        restore_action = file_menu.addAction("Restore from Backup...")
        restore_action.triggered.connect(self.restore_from_backup)
        customize_columns_action = file_menu.addAction("Customize Columns...")
        customize_columns_action.triggered.connect(self.customize_columns)
        save_preset_action = file_menu.addAction("Save Column Preset...")
        save_preset_action.triggered.connect(self.save_column_preset)
        load_preset_action = file_menu.addAction("Load Column Preset...")
        load_preset_action.triggered.connect(self.load_column_preset)
        self.undo_action = file_menu.addAction("Undo Last Import/Change")
        self.undo_action.setEnabled(False)
        self.undo_action.triggered.connect(self.undo_last_change)
        export_whatnot_action = file_menu.addAction("Export to Whatnot...")
        export_whatnot_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.export_to_whatnot, feature_name='export_whatnot'))
        export_item_listings_action = file_menu.addAction("Export Item Listings...")
        export_item_listings_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.export_item_listings_dialog, feature_name='export_item_listings'))
        process_packing_slips_action = file_menu.addAction("Process Whatnot Packing Slips...")
        process_packing_slips_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.process_packing_slips, feature_name='process_packing_slips'))
        undo_packing_slip_action = file_menu.addAction("Undo Last Packing Slip Removal")
        undo_packing_slip_action.setEnabled(False)
        undo_packing_slip_action.triggered.connect(self.undo_last_packing_slip_removal)
        self._last_packing_slip_inventory = None
        self._last_packing_slip_summary = None
        edit_menu = menubar.addMenu("Edit")
        bulk_edit_remove_action = edit_menu.addAction("Bulk Edit/Remove...")
        bulk_edit_remove_action.triggered.connect(self.bulk_edit_remove_dialog)
        self._undo_stack = []  # Multi-level undo stack
        self._current_json_file = None
        self._unsaved_changes = False
        self._auto_save = False
        self.break_builder_action = None  # Ensure attribute exists early
        if license.is_license_valid():
            self._unlock_paid_features()
        # self.setMenuBar(menubar)  # Not needed with self.menuBar()

        # Central widget and main layout
        central = QWidget()
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Left side: vertical layout for filter row and card table
        left_layout = QVBoxLayout()
        # Table container with just the table
        table_container = QWidget()
        table_container_layout = QVBoxLayout()
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.card_table = CardTableView(self.inventory, self.columns)
        self.card_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.card_table.horizontalHeader().setSectionsMovable(False)
        # Restore column widths if available
        if hasattr(self, 'column_widths') and self.column_widths:
            for i, col in enumerate(self.columns):
                if col in self.column_widths:
                    self.card_table.setColumnWidth(i, self.column_widths[col])
        self.card_table.horizontalHeader().sectionResized.connect(self.save_column_widths)
        table_container_layout.addWidget(self.card_table)
        # Add pagination widget below the table
        table_container_layout.addWidget(self.card_table.pagination_widget)
        table_container.setLayout(table_container_layout)
        left_layout.addWidget(table_container)
        # Create and show the filter overlay as a child of the table's viewport
        self.filter_overlay = FilterOverlay(self.card_table, self.columns)
        self.filter_overlay.show()
        for col, filt in self.filter_overlay.filters.items():
            filt.textChanged.connect(self.update_table_filter)

        # Right side: vertical splitter for image preview and card details
        right_splitter = QSplitter()
        right_splitter.setOrientation(Qt.Vertical)
        self.image_preview = ImagePreview()
        self.image_preview.setMinimumHeight(100)
        self.image_preview.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.card_details = CardDetails()
        self.card_details.setMinimumHeight(100)
        self.card_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_splitter.addWidget(self.image_preview)
        right_splitter.addWidget(self.card_details)
        right_splitter.setSizes([300, 400])  # Initial sizes: image, details
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setHandleWidth(8)
        right_splitter.setMinimumWidth(100)
        right_splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Main splitter for resizable panels (left/right)
        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        # Left widget (filter + table)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        # Right widget (image + details)
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # Add splitter to main layout
        main_layout.addWidget(splitter)
        splitter.setSizes([700, 400])

        # Status bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

        # Initial table population
        self.card_table.update_cards(self.inventory.get_all_cards())

        # Connect card selection to image preview and details
        self.card_table.card_selected.connect(self.image_preview.show_card_image)
        self.card_table.card_selected.connect(self.card_details.show_card_details)

        # Try to load last used JSON file
        last_file = load_last_file()
        if last_file and os.path.exists(last_file):
            try:
                with open(last_file, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        for col in self.columns:
                            if col not in card or card[col] is None:
                                card[col] = ""
                            if isinstance(card[col], float) and (card[col] != card[col]):
                                card[col] = ""
                    self.inventory.load_cards(cards)
                    self._update_columns_from_inventory()
                    self.card_table.update_cards(self.inventory.get_all_cards())
                    self.statusBar().showMessage(f"Loaded {len(cards)} cards from {os.path.basename(last_file)} (auto)")
            except Exception as e:
                self.statusBar().showMessage(f"Failed to load last file: {e}")

        # Connect edit and delete signals
        self.card_table.edit_card_requested.connect(self.edit_card)
        self.card_table.delete_card_requested.connect(self.delete_cards)

        # Add menu actions for column width reset/stretch
        view_menu = menubar.addMenu("View")
        reset_widths_action = QAction("Reset Column Widths", self)
        reset_widths_action.triggered.connect(self.card_table.reset_column_widths)
        view_menu.addAction(reset_widths_action)
        stretch_columns_action = QAction("Stretch Columns to Fit", self)
        stretch_columns_action.setCheckable(True)
        stretch_columns_action.setChecked(False)
        def toggle_stretch():
            self.card_table.set_stretch_columns(stretch_columns_action.isChecked())
        stretch_columns_action.triggered.connect(toggle_stretch)
        view_menu.addAction(stretch_columns_action)

        # Add Whatnot pricing adjustment action (paid)
        tools_menu = menubar.addMenu("Tools")
        adjust_whatnot_action = QAction("Adjust Whatnot Pricing...", self)
        adjust_whatnot_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.adjust_whatnot_pricing_dialog, feature_name='adjust_whatnot_pricing'))
        tools_menu.addAction(adjust_whatnot_action)
        self.adjust_whatnot_action = adjust_whatnot_action
        # Add Scryfall enrichment action
        enrich_action = QAction("Enrich All Cards from Scryfall...", self)
        enrich_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.enrich_all_cards_from_scryfall, feature_name='enrich_scryfall'))
        tools_menu.addAction(enrich_action)
        # Add Break/Autobox Builder action
        break_builder_action = QAction("Open Break/Autobox Builder", self)
        self.break_builder_action = break_builder_action
        self.break_builder_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.open_break_builder, feature_name='break_builder'))
        tools_menu.addAction(self.break_builder_action)
        # Add Scryfall ID to Inventory action
        add_scryfall_action = QAction("Add Card by Scryfall ID", self)
        add_scryfall_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.add_card_by_scryfall_id, feature_name='add_scryfall'))
        tools_menu.addAction(add_scryfall_action)

        # Add Whatnot export action (paid)
        self.export_whatnot_action = export_whatnot_action
        self.export_whatnot_action.triggered.disconnect()
        self.export_whatnot_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.export_to_whatnot, feature_name='export_whatnot'))
        # Add export item listings action (paid)
        self.export_item_listings_action = export_item_listings_action
        self.export_item_listings_action.triggered.disconnect()
        self.export_item_listings_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.export_item_listings_dialog, feature_name='export_item_listings'))
        # Add Scryfall enrichment action (paid)
        self.enrich_action = enrich_action
        self.enrich_action.triggered.disconnect()
        self.enrich_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.enrich_all_cards_from_scryfall, feature_name='enrich_scryfall'))
        # Add add card by Scryfall ID action (paid)
        self.add_scryfall_action = add_scryfall_action
        self.add_scryfall_action.triggered.disconnect()
        self.add_scryfall_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.add_card_by_scryfall_id, feature_name='add_scryfall'))
        # Add break builder action (already paid)
        # self.break_builder_action already set up

        # Add process Whatnot packing slips action (paid)
        self.process_packing_slips_action = process_packing_slips_action
        self.process_packing_slips_action.triggered.disconnect()
        self.process_packing_slips_action.triggered.connect(lambda: self._on_paid_feature_triggered(self.process_packing_slips, feature_name='process_packing_slips'))

    def _update_columns_from_inventory(self):
        # Dynamically set self.columns to all unique fields in inventory, with defaults first
        all_fields = set(DEFAULT_COLUMNS)
        for card in self.inventory.get_all_cards():
            all_fields.update(card.keys())
        # Keep default columns order, then add the rest sorted
        extra_fields = sorted(f for f in all_fields if f not in DEFAULT_COLUMNS)
        self.columns = DEFAULT_COLUMNS + extra_fields
        self.visible_columns = self.columns.copy()
        # Update table and filter overlay if they exist
        if hasattr(self, 'card_table'):
            self.card_table.columns = self.columns
            self.card_table.model.columns = self.columns
            self.card_table.update_cards(self.inventory.get_all_cards())
        if hasattr(self, 'filter_overlay'):
            self.filter_overlay.columns = self.columns
            # Rebuild overlay filters
            for filt in self.filter_overlay.filters.values():
                filt.deleteLater()
            self.filter_overlay.filters = {}
            for col in self.columns:
                filt = QLineEdit(self.filter_overlay)
                filt.setPlaceholderText(col)
                filt.textChanged.connect(self.update_table_filter)
                self.filter_overlay.filters[col] = filt
            self.filter_overlay.update_positions()

    def update_table_filter(self):
        filters = {col: self.filter_overlay.filters[col].text() for col in self.columns}
        # Debug: print all card values for each filter
        for col, value in filters.items():
            if value:
                print(f"DEBUG: Filtering on column '{col}' with value '{value}'")
                print(f"DEBUG: All values for '{col}': {[str(card.get(col, '')) for card in self.inventory.get_all_cards()]}")
        if self.inventory.get_all_cards():
            print(f"DEBUG: Keys in first card: {list(self.inventory.get_all_cards()[0].keys())}")
        filtered = self.inventory.filter_cards(filters)
        print(f"Filter: {filters} -> {len(filtered)} cards")  # DEBUG
        self.card_table.update_cards(filtered)
        self.card_table.repaint()  # Force repaint
        # Hide columns not in visible_columns
        for i, col in enumerate(self.columns):
            self.card_table.setColumnHidden(i, col not in self.visible_columns)

    def open_json_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open JSON File", os.getcwd(), "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        for col in self.columns:
                            if col not in card or card[col] is None:
                                card[col] = ""
                            if isinstance(card[col], float) and (card[col] != card[col]):
                                card[col] = ""
                    self.inventory.load_cards(cards)
                    self._update_columns_from_inventory()
                    self.card_table.update_cards(self.inventory.get_all_cards())
                    self.statusBar().showMessage(f"Loaded {len(cards)} cards from {os.path.basename(filename)}")
                    save_last_file(filename)
                    self._current_json_file = filename
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load JSON: {e}")

    def export_cards(self):
        filtered_cards = self.card_table.cards
        if not filtered_cards:
            QMessageBox.information(self, "Export", "No cards to export.")
            return
        # Ask user for format
        formats = ["CSV (*.csv)", "JSON (*.json)"]
        filename, selected_filter = QFileDialog.getSaveFileName(self, "Export Cards", os.getcwd(), ";;".join(formats))
        if not filename:
            return
        try:
            if selected_filter.startswith("CSV") or filename.lower().endswith(".csv"):
                # Get all unique fields from the cards
                all_fields = set()
                for card in filtered_cards:
                    all_fields.update(card.keys())
                # Show column selection dialog
                dialog = ExportColumnsDialog(sorted(all_fields), self)
                if dialog.exec():
                    selected_columns = dialog.get_selected_columns()
                    if selected_columns:
                        self._export_to_csv(filename, filtered_cards, selected_columns)
                        self.statusBar().showMessage(f"Exported {len(filtered_cards)} cards to {os.path.basename(filename)}")
                    else:
                        QMessageBox.warning(self, "Export", "No columns selected for export.")
            else:
                self._export_to_json(filename, filtered_cards)
                self.statusBar().showMessage(f"Exported {len(filtered_cards)} cards to {os.path.basename(filename)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export: {e}")

    def _export_to_csv(self, filename, cards, columns):
        """Export cards to CSV with specified columns in the given order."""
        if not cards or not columns:
            return
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for card in cards:
                writer.writerow({col: card.get(col, "") for col in columns})

    def _export_to_json(self, filename, cards):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)

    def import_cards(self):
        formats = ["CSV (*.csv)", "JSON (*.json)"]
        filename, selected_filter = QFileDialog.getOpenFileName(self, "Import Cards", os.getcwd(), ";;".join(formats))
        if not filename:
            return
        # Ask user: merge or replace?
        choice = QMessageBox.question(
            self, "Import Mode",
            "Do you want to merge with the current inventory or replace it?\n\nYes = Merge, No = Replace",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        if choice == QMessageBox.Cancel:
            return
        merge = (choice == QMessageBox.Yes)
        # Call import logic (to be implemented next)
        self._do_import_cards(filename, selected_filter, merge)

    def _do_import_cards(self, filename, selected_filter, merge):
        import csv
        import json
        from PySide6.QtWidgets import QMessageBox
        try:
            self.save_undo_state()
            # Determine file type
            if selected_filter.startswith("CSV") or filename.lower().endswith(".csv"):
                with open(filename, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    csv_columns = reader.fieldnames
                    # Show column mapping dialog
                    app_fields = [
                        "Name", "Set name", "Set code", "Collector number", "Rarity",
                        "Condition", "Foil", "Language", "Purchase price", "Whatnot price",
                        "ManaBox ID", "Scryfall ID", "Misprint", "Altered", "Purchase price currency",
                        "Quantity", "cmc", "color_identity", "colors", "legal_commander", "legal_pauper",
                        "mana_cost", "type_line", "oracle_text"
                    ]
                    dialog = ImportColumnMappingDialog(csv_columns, app_fields, self)
                    if not dialog.exec():
                        return  # User cancelled
                    mapping = dialog.get_mapping()
                    # Build new_cards using mapping
                    new_cards = []
                    for row in reader:
                        card = {}
                        for csv_col, app_field in mapping.items():
                            if app_field:
                                val = row.get(csv_col, "")
                                # For price fields, keep as string, never set to '0.0'
                                if app_field in ("Purchase price", "Whatnot price"):
                                    if val is None or val.strip() == "" or val.strip() == "0.0":
                                        val = ""
                                card[app_field] = val
                        if card:
                            new_cards.append(card)
                    # DEBUG: Print first 5 imported cards and their 'Purchase price'
                    print("DEBUG: First 5 imported cards after CSV import:")
                    for c in new_cards[:5]:
                        print({k: c.get(k, None) for k in ("Name", "Purchase price")})
            else:
                with open(filename, 'r', encoding='utf-8') as f:
                    new_cards = json.load(f)
            if not isinstance(new_cards, list):
                raise ValueError("Imported file does not contain a list of cards.")
            if not new_cards:
                QMessageBox.information(self, "Import", "No cards found in the file.")
                return
            # Normalize keys (strip whitespace)
            for card in new_cards:
                for k in list(card.keys()):
                    if k != k.strip():
                        card[k.strip()] = card.pop(k)
            if merge:
                # Merge: update existing or add new (by Name+Set code+Collector number)
                existing = self.inventory.get_all_cards()
                key_fields = ["Name", "Set code", "Collector number"]
                def card_key(card):
                    return tuple(card.get(f, "").strip().lower() for f in key_fields)
                existing_map = {card_key(card): card for card in existing}
                added, updated = 0, 0
                for new_card in new_cards:
                    k = card_key(new_card)
                    if k in existing_map:
                        # Only update fields where new_card has a non-empty value
                        for field, value in new_card.items():
                            if value not in (None, ""):
                                existing_map[k][field] = value
                        updated += 1
                    else:
                        existing.append(new_card)
                        added += 1
                self.inventory.load_cards(existing)
                self.card_table.update_cards(self.inventory.get_all_cards())
                QMessageBox.information(self, "Import", f"Imported {len(new_cards)} cards.\nAdded: {added}, Updated: {updated}.")
                self._unsaved_changes = True
                if self._auto_save:
                    self.save_inventory()
            else:
                # Replace: clear and load
                self.inventory.load_cards(new_cards)
                self.card_table.update_cards(self.inventory.get_all_cards())
                QMessageBox.information(self, "Import", f"Replaced inventory with {len(new_cards)} cards.")
                self._unsaved_changes = True
                if self._auto_save:
                    self.save_inventory()
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Failed to import: {e}")

    def save_undo_state(self):
        # Save a deep copy of the current inventory for multi-level undo
        self._undo_stack.append(copy.deepcopy(self.inventory.get_all_cards()))
        self.undo_action.setEnabled(True)

    def undo_last_change(self):
        if not self._undo_stack:
            QMessageBox.information(self, "Undo", "No previous state to undo.")
            return
        prev_cards = self._undo_stack.pop()
        current_cards = self.inventory.get_all_cards()
        confirm = QMessageBox.question(
            self, "Undo Last Import/Change",
            f"Are you sure you want to undo the last import/change?\n\nCurrent cards: {len(current_cards)}\nPrevious cards: {len(prev_cards)}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.inventory.load_cards(prev_cards)
            self.card_table.update_cards(self.inventory.get_all_cards())
            if not self._undo_stack:
                self.undo_action.setEnabled(False)
            # Show summary dialog with optional diff
            class UndoSummaryDialog(QDialog):
                def __init__(self, before, after, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Undo Summary")
                    layout = QVBoxLayout(self)
                    layout.addWidget(QLabel(f"Undo complete.\nCards before: {len(before)}\nCards after: {len(after)}"))
                    btns = QHBoxLayout()
                    view_btn = QPushButton("View Changes")
                    view_btn.clicked.connect(self.show_diff)
                    close_btn = QPushButton("Close")
                    close_btn.clicked.connect(self.accept)
                    btns.addWidget(view_btn)
                    btns.addWidget(close_btn)
                    layout.addLayout(btns)
                    self.before = before
                    self.after = after
                def show_diff(self):
                    # Show a simple diff: added/removed/changed
                    before_set = {self._card_key(c): c for c in self.before}
                    after_set = {self._card_key(c): c for c in self.after}
                    added = [after_set[k] for k in after_set if k not in before_set]
                    removed = [before_set[k] for k in before_set if k not in after_set]
                    changed = [after_set[k] for k in after_set if k in before_set and after_set[k] != before_set[k]]
                    text = []
                    if added:
                        text.append(f"Added ({len(added)}):\n" + "\n".join(str(a) for a in added))
                    if removed:
                        text.append(f"Removed ({len(removed)}):\n" + "\n".join(str(r) for r in removed))
                    if changed:
                        text.append(f"Changed ({len(changed)}):\n" + "\n".join(str(c) for c in changed))
                    if not text:
                        text = ["No differences detected."]
                    diff_dialog = QDialog(self)
                    diff_dialog.setWindowTitle("Undo Changes Diff")
                    vbox = QVBoxLayout(diff_dialog)
                    txt = QTextEdit()
                    txt.setReadOnly(True)
                    txt.setPlainText("\n\n".join(text))
                    vbox.addWidget(txt)
                    close_btn = QPushButton("Close")
                    close_btn.clicked.connect(diff_dialog.accept)
                    vbox.addWidget(close_btn)
                    diff_dialog.resize(600, 400)
                    diff_dialog.exec()
                def _card_key(self, card):
                    return tuple(card.get(f, "").strip().lower() for f in ["Name", "Set code", "Collector number"])
            dlg = UndoSummaryDialog(current_cards, prev_cards, self)
            dlg.exec()

    def edit_card(self, row, test_mode=False):
        card = self.card_table.cards[row]
        dlg = EditCardDialog(card, all_fields=self.columns, parent=self)
        if test_mode:
            def on_accept():
                self.save_undo_state()
                updated_card = dlg.get_card()
                all_cards = self.inventory.get_all_cards()
                all_cards[row] = updated_card
                self.inventory.load_cards(all_cards)
                self.card_table.update_cards(self.inventory.get_all_cards())
                self._unsaved_changes = True
                if self._auto_save:
                    self.save_inventory()
            dlg.accepted.connect(on_accept)
            dlg.show()
            return dlg
        if dlg.exec():
            self.save_undo_state()
            updated_card = dlg.get_card()
            # Update the card in inventory
            all_cards = self.inventory.get_all_cards()
            all_cards[row] = updated_card
            self.inventory.load_cards(all_cards)
            self.card_table.update_cards(self.inventory.get_all_cards())
            self._unsaved_changes = True
            if self._auto_save:
                self.save_inventory()

    def add_card(self, test_mode=False):
        dlg = EditCardDialog(card=None, all_fields=self.columns, parent=self)
        if test_mode:
            def on_accept():
                self.save_undo_state()
                new_card = dlg.get_card()
                all_cards = self.inventory.get_all_cards()
                all_cards.append(new_card)
                self.inventory.load_cards(all_cards)
                self.card_table.update_cards(self.inventory.get_all_cards())
                self._unsaved_changes = True
                if self._auto_save:
                    self.save_inventory()
            dlg.accepted.connect(on_accept)
            dlg.show()
            return dlg
        if dlg.exec():
            self.save_undo_state()
            new_card = dlg.get_card()
            all_cards = self.inventory.get_all_cards()
            all_cards.append(new_card)
            self.inventory.load_cards(all_cards)
            self.card_table.update_cards(self.inventory.get_all_cards())
            self._unsaved_changes = True
            if self._auto_save:
                self.save_inventory()

    def delete_cards(self, rows):
        from PySide6.QtWidgets import QMessageBox
        if not rows:
            return
        confirm = QMessageBox.question(
            self, "Delete Card(s)",
            f"Are you sure you want to delete {len(rows)} card(s)?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.save_undo_state()
            all_cards = self.inventory.get_all_cards()
            # Remove by index, highest first to avoid reindexing
            for row in sorted(rows, reverse=True):
                if 0 <= row < len(all_cards):
                    all_cards.pop(row)
            self.inventory.load_cards(all_cards)
            self.card_table.update_cards(self.inventory.get_all_cards())
            self._unsaved_changes = True
            if self._auto_save:
                self.save_inventory()

    def save_inventory(self):
        import json
        if not self._current_json_file:
            self.save_inventory_as()
            return
        try:
            with open(self._current_json_file, 'w', encoding='utf-8') as f:
                json.dump(self.inventory.get_all_cards(), f, ensure_ascii=False, indent=2)
            self.statusBar().showMessage(f"Saved to {os.path.basename(self._current_json_file)}")
            self._unsaved_changes = False
            # Versioned backup
            self._save_versioned_backup()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Save Failed", f"Failed to save: {e}")

    def save_inventory_as(self):
        import json
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        filename, _ = QFileDialog.getSaveFileName(self, "Save Inventory As", os.getcwd(), "JSON Files (*.json)")
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.inventory.get_all_cards(), f, ensure_ascii=False, indent=2)
            self._current_json_file = filename
            self.statusBar().showMessage(f"Saved to {os.path.basename(filename)}")
            self._unsaved_changes = False
            # Versioned backup
            self._save_versioned_backup()
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"Failed to save: {e}")

    def _save_versioned_backup(self):
        import json
        if not self._current_json_file:
            return
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Backups')
        os.makedirs(backup_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(self._current_json_file))[0]
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f"{base}_backup_{timestamp}.json")
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.inventory.get_all_cards(), f, ensure_ascii=False, indent=2)
            self.statusBar().showMessage(f"Backup saved: {os.path.basename(backup_file)}", 5000)
        except Exception as e:
            pass

    def closeEvent(self, event):
        from PySide6.QtWidgets import QMessageBox
        if self._unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.save_inventory()
                if self._unsaved_changes:
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        event.accept()

    def toggle_auto_save(self):
        self._auto_save = self.auto_save_action.isChecked()

    def restore_from_backup(self):
        import json
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Backups')
        filename, _ = QFileDialog.getOpenFileName(self, "Restore from Backup", backup_dir, "JSON Files (*.json)")
        if not filename:
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                cards = json.load(f)
            if not isinstance(cards, list):
                raise ValueError("Backup file does not contain a list of cards.")
            self.inventory.load_cards(cards)
            self.card_table.update_cards(self.inventory.get_all_cards())
            self._unsaved_changes = True
            # Optionally, update current file path (comment out if not desired)
            # self._current_json_file = filename
            self.statusBar().showMessage(f"Restored from backup: {os.path.basename(filename)}")
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", f"Failed to restore: {e}")

    def customize_columns(self):
        dlg = ColumnCustomizationDialog(self.columns, self.visible_columns, self.columns, self)
        if dlg.exec():
            ordered, visible = dlg.get_columns()
            self.columns = ordered
            self.visible_columns = visible
            self.save_column_prefs()
            # Update table columns and visibility
            self.card_table.columns = self.columns
            self.card_table.model.columns = self.columns
            self.card_table.update_cards(self.inventory.get_all_cards())
            # Hide columns not in visible_columns
            for i, col in enumerate(self.columns):
                self.card_table.setColumnHidden(i, col not in self.visible_columns)
            # Restore column widths if available
            if hasattr(self, 'column_widths') and self.column_widths:
                for i, col in enumerate(self.columns):
                    if col in self.column_widths:
                        self.card_table.setColumnWidth(i, self.column_widths[col])
            # Ensure visual order matches logical order
            self._apply_column_order()

    def save_column_widths(self):
        # Save current column widths to preferences
        widths = {}
        for i, col in enumerate(self.columns):
            widths[col] = self.card_table.columnWidth(i)
        self.column_widths = widths
        self.save_column_prefs()

    def save_column_prefs(self):
        import json
        prefs = {
            "columns": self.columns,
            "visible_columns": self.visible_columns,
            "column_widths": getattr(self, 'column_widths', {})
        }
        prefs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'column_prefs.json')
        with open(prefs_file, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)

    def load_column_prefs(self):
        import json
        prefs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'column_prefs.json')
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                self.column_widths = prefs.get('column_widths', {})
                return prefs.get('columns', self.columns), prefs.get('visible_columns', self.columns)
            except Exception:
                pass
        self.column_widths = {}
        return self.columns, self.columns

    def save_column_preset(self):
        import json
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        preset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'column_presets')
        os.makedirs(preset_dir, exist_ok=True)
        name, ok = QInputDialog.getText(self, "Save Column Preset", "Preset name:")
        if not ok or not name.strip():
            return
        preset_file = os.path.join(preset_dir, f"{name.strip()}.json")
        preset = {
            "columns": self.columns,
            "visible_columns": self.visible_columns,
            "column_widths": getattr(self, 'column_widths', {})
        }
        try:
            with open(preset_file, 'w', encoding='utf-8') as f:
                json.dump(preset, f, ensure_ascii=False, indent=2)
            self.statusBar().showMessage(f"Preset saved: {name.strip()}")
        except Exception as e:
            QMessageBox.critical(self, "Save Preset Failed", f"Failed to save preset: {e}")

    def load_column_preset(self):
        import json
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        preset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'column_presets')
        os.makedirs(preset_dir, exist_ok=True)
        filename, _ = QFileDialog.getOpenFileName(self, "Load Column Preset", preset_dir, "JSON Files (*.json)")
        if not filename:
            return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                preset = json.load(f)
            self.columns = preset.get('columns', self.columns)
            self.visible_columns = preset.get('visible_columns', self.columns)
            self.column_widths = preset.get('column_widths', {})
            self.save_column_prefs()
            # Update table columns and visibility
            self.card_table.columns = self.columns
            self.card_table.model.columns = self.columns
            self.card_table.update_cards(self.inventory.get_all_cards())
            for i, col in enumerate(self.columns):
                self.card_table.setColumnHidden(i, col not in self.visible_columns)
                if col in self.column_widths:
                    self.card_table.setColumnWidth(i, self.column_widths[col])
            # Ensure visual order matches logical order
            self._apply_column_order()
            self.statusBar().showMessage(f"Preset loaded: {os.path.basename(filename)}")
        except Exception as e:
            QMessageBox.critical(self, "Load Preset Failed", f"Failed to load preset: {e}")

    def _apply_column_order(self):
        # Ensure the QTableView's visual order matches self.columns
        header = self.card_table.horizontalHeader()
        model_cols = self.card_table.model.columns
        for logical, col in enumerate(self.columns):
            visual = header.visualIndex(model_cols.index(col))
            if visual != logical:
                header.moveSection(visual, logical)

    def export_to_whatnot(self):
        import csv
        import os
        from PySide6.QtWidgets import QMessageBox
        from ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
        all_cards = self.inventory.get_all_cards()
        if not all_cards:
            QMessageBox.information(self, "Export to Whatnot", "No cards to export.")
            return
        # Read Whatnot template for columns and defaults
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../Whatnot Card Inventory - Template (3).csv')
        with open(template_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            columns = next(reader)
            defaults = next(reader)
        # Static columns and their default values
        static_defaults = {
            "Category": "Trading Card Games",
            "Sub Category": "Magic: The Gathering",
            "Type": "Buy it Now",
            "Shipping Profile": "0-1 oz",
            "Offerable": "No",
            "Hazmat": "Not Hazmat",
            "Condition": "Near Mint",
        }
        # Ask user for Title/Description fields and order
        all_fields = set()
        for card in all_cards:
            all_fields.update(card.keys())
        all_fields = sorted(all_fields)
        dlg = ExportItemListingFieldsDialog(all_fields, self)
        if not dlg.exec():
            return
        title_fields, desc_fields = dlg.get_fields()
        if not title_fields:
            title_fields = ["Name", "Foil"] if "Name" in all_fields else all_fields[:1]
        if not desc_fields:
            desc_fields = [f for f in all_fields if f not in ("Name", "Foil", "Purchase price")]
        # Build export rows
        export_rows = []
        for card in all_cards:
            row = list(defaults)  # start with template defaults
            # Fill static columns
            for col, val in static_defaults.items():
                if col in columns:
                    row[columns.index(col)] = val
            # Title: join selected fields
            title = " ".join(str(card.get(f, "")) for f in title_fields if f in card)
            if "Title" in columns:
                row[columns.index("Title")] = title.strip()
            # Description: join selected fields as lines
            desc = "\n".join(f"{f}: {card.get(f, '')}" for f in desc_fields if f in card)
            if "Description" in columns:
                row[columns.index("Description")] = desc.strip()
            # Quantity
            if "Quantity" in columns:
                row[columns.index("Quantity")] = str(card.get("Quantity", ""))
            # Price
            if "Price" in columns:
                # Whatnot price minimum rule: 0 always exports as 1 (see README)
                price_val = card.get("Whatnot price", "")
                if str(price_val).strip() in ("0", "0.0"):
                    row[columns.index("Price")] = "1"
                else:
                    row[columns.index("Price")] = str(price_val)
            # Cost Per Item
            if "Cost Per Item" in columns:
                row[columns.index("Cost Per Item")] = str(card.get("Purchase price", ""))
            # Image URL 1
            if "Image URL 1" in columns:
                row[columns.index("Image URL 1")] = card.get("image_url", card.get("Image URL 1", ""))
            # Fill other columns with card data if present (but don't overwrite above)
            for i, col in enumerate(columns):
                if col in static_defaults or col in ("Title", "Description", "Quantity", "Price", "Cost Per Item", "Image URL 1"):
                    continue
                value = card.get(col, None)
                if value is not None and value != '':
                    row[i] = str(value)
            export_rows.append(row)
        # Save to CSV
        out_path, _ = self.get_export_path('whatnot')
        if not out_path:
            return
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(export_rows)
        QMessageBox.information(self, "Export to Whatnot", f"Exported {len(export_rows)} cards to {out_path}.")

    def bulk_edit_remove_dialog(self):
        dlg = BulkEditRemoveDialog(self.card_table.cards, self.columns, parent=self)
        if dlg.exec():
            action, field, value = dlg.get_result()
            self.save_undo_state()
            if action == "remove":
                # Remove all filtered cards
                self.inventory.remove_cards(self.card_table.cards)
                self.card_table.update_cards(self.inventory.get_all_cards())
                self._unsaved_changes = True
                if self._auto_save:
                    self.save_inventory()
            elif action == "edit":
                # Bulk edit field for all filtered cards
                all_cards = self.inventory.get_all_cards()
                filtered = self.card_table.cards
                for card in all_cards:
                    if card in filtered:
                        card[field] = value
                self.inventory.load_cards(all_cards)
                self.card_table.update_cards(self.inventory.get_all_cards())
                self._unsaved_changes = True
                if self._auto_save:
                    self.save_inventory()

    def adjust_whatnot_pricing_dialog(self):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QMessageBox
        import math
        dlg = QDialog(self)
        dlg.setWindowTitle("Adjust Whatnot Pricing")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Choose adjustment method for Whatnot price (applies to FILTERED cards only):"))
        # Option 1: Set fixed price
        fixed_radio = QRadioButton("Set filtered to fixed price:")
        fixed_input = QLineEdit()
        fixed_input.setPlaceholderText("e.g. 2.00")
        # Option 2: Custom rounding logic
        round_radio = QRadioButton("Round: cents >= threshold rounds up, otherwise down")
        round_threshold_label = QLabel("Rounding threshold (e.g. 0.30):")
        round_threshold_input = QLineEdit()
        round_threshold_input.setPlaceholderText("0.30")
        round_threshold_input.setText("0.30")
        fixed_radio.setChecked(True)
        group = QButtonGroup(dlg)
        group.addButton(fixed_radio)
        group.addButton(round_radio)
        layout.addWidget(fixed_radio)
        layout.addWidget(fixed_input)
        layout.addWidget(round_radio)
        round_row = QHBoxLayout()
        round_row.addWidget(round_threshold_label)
        round_row.addWidget(round_threshold_input)
        layout.addLayout(round_row)
        btns = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(apply_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        def apply():
            # Use all cards in the inventory, not just filtered
            all_cards = self.inventory.get_all_cards()
            def card_key(card):
                return (
                    card.get("Name", "").strip().lower(),
                    card.get("Set code", "").strip().lower(),
                    card.get("Collector number", "").strip().lower(),
                )
            inventory_map = {card_key(card): card for card in all_cards}
            for inv_card in all_cards:
                price_str = str(inv_card.get("Purchase price", "")).replace("$", "").strip()
                if fixed_radio.isChecked():
                    try:
                        val = float(fixed_input.text())
                        inv_card["Whatnot price"] = str(int(round(val)))
                        print(f"DEBUG: {inv_card.get('Name', '')} | Purchase price: {price_str} | Whatnot price set to: {inv_card['Whatnot price']}")
                    except Exception:
                        print(f"WARNING: {inv_card.get('Name', '')} | Purchase price: {price_str} | Could not parse fixed price input.")
                        QMessageBox.warning(dlg, "Invalid Input", "Please enter a valid number for fixed price.")
                        return
                elif round_radio.isChecked():
                    try:
                        threshold = float(round_threshold_input.text())
                    except Exception:
                        print(f"WARNING: {inv_card.get('Name', '')} | Purchase price: {price_str} | Could not parse rounding threshold.")
                        QMessageBox.warning(dlg, "Invalid Input", "Please enter a valid number for rounding threshold.")
                        return
                    try:
                        price = float(price_str)
                        cents = price - int(price)
                        if cents >= threshold:
                            rounded = math.ceil(price)
                        else:
                            rounded = math.floor(price)
                        inv_card["Whatnot price"] = str(int(rounded))
                        print(f"DEBUG: {inv_card.get('Name', '')} | Purchase price: {price_str} | Whatnot price set to: {inv_card['Whatnot price']}")
                    except Exception:
                        print(f"WARNING: {inv_card.get('Name', '')} | Purchase price: {price_str} | Could not parse for rounding, skipped.")
                        continue
            self.card_table.update_cards(self.inventory.get_all_cards())
            dlg.accept()
        apply_btn.clicked.connect(apply)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()

    def enrich_all_cards_from_scryfall(self):
        from PySide6.QtWidgets import QMessageBox, QProgressDialog
        from models.scryfall_api import fetch_scryfall_data
        import time
        cards = self.inventory.get_all_cards()
        if not cards:
            QMessageBox.information(self, "Scryfall Enrichment", "No cards to enrich.")
            return
        progress = QProgressDialog("Enriching cards from Scryfall...", "Cancel", 0, len(cards), self)
        progress.setWindowTitle("Scryfall Enrichment")
        progress.setWindowModality(Qt.WindowModal)
        updated = 0
        for i, card in enumerate(cards):
            progress.setValue(i)
            if progress.wasCanceled():
                break
            scryfall_id = card.get("Scryfall ID", "")
            if scryfall_id:
                data = fetch_scryfall_data(scryfall_id)
                card.update(data)
                updated += 1
            time.sleep(0.1)  # To avoid Scryfall rate limits
        progress.setValue(len(cards))
        self.inventory.load_cards(cards)
        self.card_table.update_cards(self.inventory.get_all_cards())
        QMessageBox.information(self, "Scryfall Enrichment", f"Enriched {updated} cards from Scryfall.")

    def export_item_listings_dialog(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        formats = ["CSV (*.csv)", "Text (*.txt)"]
        filename, selected_filter = QFileDialog.getSaveFileName(self, "Export Item Listings", os.getcwd(), ";;".join(formats))
        if not filename:
            return
        if selected_filter.startswith("CSV") or filename.lower().endswith(".csv"):
            self.export_item_listings(filename, filetype="csv")
        else:
            self.export_item_listings(filename, filetype="txt")

    def export_item_listings(self, filename, filetype="csv"):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit, QMessageBox
        import csv
        from ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
        # Use all filtered cards
        cards = self.inventory.filter_cards({col: self.filter_overlay.filters[col].text() for col in self.columns})
        if not cards:
            QMessageBox.information(self, "Export Item Listings", "No cards to export.")
            return
        # Gather all available fields
        all_fields = set()
        for card in cards:
            all_fields.update(card.keys())
        all_fields = sorted(all_fields)
        # Ask user for Title/Description fields and order
        dlg = ExportItemListingFieldsDialog(all_fields, self)
        if not dlg.exec():
            return
        title_fields, desc_fields = dlg.get_fields()
        if not title_fields:
            title_fields = ["Name", "Foil"] if "Name" in all_fields else all_fields[:1]
        if not desc_fields:
            desc_fields = [f for f in all_fields if f not in ("Name", "Foil", "Purchase price")]  # Remove purchase price by default
        # Build listings: title, description
        def make_listing(card):
            title = " ".join(str(card.get(f, "")) for f in title_fields if f in card)
            desc_lines = [f"{f}: {card.get(f, '')}" for f in desc_fields if f in card]
            desc = "\n".join(desc_lines)
            return title.strip(), desc
        listings = [make_listing(card) for card in cards]
        # Preview dialog with pagination
        class ListingPreviewDialog(QDialog):
            def __init__(self, listings, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Preview Item Listings")
                self.listings = listings
                self.idx = 0
                self.layout = QVBoxLayout(self)
                self.title_label = QLabel()
                self.desc_text = QTextEdit()
                self.desc_text.setReadOnly(True)
                self.layout.addWidget(self.title_label)
                self.layout.addWidget(self.desc_text)
                btns = QHBoxLayout()
                self.prev_btn = QPushButton("Previous")
                self.next_btn = QPushButton("Next")
                self.export_btn = QPushButton("Export All")
                self.cancel_btn = QPushButton("Cancel")
                btns.addWidget(self.prev_btn)
                btns.addWidget(self.next_btn)
                btns.addWidget(self.export_btn)
                btns.addWidget(self.cancel_btn)
                self.layout.addLayout(btns)
                self.prev_btn.clicked.connect(self.prev)
                self.next_btn.clicked.connect(self.next)
                self.export_btn.clicked.connect(self.accept)
                self.cancel_btn.clicked.connect(self.reject)
                self.update_view()
            def update_view(self):
                title, desc = self.listings[self.idx]
                self.title_label.setText(f"<b>{title}</b>  <span style='font-size:10pt;'>(Listing {self.idx+1} of {len(self.listings)})</span>")
                self.desc_text.setPlainText(desc)
                self.prev_btn.setEnabled(self.idx > 0)
                self.next_btn.setEnabled(self.idx < len(self.listings)-1)
            def prev(self):
                if self.idx > 0:
                    self.idx -= 1
                    self.update_view()
            def next(self):
                if self.idx < len(self.listings)-1:
                    self.idx += 1
                    self.update_view()
        dlg = ListingPreviewDialog(listings, self)
        if not dlg.exec():
            return
        # Export all listings
        if filetype == "csv":
            with open(filename, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Title", "Description"])
                for title, desc in listings:
                    writer.writerow([title, desc])
        else:
            with open(filename, "w", encoding="utf-8") as f:
                for i, (title, desc) in enumerate(listings, 1):
                    f.write(f"Listing {i}: {title}\n{desc}\n\n")
        self.statusBar().showMessage(f"Exported {len(listings)} item listings to {filename}")

    def get_export_path(self, kind):
        from PySide6.QtWidgets import QFileDialog
        default_name = f"{kind}_export.csv"
        filename, _ = QFileDialog.getSaveFileName(self, f"Export to {kind.title()}", os.getcwd(), "CSV Files (*.csv)", options=QFileDialog.Options())
        if not filename:
            return None, None
        return filename, None

    def open_break_builder(self):
        dlg = BreakBuilderDialog(self.inventory, self)
        dlg.exec()
        self.card_table.update_cards(self.inventory.get_all_cards())

    def add_card_by_scryfall_id(self):
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        from models.scryfall_api import fetch_scryfall_data
        scry_id, ok = QInputDialog.getText(self, "Add by Scryfall ID", "Enter Scryfall ID:")
        if not ok or not scry_id.strip():
            return
        data = fetch_scryfall_data(scry_id.strip())
        if not data:
            QMessageBox.warning(self, "Not Found", "No card found for that Scryfall ID.")
            return
        self.inventory.get_all_cards().append(data)
        self.card_table.update_cards(self.inventory.get_all_cards())
        QMessageBox.information(self, "Added", f"Card '{data.get('Name', '')}' added to inventory.")

    def process_packing_slips(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import pdfplumber
        import traceback
        from utils.packing_slip_file_manager import find_new_packing_slips, move_and_rename_packing_slip
        from logic.whatnot_packing_slip_parser import WhatnotPackingSlipParser
        from logic.whatnot_inventory_removal import remove_sold_cards_from_inventory
        from logic.whatnot_buyer_db import WhatnotBuyerDB
        from ui.dialogs.packing_slip_summary import PackingSlipSummaryDialog
        from ui.dialogs.edit_card import EditCardDialog
        import os

        # 1. Prompt for folder
        folder = getattr(self, '_packing_slip_folder', None)
        if not folder or not os.path.isdir(folder):
            folder = QFileDialog.getExistingDirectory(self, "Select Packing Slip Folder", os.getcwd())
            if not folder:
                return
            self._packing_slip_folder = folder
        done_folder = os.path.join(folder, 'done')
        os.makedirs(done_folder, exist_ok=True)

        # 2. Find new PDFs
        pdfs = find_new_packing_slips(folder)
        if not pdfs:
            QMessageBox.information(self, "Packing Slips", "No new packing slip PDFs found.")
            return

        parser = WhatnotPackingSlipParser()
        buyer_db = WhatnotBuyerDB()
        summary = {'removed': [], 'not_found': [], 'ambiguous': [], 'buyers': [], 'files': [], 'errors': []}
        updated_inventory = copy.deepcopy(self.inventory.get_all_cards())
        self._last_packing_slip_inventory = copy.deepcopy(self.inventory.get_all_cards())
        self._last_packing_slip_summary = None
        buyers_updated = set()
        files_to_move = []

        # DEBUG: Print first 5 inventory cards before removal
        print("=== INVENTORY SAMPLE BEFORE REMOVAL ===")
        for card in updated_inventory[:5]:
            print(card)

        def user_prompt_callback(sale, matches):
            # Show dialog to user to resolve ambiguity
            dlg = EditCardDialog(card=sale, all_fields=list(matches[0].keys()), parent=self)
            # Optionally, show a list of matches and let user pick one
            # For now, just let user edit the sale fields and try to match again
            if dlg.exec():
                selected_card = dlg.get_card()
                # Try to find the best match from matches
                for m in matches:
                    if all(str(m.get(f, '')).lower() == str(selected_card.get(f, '')).lower() for f in ['Name', 'Set code', 'Collector number', 'Foil', 'Language'] if selected_card.get(f, '')):
                        return m
                # If not found, just return the first
                return matches[0]
            return None

        for pdf_path in pdfs:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                buyers = parser.parse(text)
                print(f"=== BUYERS PARSED FROM PDF ===\n{buyers}")
                if not buyers:
                    print("=== RAW PDF TEXT ===")
                    print(text)
                for buyer_entry in buyers:
                    print(f"=== PARSED SALES FOR BUYER: {buyer_entry['buyer']} ===")
                    for sale in buyer_entry['sales']:
                        print(sale)
                    show = buyer_entry['show']
                    buyer = buyer_entry['buyer']
                    sales = buyer_entry['sales']
                    # Print sales list before removal
                    print(f"=== SALES TO REMOVE FROM INVENTORY ===")
                    for sale in sales:
                        print(sale)
                    # Remove from inventory with user prompt for ambiguous
                    updated_inventory, removal_log = remove_sold_cards_from_inventory(
                        updated_inventory, sales, user_prompt_callback=user_prompt_callback)
                    # Print removal log after removal
                    print(f"=== REMOVAL LOG ===")
                    for log in removal_log:
                        print(log)
                    for log in removal_log:
                        if log['action'] == 'removed':
                            summary['removed'].append(log)
                        elif log['action'] == 'not_found':
                            summary['not_found'].append(log)
                        elif log['action'] == 'ambiguous':
                            summary['ambiguous'].append(log)
                    # Update buyers DB
                    for sale in sales:
                        buyer_db.add_purchase(buyer, sale, show)
                    buyers_updated.add(buyer['username'] or buyer['name'])
                # Do not move/rename file yet; add to files_to_move for after confirmation
                show_date = buyers[0]['show']['date'] if buyers and buyers[0]['show']['date'] else 'UnknownDate'
                show_title = buyers[0]['show']['title'] if buyers and buyers[0]['show']['title'] else 'UnknownShow'
                files_to_move.append((pdf_path, show_date, show_title))
            except Exception as e:
                summary['errors'].append(f"{os.path.basename(pdf_path)}: {e}\n{traceback.format_exc()}")

        # Save updated inventory
        self.inventory.load_cards(updated_inventory)
        self.card_table.update_cards(self.inventory.get_all_cards())
        self._last_packing_slip_summary = copy.deepcopy(summary)
        # Enable undo after a successful removal
        if summary['removed']:
            for action in self.menuBar().actions():
                for act in action.menu().actions():
                    if act.text() == "Undo Last Packing Slip Removal":
                        act.setEnabled(True)
                        break
        # Show summary dialog
        dlg = PackingSlipSummaryDialog(summary, self)
        dlg.exec()

        # Ask user to confirm removal and moving files
        if summary['removed']:
            confirm = QMessageBox.question(
                self, "Confirm Removal and Move Files",
                f"{len(summary['removed'])} cards were removed from inventory. Move processed packing slips to 'done'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if confirm == QMessageBox.Yes:
                for pdf_path, show_date, show_title in files_to_move:
                    try:
                        new_path = move_and_rename_packing_slip(pdf_path, show_date, show_title, done_folder)
                        summary['files'].append(new_path)
                    except Exception as e:
                        summary['errors'].append(f"{os.path.basename(pdf_path)}: {e}\n{traceback.format_exc()}")
        else:
            QMessageBox.information(self, "Packing Slips", "No cards were removed. Packing slips will not be moved.")

    def undo_last_packing_slip_removal(self):
        from PySide6.QtWidgets import QMessageBox
        if self._last_packing_slip_inventory is None:
            QMessageBox.information(self, "Undo", "No packing slip removal to undo.")
            return
        confirm = QMessageBox.question(
            self, "Undo Packing Slip Removal",
            "Are you sure you want to restore the inventory to its state before the last packing slip removal?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.inventory.load_cards(copy.deepcopy(self._last_packing_slip_inventory))
            self.card_table.update_cards(self.inventory.get_all_cards())
            self.statusBar().showMessage("Inventory restored to before last packing slip removal.")
            # Optionally, show the previous summary dialog
            if self._last_packing_slip_summary:
                dlg = PackingSlipSummaryDialog(self._last_packing_slip_summary, self)
                dlg.exec()
            # Disable undo until next packing slip removal
            for action in self.menuBar().actions():
                for act in action.menu().actions():
                    if act.text() == "Undo Last Packing Slip Removal":
                        act.setEnabled(False)
                        break
            self._last_packing_slip_inventory = None
            self._last_packing_slip_summary = None

    def _lock_paid_features(self):
        # Do not disable any paid feature actions/buttons; all should remain enabled
        pass

    def _unlock_paid_features(self):
        # Do not enable/disable any paid feature actions/buttons; all should remain enabled
        pass

    def _on_paid_feature_triggered(self, feature_func, feature_name=None):
        """
        Wrapper for all paid feature actions. Prompts the user to start a free trial or enter a license key if needed.
        Uses the new prompt_for_trial_or_license flow for maximum clarity and user-friendliness.
        """
        from utils import license as license_utils
        # If a valid license is present for this feature, allow access
        if license_utils.is_license_valid(feature_name=feature_name):
            feature_func()
            return
        # Otherwise, prompt for trial or license
        if license_utils.prompt_for_trial_or_license(self, feature_name=feature_name):
            # If unlocked, allow the feature
            feature_func()
            return
        # If still not unlocked, show a warning
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Feature Locked", f"You do not have access to this feature.\n\nPlease contact Thereal.FosGameres@gmail.com to purchase or upgrade your license.")

    # Layman description:
    # - This function now checks for a valid license key first.
    # - If no license, it checks if a 3-day free trial is active (server-checked).
    # - If the trial is expired, all paid features are locked until a license key is entered.
    # - If not expired, it tries to start a new trial (up to 3 per user/machine).
    # - If a trial is active, all features are unlocked for 3 days.
    # - After 3 trials, a license key is required to use paid features.
