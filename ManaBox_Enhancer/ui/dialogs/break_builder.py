from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QCheckBox, QFileDialog, QInputDialog, QWidget, QFormLayout, QGroupBox, QGridLayout, QSplitter, QScrollArea, QTextEdit, QDialogButtonBox
from PySide6.QtCore import Qt
from models.scryfall_api import fetch_scryfall_data
import random

class BreakBuilderDialog(QDialog):
    """
    Modular dialog for building Whatnot breaks/autoboxes from inventory.
    """
    def __init__(self, inventory, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Break/Autobox Builder")
        self.resize(900, 600)
        self.inventory = inventory
        self.break_items = []  # List of dicts (cards/items)
        self.removed_from_inventory = []
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        # Tab 1: Inventory Search/Select
        self.inv_tab = QWidget()
        inv_layout = QVBoxLayout(self.inv_tab)
        inv_layout.addWidget(QLabel("Filter and select cards from inventory:"))
        
        # --- Improved Main Layout with Splitter ---
        main_splitter = QSplitter()
        main_splitter.setOrientation(Qt.Horizontal)
        # Left: Filters (in a scroll area)
        filter_widget = QWidget()
        filter_vbox = QVBoxLayout(filter_widget)
        filter_vbox.addWidget(QLabel("Card Filters"))
        filter_group = QGroupBox()
        filter_grid = QGridLayout()
        self.filter_fields = self._get_all_inventory_fields()
        self.filter_inputs = {}
        self.numeric_fields = {f for f in self.filter_fields if any(x in f.lower() for x in ["price", "quantity", "number", "count"])}
        col_count = 1  # One column for better vertical scrolling
        for idx, field in enumerate(self.filter_fields):
            row = idx
            if field in self.numeric_fields:
                min_le = QLineEdit()
                min_le.setPlaceholderText(f"Min {field}")
                min_le.textChanged.connect(self.update_inventory_list)
                max_le = QLineEdit()
                max_le.setPlaceholderText(f"Max {field}")
                max_le.textChanged.connect(self.update_inventory_list)
                self.filter_inputs[field] = (min_le, max_le)
                filter_grid.addWidget(QLabel(field+":"), row, 0)
                filter_grid.addWidget(min_le, row, 1)
                filter_grid.addWidget(QLabel("to"), row, 2)
                filter_grid.addWidget(max_le, row, 3)
            else:
                le = QLineEdit()
                le.setPlaceholderText(f"Filter {field} (comma=OR)")
                le.textChanged.connect(self.update_inventory_list)
                self.filter_inputs[field] = le
                filter_grid.addWidget(QLabel(field+":"), row, 0)
                filter_grid.addWidget(le, row, 1, 1, 3)
        filter_group.setLayout(filter_grid)
        filter_vbox.addWidget(filter_group)
        filter_vbox.addStretch()
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_scroll.setWidget(filter_widget)
        main_splitter.addWidget(filter_scroll)
        # Right: Card list and action buttons
        right_widget = QWidget()
        right_vbox = QVBoxLayout(right_widget)
        right_vbox.addWidget(QLabel("Filtered Cards:"))
        self.inv_list = QListWidget()
        self.inv_list.setMinimumHeight(200)
        right_vbox.addWidget(self.inv_list, stretch=1)
        btn_row = QHBoxLayout()
        self.add_selected_btn = QPushButton("Add Selected to Break List")
        self.add_selected_btn.clicked.connect(self.add_selected_to_break)
        btn_row.addWidget(self.add_selected_btn)
        self.rand_count_input = QLineEdit()
        self.rand_count_input.setPlaceholderText("Number to randomly select")
        self.rand_count_input.setMaximumWidth(150)
        btn_row.addWidget(self.rand_count_input)
        self.rand_select_btn = QPushButton("Randomly Select from Filtered")
        self.rand_select_btn.clicked.connect(self.randomly_select_from_filtered)
        btn_row.addWidget(self.rand_select_btn)
        btn_row.addStretch()
        right_vbox.addLayout(btn_row)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([300, 600])
        inv_layout.addWidget(main_splitter)
        # --- End Improved Main Layout ---
        
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
        self.preview_box = QLineEdit()
        self.preview_box.setReadOnly(True)
        preview_layout.addWidget(self.preview_box)
        self.export_btn = QPushButton("Export/Copy for Whatnot")
        self.export_btn.clicked.connect(self.export_break_list)
        self.remove_from_inv_chk = QCheckBox("Remove exported cards from inventory")
        preview_layout.addWidget(self.remove_from_inv_chk)
        preview_layout.addWidget(self.export_btn)
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
    def _get_all_inventory_fields(self):
        # Get all unique fields from inventory
        fields = set()
        for card in self.inventory.get_all_cards():
            fields.update(card.keys())
        return sorted(fields)
    def update_inventory_list(self):
        self.inv_list.clear()
        filters = {}
        for field, widget in self.filter_inputs.items():
            if isinstance(widget, tuple):
                min_val = widget[0].text().strip()
                max_val = widget[1].text().strip()
                if min_val or max_val:
                    filters[field] = (min_val, max_val)
            else:
                val = widget.text().strip()
                if val:
                    filters[field] = val
        self.filtered_cards = []
        for card in self.inventory.get_all_cards():
            match = True
            for field, val in filters.items():
                if isinstance(val, tuple):
                    # Numeric range filter
                    min_val, max_val = val
                    try:
                        card_val = float(card.get(field, 0))
                    except Exception:
                        match = False
                        break
                    if min_val:
                        try:
                            if card_val < float(min_val):
                                match = False
                                break
                        except Exception:
                            pass
                    if max_val:
                        try:
                            if card_val > float(max_val):
                                match = False
                                break
                        except Exception:
                            pass
                else:
                    # OR filter for comma-separated values
                    or_values = [v.strip().lower() for v in val.split(",") if v.strip()]
                    card_val = str(card.get(field, "")).lower()
                    if not any(ov in card_val for ov in or_values):
                        match = False
                        break
            if match:
                item = QListWidgetItem(f"{card.get('Name', '')} [{card.get('Set name', '')}]")
                item.setData(Qt.UserRole, card)
                self.inv_list.addItem(item)
                self.filtered_cards.append(card)
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
        # For now, just show Title/Description for all items
        lines = []
        for card in self.break_items:
            title = card.get("Name", "")
            desc = card.get("Set name", "")
            lines.append(f"{title}\t{desc}")
        self.preview_box.setText("\n".join(lines))
    def export_break_list(self):
        # Copy to clipboard and/or save as CSV
        import pyperclip
        lines = []
        for card in self.break_items:
            title = card.get("Name", "")
            desc = card.get("Set name", "")
            lines.append(f"{title}\t{desc}")
        text = "\n".join(lines)
        pyperclip.copy(text)
        # Optionally save as CSV
        fname, _ = QFileDialog.getSaveFileName(self, "Export Break List", "break_list.csv", "CSV Files (*.csv)")
        if fname:
            with open(fname, 'w', encoding='utf-8', newline='') as f:
                for line in lines:
                    f.write(line + '\n')
        # After export, ask if user wants to remove from inventory (if not already checked)
        if not self.remove_from_inv_chk.isChecked():
            remove = QMessageBox.question(self, "Remove from Inventory?", "Do you want to remove the exported cards from inventory?", QMessageBox.Yes | QMessageBox.No)
            if remove == QMessageBox.Yes:
                for card in self.break_items:
                    self.inventory.remove_card(card)
                self.removed_from_inventory = self.break_items.copy()
                QMessageBox.information(self, "Removed", f"{len(self.break_items)} cards removed from inventory.")
        else:
            for card in self.break_items:
                self.inventory.remove_card(card)
            self.removed_from_inventory = self.break_items.copy()
            QMessageBox.information(self, "Removed", f"{len(self.break_items)} cards removed from inventory.")
        QMessageBox.information(self, "Exported", "Break list exported and copied to clipboard.")
    def reimport_removed(self):
        # Optionally re-import removed cards
        for card in self.removed_from_inventory:
            self.inventory.add_card(card)
        self.removed_from_inventory = []
        QMessageBox.information(self, "Re-imported", "Removed cards re-imported to inventory.")

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