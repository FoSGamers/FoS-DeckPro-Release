from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStatusBar, QMenuBar, QFileDialog, QMessageBox, QSplitter, QSizePolicy, QDialog, QPushButton, QTextEdit, QInputDialog
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ManaBox Enhancer (PySide6)")
        self.setMinimumSize(1200, 700)

        # Expanded columns for display and filtering
        self.default_columns = [
            "Name", "Set name", "Set code", "Collector number", "Rarity",
            "Condition", "Foil", "Language", "Purchase price", "Whatnot price"
        ]
        self.columns, self.visible_columns = self.load_column_prefs()
        self.inventory = CardInventory()
        # Load sample data for now
        sample_cards = [
            {"Name": "Paradise Plume", "Set name": "Time Spiral Remastered", "Set code": "TSR", "Collector number": "271", "Rarity": "uncommon", "Condition": "near_mint", "Foil": "normal", "Language": "en", "Purchase price": "$0.25", "Whatnot price": "$1"},
            {"Name": "Lightning Bolt", "Set name": "Magic 2011", "Set code": "M11", "Collector number": "145", "Rarity": "common", "Condition": "near_mint", "Foil": "foil", "Language": "en", "Purchase price": "$2.00", "Whatnot price": "$2"},
        ]
        self.inventory.load_cards(sample_cards)

        # Menu bar and File > Open
        menubar = QMenuBar(self)
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
        export_whatnot_action.triggered.connect(self.export_to_whatnot)
        edit_menu = menubar.addMenu("Edit")
        bulk_edit_remove_action = edit_menu.addAction("Bulk Edit/Remove...")
        bulk_edit_remove_action.triggered.connect(self.bulk_edit_remove_dialog)
        self._undo_stack = []  # Multi-level undo stack
        self._current_json_file = None
        self._unsaved_changes = False
        self._auto_save = False
        self.setMenuBar(menubar)

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

    def update_table_filter(self):
        filters = {col: self.filter_overlay.filters[col].text() for col in self.columns}
        filtered = self.inventory.filter_cards(filters)
        self.card_table.update_cards(filtered)
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
                                card[app_field] = row.get(csv_col, "")
                        if card:
                            new_cards.append(card)
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
                        existing_map[k].update(new_card)
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

    def edit_card(self, row):
        card = self.card_table.cards[row]
        dlg = EditCardDialog(card, all_fields=self.columns, parent=self)
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

    def add_card(self):
        dlg = EditCardDialog(card=None, all_fields=self.columns, parent=self)
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
        dlg = ColumnCustomizationDialog(self.columns, self.visible_columns, self.default_columns, self)
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
                return prefs.get('columns', self.default_columns), prefs.get('visible_columns', self.default_columns)
            except Exception:
                pass
        self.column_widths = {}
        return self.default_columns, self.default_columns

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
            self.columns = preset.get('columns', self.default_columns)
            self.visible_columns = preset.get('visible_columns', self.default_columns)
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
        filtered_cards = self.card_table.cards
        if not filtered_cards:
            QMessageBox.information(self, "Export to Whatnot", "No cards to export.")
            return
        # Whatnot template columns (from sample)
        whatnot_columns = [
            "Category", "Sub Category", "Title", "Description", "Quantity", "Type", "Price", "Shipping Profile", "Offerable", "Hazmat", "Condition", "Cost Per Item", "SKU", "Image URL 1", "Image URL 2", "Image URL 3", "Image URL 4", "Image URL 5", "Image URL 6", "Image URL 7", "Image URL 8"
        ]
        filename, _ = QFileDialog.getSaveFileName(self, "Export to Whatnot", os.getcwd(), "CSV Files (*.csv)")
        if not filename:
            return
        try:
            with open(filename, "w", newline='', encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=whatnot_columns)
                writer.writeheader()
                for card in filtered_cards:
                    row = {col: "" for col in whatnot_columns}
                    # Map fields
                    row["Category"] = "Trading Cards"
                    row["Sub Category"] = "Magic: The Gathering"
                    row["Title"] = card.get("Name", "")
                    # Description: Name - Set name (Collector number)
                    name = card.get("Name", "")
                    set_name = card.get("Set name", "")
                    collector = card.get("Collector number", "")
                    row["Description"] = f"{name} - {set_name} ({collector})" if collector else f"{name} - {set_name}"
                    row["Quantity"] = card.get("Quantity", "1")
                    row["Type"] = card.get("Type", "")
                    row["Price"] = card.get("Whatnot price", "")
                    row["Shipping Profile"] = card.get("Shipping Profile", "")
                    row["Offerable"] = card.get("Offerable", "Yes")
                    row["Hazmat"] = card.get("Hazmat", "No")
                    row["Condition"] = card.get("Condition", "")
                    row["Cost Per Item"] = card.get("Purchase price", "")
                    row["SKU"] = card.get("SKU", "")
                    # Image URLs (up to 8)
                    for i in range(1, 9):
                        key = f"Image URL {i}"
                        img_key = key if key in card else None
                        if img_key and card.get(img_key):
                            row[key] = card[img_key]
                        elif i == 1:
                            # Try Scryfall image if available
                            row[key] = card.get("Scryfall image", "")
                    writer.writerow(row)
            self.statusBar().showMessage(f"Exported {len(filtered_cards)} cards to Whatnot CSV: {os.path.basename(filename)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export to Whatnot: {e}")

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
