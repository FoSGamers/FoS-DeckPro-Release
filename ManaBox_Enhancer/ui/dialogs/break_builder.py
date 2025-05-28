from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QCheckBox, QFileDialog, QInputDialog, QWidget, QFormLayout, QScrollArea, QSizePolicy, QFrame, QSpinBox, QDoubleSpinBox, QGroupBox, QAbstractItemView, QSplitter)
from PySide6.QtCore import Qt
from models.scryfall_api import fetch_scryfall_data
import random
import json
from ui.card_table import CardTableView
from ui.filter_overlay import FilterOverlay
from ui.image_preview import ImagePreview
from ui.card_details import CardDetails

# Centralized config/constants for break builder
BREAK_BUILDER_CONFIG = {
    'rule_fields': [
        {'name': 'Price', 'type': 'float', 'label': 'Price ($)', 'min': 0, 'max': 10000, 'step': 0.01},
        {'name': 'Rarity', 'type': 'str', 'label': 'Rarity', 'choices': ['common', 'uncommon', 'rare', 'mythic']},
        {'name': 'Set name', 'type': 'str', 'label': 'Set Name'},
        # Add more fields as needed
    ],
    'max_rules': 10,
    'template_file': 'break_templates.json',
}

class BreakRuleWidget(QWidget):
    """
    Widget for a single rule in the break builder.
    Allows user to specify count/percentage and filter criteria.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.count_type = QComboBox()
        self.count_type.addItems(["Count", "% of available"])
        self.count_type.setToolTip("Choose whether to select a fixed number or a percentage of cards matching this rule.")
        self.count_value = QSpinBox()
        self.count_value.setMinimum(1)
        self.count_value.setMaximum(1000)
        self.percent_value = QDoubleSpinBox()
        self.percent_value.setMinimum(1)
        self.percent_value.setMaximum(100)
        self.percent_value.setSuffix("%")
        self.percent_value.setVisible(False)
        self.count_type.currentIndexChanged.connect(self._toggle_count_type)
        layout.addWidget(QLabel("Select:"))
        layout.addWidget(self.count_type)
        layout.addWidget(self.count_value)
        layout.addWidget(self.percent_value)
        # Field selectors
        self.field_selectors = {}
        for field in BREAK_BUILDER_CONFIG['rule_fields']:
            if field['type'] == 'float':
                min_box = QDoubleSpinBox()
                min_box.setMinimum(field.get('min', 0))
                min_box.setMaximum(field.get('max', 10000))
                min_box.setSingleStep(field.get('step', 0.01))
                min_box.setPrefix(">$ ")
                max_box = QDoubleSpinBox()
                max_box.setMinimum(field.get('min', 0))
                max_box.setMaximum(field.get('max', 10000))
                max_box.setSingleStep(field.get('step', 0.01))
                max_box.setPrefix("< $")
                layout.addWidget(QLabel(field['label']))
                layout.addWidget(min_box)
                layout.addWidget(max_box)
                self.field_selectors[field['name']] = (min_box, max_box)
            elif field['type'] == 'str' and 'choices' in field:
                combo = QComboBox()
                combo.addItem("")  # Allow blank (no filter)
                combo.addItems(field['choices'])
                layout.addWidget(QLabel(field['label']))
                layout.addWidget(combo)
                self.field_selectors[field['name']] = combo
            else:
                edit = QLineEdit()
                edit.setPlaceholderText(f"Filter {field['label']}")
                layout.addWidget(QLabel(field['label']))
                layout.addWidget(edit)
                self.field_selectors[field['name']] = edit
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setStyleSheet("color: red;")
        layout.addWidget(self.remove_btn)
        layout.addStretch(1)
    def _toggle_count_type(self, idx):
        if idx == 0:
            self.count_value.setVisible(True)
            self.percent_value.setVisible(False)
        else:
            self.count_value.setVisible(False)
            self.percent_value.setVisible(True)
    def get_rule(self):
        rule = {}
        rule['count_type'] = self.count_type.currentText()
        rule['count'] = self.count_value.value() if self.count_type.currentIndex() == 0 else self.percent_value.value()
        for field, widget in self.field_selectors.items():
            if isinstance(widget, tuple):
                min_val = widget[0].value()
                max_val = widget[1].value()
                rule[field] = (min_val, max_val)
            elif isinstance(widget, QComboBox):
                rule[field] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                rule[field] = widget.text().strip()
        return rule
    def set_rule(self, rule):
        if rule.get('count_type') == 'Count':
            self.count_type.setCurrentIndex(0)
            self.count_value.setValue(int(rule.get('count', 1)))
        else:
            self.count_type.setCurrentIndex(1)
            self.percent_value.setValue(float(rule.get('count', 1)))
        for field, widget in self.field_selectors.items():
            if field in rule:
                val = rule[field]
                if isinstance(widget, tuple):
                    widget[0].setValue(val[0])
                    widget[1].setValue(val[1])
                elif isinstance(widget, QComboBox):
                    idx = widget.findText(val)
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                elif isinstance(widget, QLineEdit):
                    widget.setText(val)

class BreakBuilderDialog(QDialog):
    """
    Modular dialog for building Whatnot breaks/autoboxes from inventory.
    Modernized for resizable, sidebar-based UI and advanced curation.
    Now includes a powerful rule-based break builder for advanced users.
    Allows user to specify the total number of cards needed for the break.
    Curated card selection uses a full-featured CardTableView with filtering, images, and details.
    """
    def __init__(self, inventory, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Break/Autobox Builder")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.inventory = inventory
        self.break_items = []  # List of dicts (cards/items)
        self.curated_cards = []  # List of curated card dicts
        self.removed_from_inventory = []
        self.rules = []  # List of rule dicts
        self.rule_widgets = []  # List of BreakRuleWidget
        layout = QVBoxLayout(self)
        # --- Total cards needed input ---
        total_row = QHBoxLayout()
        total_row.addWidget(QLabel("Total cards needed for break:"))
        self.total_cards_input = QSpinBox()
        self.total_cards_input.setMinimum(1)
        self.total_cards_input.setMaximum(10000)
        self.total_cards_input.setValue(30)
        self.total_cards_input.setToolTip("Specify the total number of cards you want in the break (from curated + rules).")
        total_row.addWidget(self.total_cards_input)
        total_row.addStretch(1)
        layout.addLayout(total_row)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        # Tab 1: Inventory Search/Select (now with CardTableView)
        self.inv_tab = QWidget()
        inv_main_layout = QHBoxLayout(self.inv_tab)
        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        # Left: Filters + Table + Pagination
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        # Sidebar for filters
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(340)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.addWidget(QLabel("Filters"))
        # Scroll area for filters
        filter_scroll = QScrollArea()
        filter_scroll.setWidgetResizable(True)
        filter_widget = QWidget()
        filter_form = QFormLayout(filter_widget)
        self.filter_fields = self._get_all_inventory_fields()
        self.filter_inputs = {}
        for field in self.filter_fields:
            le = QLineEdit()
            le.setPlaceholderText(f"Filter {field}")
            le.textChanged.connect(self.update_table_filter)
            self.filter_inputs[field] = le
            filter_form.addRow(QLabel(field+":"), le)
        filter_widget.setLayout(filter_form)
        filter_scroll.setWidget(filter_widget)
        sidebar_layout.addWidget(filter_scroll, 1)
        # Active filter chips
        self.active_filter_chips = QWidget()
        self.active_filter_chips_layout = QHBoxLayout(self.active_filter_chips)
        self.active_filter_chips_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(self.active_filter_chips)
        # Clear all filters button
        self.clear_filters_btn = QPushButton("Clear All Filters")
        self.clear_filters_btn.clicked.connect(self.clear_all_filters)
        sidebar_layout.addWidget(self.clear_filters_btn)
        sidebar_layout.addStretch(1)
        left_layout.addWidget(sidebar)
        # CardTableView for inventory
        from ui.main_window import MainWindow  # for columns
        self.columns = MainWindow.default_columns if hasattr(MainWindow, 'default_columns') else [
            "Name", "Set name", "Set code", "Collector number", "Rarity",
            "Condition", "Foil", "Language", "Purchase price", "Whatnot price"
        ]
        self.card_table = CardTableView(self.inventory, self.columns)
        self.card_table.setSelectionMode(QAbstractItemView.MultiSelection)
        left_layout.addWidget(self.card_table)
        # Pagination widget below the table
        left_layout.addWidget(self.card_table.pagination_widget)
        left_widget.setLayout(left_layout)
        # Filter overlay for fast searching (as in main window)
        self.filter_overlay = FilterOverlay(self.card_table, self.columns)
        self.filter_overlay.show()
        for col, filt in self.filter_overlay.filters.items():
            filt.textChanged.connect(self.update_table_filter)
        # Right: Image preview and card details in a vertical splitter
        right_splitter = QSplitter()
        right_splitter.setOrientation(Qt.Vertical)
        self.image_preview = ImagePreview()
        self.image_preview.setMinimumHeight(120)
        self.image_preview.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.card_details = CardDetails()
        self.card_details.setMinimumHeight(120)
        self.card_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_splitter.addWidget(self.image_preview)
        right_splitter.addWidget(self.card_details)
        right_splitter.setSizes([200, 400])
        right_splitter.setChildrenCollapsible(False)
        right_splitter.setHandleWidth(8)
        right_splitter.setMinimumWidth(100)
        right_splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Compose splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_splitter)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        inv_main_layout.addWidget(splitter)
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
        # Generate Break List button
        self.generate_btn = QPushButton("Generate Break List")
        self.generate_btn.clicked.connect(self.generate_break_list)
        inv_main_layout.addWidget(self.generate_btn)
        # Preview of final break list
        self.break_preview_label = QLabel("Break List Preview:")
        inv_main_layout.addWidget(self.break_preview_label)
        self.break_preview_box = QLineEdit()
        self.break_preview_box.setReadOnly(True)
        inv_main_layout.addWidget(self.break_preview_box)
        # --- Curated Table Section ---
        # Place below the inventory splitter, in a labeled, resizable section
        self.curated_section = QWidget()
        curated_layout = QVBoxLayout(self.curated_section)
        curated_layout.addWidget(QLabel("Curated Cards (drag to reorder):"))
        self.curated_table = CardTableView(self, self.columns)
        self.curated_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.curated_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        curated_layout.addWidget(self.curated_table)
        # Add to main layout below the splitter
        self.layout().addWidget(self.curated_section)
        # Track the current filtered inventory pool
        self.filtered_inventory = self.inventory.get_all_cards()
        # Add a UI hint for users
        self.filter_hint_label = QLabel("Rules will only select from cards currently visible in the inventory table.")
        self.filter_hint_label.setStyleSheet("color: #888; font-style: italic;")
        inv_main_layout.addWidget(self.filter_hint_label)
        # Populate inventory list
        self.update_break_list()
        self.update_preview()
    def _get_all_inventory_fields(self):
        # Get all unique fields from inventory
        fields = set()
        for card in self.inventory.get_all_cards():
            fields.update(card.keys())
        return sorted(fields)
    def add_selected_to_curated(self):
        selected_rows = self.card_table.selectionModel().selectedRows()
        for idx in selected_rows:
            card = self.card_table.cards[idx.row() - 1]
            if card not in self.curated_cards:
                self.curated_cards.append(card)
        self.update_curated_table()
    def remove_selected_from_curated(self):
        selected_rows = self.curated_table.selectionModel().selectedRows()
        for idx in sorted(selected_rows, reverse=True):
            if 0 <= idx.row() - 1 < len(self.curated_cards):
                self.curated_cards.pop(idx.row() - 1)
        self.update_curated_table()
    def update_curated_table(self):
        self.curated_table.update_cards(self.curated_cards)
    def generate_break_list(self):
        """
        Combine curated and rule-based selections, deduplicate, and match total.
        Show preview with sections for curated and each rule-based group.
        Handle errors if not enough cards are available for any rule.
        Rules only operate on the currently filtered inventory pool.
        """
        total_needed = self.total_cards_input.value()
        curated = list(self.curated_cards)
        # Use only the filtered pool for rule-based selection
        all_cards = self.filtered_inventory
        used_ids = set(id(c) for c in curated)
        rule_cards_by_rule = []
        # Advanced rule-based selection
        for rule_widget in self.rule_widgets:
            rule = rule_widget.get_rule()
            # Build filter for this rule
            filtered = []
            for card in all_cards:
                if id(card) in used_ids:
                    continue
                match = True
                for field, val in rule.items():
                    if field in ("count_type", "count"):
                        continue
                    if isinstance(val, tuple):
                        min_val, max_val = val
                        try:
                            card_val = float(card.get(field, 0))
                        except Exception:
                            card_val = 0
                        if not (min_val <= card_val <= max_val):
                            match = False
                            break
                    elif isinstance(val, str) and val:
                        if str(card.get(field, "")).lower() != val.lower():
                            match = False
                            break
                if match:
                    filtered.append(card)
            # Determine how many to select
            n = 0
            if rule.get("count_type") == "Count":
                n = int(rule.get("count", 1))
            else:
                percent = float(rule.get("count", 1))
                n = max(1, int(len(filtered) * percent / 100))
            if n > len(filtered):
                QMessageBox.warning(self, "Not Enough Cards", f"Rule for {rule} requested {n} cards but only {len(filtered)} available. Using all available.")
                n = len(filtered)
            selected = filtered[:n]
            for card in selected:
                used_ids.add(id(card))
            rule_cards_by_rule.append((rule, selected))
        # Combine curated and rule-based, fill with randoms if needed
        final_list = list(curated)
        for rule, cards in rule_cards_by_rule:
            final_list.extend(cards)
        # Fill with randoms if still not enough
        if len(final_list) < total_needed:
            for card in all_cards:
                if id(card) not in used_ids:
                    final_list.append(card)
                    used_ids.add(id(card))
                    if len(final_list) >= total_needed:
                        break
        # Show preview with sections
        lines = []
        if curated:
            lines.append("Curated Cards:")
            lines.extend([f"  {c.get('Name', '')} [{c.get('Set name', '')}]" for c in curated])
        for i, (rule, cards) in enumerate(rule_cards_by_rule):
            lines.append(f"Rule {i+1} ({rule.get('count_type')} {rule.get('count')}):")
            lines.extend([f"  {c.get('Name', '')} [{c.get('Set name', '')}]" for c in cards])
        if len(final_list) > len(curated) + sum(len(cards) for _, cards in rule_cards_by_rule):
            lines.append("Filler Cards:")
            lines.extend([f"  {c.get('Name', '')} [{c.get('Set name', '')}]" for c in final_list[len(curated) + sum(len(cards) for _, cards in rule_cards_by_rule):]])
        self.break_preview_box.setText("\n".join(lines[:total_needed + 10]))  # Show a bit more than needed for clarity
    def update_table_filter(self):
        filters = {col: self.filter_overlay.filters[col].text() for col in self.columns}
        filtered = self.inventory.filter_cards(filters)
        self.filtered_inventory = filtered  # Store the filtered pool
        self.card_table.update_cards(filtered)
        self.card_table.repaint()
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
    def clear_all_filters(self):
        for le in self.filter_inputs.values():
            le.clear()
        self.update_table_filter() 