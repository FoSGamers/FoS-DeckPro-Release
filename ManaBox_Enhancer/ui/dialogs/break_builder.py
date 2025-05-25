from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QCheckBox, QFileDialog, QInputDialog, QWidget, QFormLayout
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
        # Dynamic filter row
        self.filter_fields = self._get_all_inventory_fields()
        self.filter_inputs = {}
        filter_form = QFormLayout()
        for field in self.filter_fields:
            le = QLineEdit()
            le.setPlaceholderText(f"Filter {field}")
            le.textChanged.connect(self.update_inventory_list)
            self.filter_inputs[field] = le
            filter_form.addRow(QLabel(field+":"), le)
        inv_layout.addLayout(filter_form)
        self.inv_list = QListWidget()
        inv_layout.addWidget(self.inv_list)
        self.add_selected_btn = QPushButton("Add Selected to Break List")
        self.add_selected_btn.clicked.connect(self.add_selected_to_break)
        inv_layout.addWidget(self.add_selected_btn)
        # Random selection controls
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
        # AND all filters
        filters = {field: le.text().strip().lower() for field, le in self.filter_inputs.items() if le.text().strip()}
        self.filtered_cards = []
        for card in self.inventory.get_all_cards():
            match = True
            for field, val in filters.items():
                if val not in str(card.get(field, "")).lower():
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
        # Show the selected cards to the user
        names = [f"{c.get('Name', '')} [{c.get('Set name', '')}]" for c in selected]
        QMessageBox.information(self, "Randomly Selected", "Selected cards:\n" + "\n".join(names))
        self.update_break_list()
        self.update_preview()
    def update_break_list(self):
        self.break_list.clear()
        for card in self.break_items:
            item = QListWidgetItem(f"{card.get('Name', '')} [{card.get('Set name', '')}]" )
            item.setData(Qt.UserRole, card)
            self.break_list.addItem(item)
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