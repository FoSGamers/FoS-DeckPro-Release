from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QCheckBox, QFileDialog, QInputDialog, QWidget, QFormLayout, QGroupBox, QGridLayout, QSplitter, QScrollArea, QTextEdit, QDialogButtonBox
from PySide6.QtCore import Qt
from models.scryfall_api import fetch_scryfall_data
from models.card import CARD_FIELDS
import random
from ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
import os
import json
import copy

class BreakBuilderDialog(QDialog):
    """
    Modular dialog for building Whatnot breaks/autoboxes from inventory.
    """
    def __init__(self, inventory, parent=None):
        super().__init__(parent)
        # Initialize template-related attributes first
        self.export_template = None  # Current template (dict with title_fields, desc_fields)
        self.templates = self.load_templates()
        self.setWindowTitle("FoS-DeckPro: Break/Autobox Builder")
        self.resize(900, 600)
        self.inventory = inventory
        self.break_items = []  # List of dicts (cards/items)
        self.removed_from_inventory = []
        self._undo_inventory = None
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        # Tab 1: Inventory Search/Select
        self.inv_tab = QWidget()
        inv_layout = QVBoxLayout(self.inv_tab)
        inv_layout.addWidget(QLabel("Filter and select cards from inventory:"))
        # --- Advanced Filter Grid ---
        filter_group = QGroupBox("Card Filters (All Fields)")
        filter_grid = QGridLayout()
        self.filter_inputs = {}
        numeric_fields = {f for f in CARD_FIELDS if any(x in f.lower() for x in ["price", "quantity", "number", "count", "cmc"])}
        for idx, field in enumerate(CARD_FIELDS):
            row = idx // 3
            col = (idx % 3) * 3
            label = QLabel(field+":")
            filter_grid.addWidget(label, row, col)
            if field in numeric_fields:
                min_entry = QLineEdit()
                min_entry.setPlaceholderText("Min")
                max_entry = QLineEdit()
                max_entry.setPlaceholderText("Max")
                filter_grid.addWidget(min_entry, row, col+1)
                filter_grid.addWidget(max_entry, row, col+2)
                min_entry.textChanged.connect(self.update_inventory_list)
                max_entry.textChanged.connect(self.update_inventory_list)
                self.filter_inputs[field] = (min_entry, max_entry)
            else:
                entry = QLineEdit()
                entry.setPlaceholderText("Value(s), comma for OR")
                filter_grid.addWidget(entry, row, col+1, 1, 2)
                entry.textChanged.connect(self.update_inventory_list)
                self.filter_inputs[field] = entry
        filter_group.setLayout(filter_grid)
        inv_layout.addWidget(filter_group)
        # --- End Advanced Filter Grid ---
        self.inv_list = QListWidget()
        inv_layout.addWidget(self.inv_list)
        self.add_selected_btn = QPushButton("Add Selected to Break List")
        self.add_selected_btn.clicked.connect(self.add_selected_to_break)
        inv_layout.addWidget(self.add_selected_btn)
        # New: Random selection controls
        rand_row = QHBoxLayout()
        self.rand_count_input = QLineEdit()
        self.rand_count_input.setPlaceholderText("Number to randomly select")
        self.rand_select_btn = QPushButton("Randomly Select from Filtered")
        self.rand_select_btn.clicked.connect(self.randomly_select_from_filtered)
        rand_row.addWidget(self.rand_count_input)
        rand_row.addWidget(self.rand_select_btn)
        inv_layout.addLayout(rand_row)
        self.tabs.addTab(self.inv_tab, "Inventory")
        # Tab 2: Break List
        self.break_tab = QWidget()
        break_layout = QVBoxLayout(self.break_tab)
        break_layout.addWidget(QLabel("Break/Autobox Items (drag to reorder, double-click to edit):"))
        self.break_list = QListWidget()
        self.break_list.setDragDropMode(QListWidget.InternalMove)
        self.break_list.itemDoubleClicked.connect(self.edit_break_item)
        break_layout.addWidget(self.break_list)
        # --- Summary Section ---
        self.summary_label = QLabel()
        break_layout.addWidget(self.summary_label)
        # --- End Summary Section ---
        btn_row = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_from_break)
        self.duplicate_btn = QPushButton("Duplicate Selected")
        self.duplicate_btn.clicked.connect(self.duplicate_selected_in_break)
        self.add_custom_btn = QPushButton("Add by Scryfall ID")
        self.add_custom_btn.clicked.connect(self.add_by_scryfall_id)
        btn_row.addWidget(self.remove_btn)
        btn_row.addWidget(self.duplicate_btn)
        btn_row.addWidget(self.add_custom_btn)
        break_layout.addLayout(btn_row)
        self.tabs.addTab(self.break_tab, "Break List")
        # Tab 3: Preview/Export
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        preview_layout.addWidget(QLabel("Preview Export (Title/Description):"))
        self.preview_box = QTextEdit()
        self.preview_box.setReadOnly(True)
        self.preview_box.setMinimumHeight(200)
        preview_layout.addWidget(self.preview_box)
        self.remove_from_inv_chk = QCheckBox("Remove exported cards from inventory")
        preview_layout.addWidget(self.remove_from_inv_chk)
        # --- Action Buttons Row ---
        btn_row = QHBoxLayout()
        self.export_btn = QPushButton("Export/Copy for Whatnot")
        self.export_btn.clicked.connect(self.export_break_list)
        self.undo_btn = QPushButton("Undo Remove")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_last_removal)
        self.template_btn = QPushButton("Manage Export Templates")
        self.template_btn.clicked.connect(self.manage_templates)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.undo_btn)
        btn_row.addWidget(self.template_btn)
        btn_row.addStretch()
        preview_layout.addLayout(btn_row)
        self.tabs.addTab(self.preview_tab, "Preview/Export")
        # Tab 4: Help/Settings
        self.help_tab = QWidget()
        help_layout = QVBoxLayout(self.help_tab)
        help_layout.addWidget(QLabel("How to use the Break/Autobox Builder:"))
        help_layout.addWidget(QLabel("1. Filter and select cards from your inventory.\n2. Add them to the break list.\n3. Optionally add by Scryfall ID.\n4. Reorder, edit, or duplicate items.\n5. Preview and export the list for Whatnot.\n6. Optionally remove exported cards from inventory.\n7. You can re-import unused cards later."))
        self.tabs.addTab(self.help_tab, "Help/Settings")
        # Populate inventory list
        self.update_inventory_list()
        self.update_break_list()
        self.update_preview()
    def update_inventory_list(self):
        self.inv_list.clear()
        filters = {}
        for field, widget in self.filter_inputs.items():
            if isinstance(widget, tuple):
                min_val = widget[0].text().strip()
                max_val = widget[1].text().strip()
                if min_val and max_val:
                    filters[field] = f"{min_val}-{max_val}"
                elif min_val:
                    filters[field] = f">={min_val}"
                elif max_val:
                    filters[field] = f"<={max_val}"
            else:
                val = widget.text().strip()
                if val:
                    filters[field] = val
        # Use inventory's filter_cards method for robust filtering
        filtered_cards = self.inventory.filter_cards(filters)
        self.filtered_cards = filtered_cards
        for card in filtered_cards:
            item = QListWidgetItem(f"{card.get('Name', '')} [{card.get('Set name', '')}]")
            item.setData(Qt.UserRole, card)
            self.inv_list.addItem(item)
    def add_selected_to_break(self):
        for item in self.inv_list.selectedItems():
            card = item.data(Qt.UserRole)
            self.break_items.append(card.copy())
        self.update_break_list()
        self.update_preview()
    def randomly_select_from_filtered(self):
        try:
            n = int(self.rand_count_input.text())
        except Exception:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number to select.")
            return
        if n <= 0 or n > len(self.filtered_cards):
            QMessageBox.warning(self, "Invalid Input", f"Number must be between 1 and {len(self.filtered_cards)}.")
            return
        selected = random.sample(self.filtered_cards, n)
        self.break_items.extend([card.copy() for card in selected])
        # Show the selected cards to the user in a scrollable dialog
        names = [f"{c.get('Name', '')} [{c.get('Set name', '')}]" for c in selected]
        dlg = ScrollableListDialog("Randomly Selected", names, self)
        dlg.exec()
        self.update_break_list()
        self.update_preview()
    def update_break_list(self):
        self.break_list.clear()
        for card in self.break_items:
            item = QListWidgetItem(f"{card.get('Name', '')} [{card.get('Set name', '')}]" )
            item.setData(Qt.UserRole, card)
            self.break_list.addItem(item)
        # --- Update Summary ---
        purchase_prices = []
        whatnot_prices = []
        for card in self.break_items:
            try:
                price = float(str(card.get('Purchase price', '')).replace('$','').replace(',',''))
                purchase_prices.append(price)
            except Exception:
                pass
            try:
                wprice = float(str(card.get('Whatnot price', '')).replace('$','').replace(',',''))
                whatnot_prices.append(wprice)
            except Exception:
                pass
        total_purchase = sum(purchase_prices)
        avg_purchase = (sum(purchase_prices)/len(purchase_prices)) if purchase_prices else 0
        total_whatnot = sum(whatnot_prices)
        avg_whatnot = (sum(whatnot_prices)/len(whatnot_prices)) if whatnot_prices else 0
        self.summary_label.setText(
            f"<b>Totals:</b> Purchase price: ${total_purchase:.2f} (avg: ${avg_purchase:.2f}) | "
            f"Whatnot price: ${total_whatnot:.2f} (avg: ${avg_whatnot:.2f})"
        )
        # --- End Update Summary ---
    def remove_selected_from_break(self):
        for item in self.break_list.selectedItems():
            idx = self.break_list.row(item)
            if idx >= 0:
                self.break_items.pop(idx)
        self.update_break_list()
        self.update_preview()
    def duplicate_selected_in_break(self):
        for item in self.break_list.selectedItems():
            card = item.data(Qt.UserRole)
            self.break_items.append(card.copy())
        self.update_break_list()
        self.update_preview()
    def edit_break_item(self, item):
        card = item.data(Qt.UserRole)
        from ui.dialogs.edit_card import EditCardDialog
        dlg = EditCardDialog(card, all_fields=list(card.keys()), parent=self)
        if dlg.exec():
            updated = dlg.get_card()
            idx = self.break_list.row(item)
            self.break_items[idx] = updated
            self.update_break_list()
            self.update_preview()
    def add_by_scryfall_id(self):
        scry_id, ok = QInputDialog.getText(self, "Add by Scryfall ID", "Enter Scryfall ID:")
        if not ok or not scry_id.strip():
            return
        data = fetch_scryfall_data(scry_id.strip())
        if not data:
            QMessageBox.warning(self, "Not Found", "No card found for that Scryfall ID.")
            return
        self.break_items.append(data)
        self.update_break_list()
        self.update_preview()
    def update_preview(self):
        # Show preview using current template if set, else fallback to Name/Set name
        if self.export_template:
            title_fields = self.export_template.get('title_fields', [])
            desc_fields = self.export_template.get('desc_fields', [])
        else:
            title_fields = ["Name"]
            desc_fields = ["Set name"]
        # Build preview rows: each row is [title, description]
        rows = []
        for card in self.break_items:
            title_parts = []
            for f in title_fields:
                val = card.get(f, "")
                if (not val or str(val).strip() == "") and card.get("Scryfall ID", ""):
                    scry_data = fetch_scryfall_data(card["Scryfall ID"])
                    if scry_data and f in scry_data:
                        val = scry_data[f]
                if not val or str(val).strip() == "":
                    val = "(none)"
                title_parts.append(str(val).title())
            title = " - ".join(title_parts).replace('\n', ' ').replace('\t', ' ').strip()
            desc_lines = []
            for f in desc_fields:
                val = card.get(f, "")
                # If field is empty, try to fetch from Scryfall
                if (not val or str(val).strip() == "") and card.get("Scryfall ID", ""):
                    scry_data = fetch_scryfall_data(card["Scryfall ID"])
                    if scry_data and f in scry_data:
                        val = scry_data[f]
                # For oracle_text, flatten newlines
                if f == "oracle_text" and val:
                    val = str(val).replace("\n", " ").replace("\r", " ")
                if not val or str(val).strip() == "":
                    val = "(none)"
                desc_lines.append(f"• {f.replace('_', ' ').title()}: {val}")
            desc = "\n".join(desc_lines)
            rows.append([title, desc])
        # Format as a table-like preview
        preview_lines = [f"{'Title':<40} | Description"]
        preview_lines.append("-"*80)
        for title, desc in rows:
            desc_lines = desc.split("\n")
            preview_lines.append(f"{title[:40]:<40} | {desc_lines[0] if desc_lines else ''}")
            for line in desc_lines[1:]:
                preview_lines.append(f"{'':<40} | {line}")
        self.preview_box.setPlainText("\n".join(preview_lines))
    def export_break_list(self):
        # Use ExportItemListingFieldsDialog for title/description selection
        all_fields = set()
        for card in self.break_items:
            all_fields.update(card.keys())
        all_fields = sorted(all_fields)
        # If a template is set, use it; else prompt
        if self.export_template:
            title_fields = self.export_template.get('title_fields', [])
            desc_fields = self.export_template.get('desc_fields', [])
        else:
            dlg = ExportItemListingFieldsDialog(all_fields, self)
            if not dlg.exec():
                return
            title_fields, desc_fields = dlg.get_fields()
            # Optionally save as template
            save = QMessageBox.question(self, "Save Template?", "Save these fields as a new export template?", QMessageBox.Yes | QMessageBox.No)
            if save == QMessageBox.Yes:
                name, ok = QInputDialog.getText(self, "Template Name", "Enter a name for this template:")
                if ok and name.strip():
                    self.templates[name.strip()] = {'title_fields': title_fields, 'desc_fields': desc_fields}
                    self.save_templates()
                    self.export_template = self.templates[name.strip()]
            # Always update preview to reflect the latest selection
            self.export_template = {'title_fields': title_fields, 'desc_fields': desc_fields}
            self.update_preview()
        # Build export rows: each row is [title, description] (no tabs/newlines inside cells)
        rows = []
        for card in self.break_items:
            title_parts = []
            for f in title_fields:
                val = card.get(f, "")
                if (not val or str(val).strip() == "") and card.get("Scryfall ID", ""):
                    scry_data = fetch_scryfall_data(card["Scryfall ID"])
                    if scry_data and f in scry_data:
                        val = scry_data[f]
                if not val or str(val).strip() == "":
                    val = "(none)"
                title_parts.append(str(val).title())
            title = " - ".join(title_parts).replace('\n', ' ').replace('\t', ' ').strip()
            desc_lines = []
            for f in desc_fields:
                val = card.get(f, "")
                # If field is empty, try to fetch from Scryfall
                if (not val or str(val).strip() == "") and card.get("Scryfall ID", ""):
                    scry_data = fetch_scryfall_data(card["Scryfall ID"])
                    if scry_data and f in scry_data:
                        val = scry_data[f]
                # For oracle_text, flatten newlines
                if f == "oracle_text" and val:
                    val = str(val).replace("\n", " ").replace("\r", " ")
                if not val or str(val).strip() == "":
                    val = "(none)"
                desc_lines.append(f"• {f.replace('_', ' ').title()}: {val}")
            desc = "\n".join(desc_lines)
            rows.append([title, desc])
        # Copy to clipboard as CSV
        import pyperclip
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Title", "Description"])
        for row in rows:
            writer.writerow(row)
        csv_text = output.getvalue()
        pyperclip.copy(csv_text)
        # Optionally save as CSV
        fname, _ = QFileDialog.getSaveFileName(self, "Export Break List", "break_list.csv", "CSV Files (*.csv)")
        if fname:
            with open(fname, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_text)
        # After export, ask if user wants to remove from inventory (if not already checked)
        if not self.remove_from_inv_chk.isChecked():
            remove = QMessageBox.question(self, "Remove from Inventory?", "Do you want to remove the exported cards from inventory?", QMessageBox.Yes | QMessageBox.No)
            if remove == QMessageBox.Yes:
                self._undo_inventory = copy.deepcopy(self.inventory.get_all_cards())
                self.inventory.remove_cards(self.break_items)
                self.removed_from_inventory = self.break_items.copy()
                self.undo_btn.setEnabled(True)
                QMessageBox.information(self, "Removed", f"{len(self.break_items)} cards removed from inventory. You can undo this action.")
        else:
            self._undo_inventory = copy.deepcopy(self.inventory.get_all_cards())
            self.inventory.remove_cards(self.break_items)
            self.removed_from_inventory = self.break_items.copy()
            self.undo_btn.setEnabled(True)
            QMessageBox.information(self, "Removed", f"{len(self.break_items)} cards removed from inventory. You can undo this action.")
        QMessageBox.information(self, "Exported", "Break list exported and copied to clipboard.")
    def manage_templates(self):
        # Dialog to select, delete, or set a template
        names = list(self.templates.keys())
        if not names:
            QMessageBox.information(self, "No Templates", "No export templates saved yet.")
            return
        name, ok = QInputDialog.getItem(self, "Select Template", "Choose a template to use: (or delete)", names, editable=False)
        if ok and name:
            action, ok2 = QInputDialog.getItem(self, "Action", f"Use or delete template '{name}'?", ["Use", "Delete"], editable=False)
            if ok2 and action == "Use":
                self.export_template = self.templates[name]
                QMessageBox.information(self, "Template Set", f"Template '{name}' will be used for export.")
                self.update_preview()
            elif ok2 and action == "Delete":
                del self.templates[name]
                self.save_templates()
                if self.export_template and self.export_template == self.templates.get(name):
                    self.export_template = None
                QMessageBox.information(self, "Deleted", f"Template '{name}' deleted.")
    def load_templates(self):
        path = os.path.join(os.path.dirname(__file__), '../../break_export_templates.json')
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    def save_templates(self):
        path = os.path.join(os.path.dirname(__file__), '../../break_export_templates.json')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    def reimport_removed(self):
        # Optionally re-import removed cards
        for card in self.removed_from_inventory:
            self.inventory.add_card(card)
        self.removed_from_inventory = []
        QMessageBox.information(self, "Re-imported", "Removed cards re-imported to inventory.")
    def undo_last_removal(self):
        if self._undo_inventory is not None:
            self.inventory.load_cards(self._undo_inventory)
            self._undo_inventory = None
            self.undo_btn.setEnabled(False)
            QMessageBox.information(self, "Undo", "Inventory restored to before last removal.")
            self.update_inventory_list()
            self.update_break_list()
            self.update_preview()

class ScrollableListDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setMaximumHeight(600)
        layout = QVBoxLayout(self)
        label = QLabel("Selected cards:")
        layout.addWidget(label)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText("\n".join(items))
        text.setMinimumHeight(300)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons) 