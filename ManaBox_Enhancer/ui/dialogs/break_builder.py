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
        # All required attributes must be initialized before any method that uses them (regression rule)
        self.filtered_inventory = self.inventory.get_all_cards()
        self.break_items = []  # List of dicts (cards/items)
        self.curated_cards = []  # List of curated card dicts
        self.rules = []  # List of rule dicts
        self.rule_widgets = []  # List of BreakRuleWidget
        layout = QVBoxLayout(self)
        # --- Step-by-step workflow guidance at the top ---
        workflow_label = QLabel("<b>Step 1:</b> Filter inventory & select cards → <b>Step 2:</b> Curate must-haves → <b>Step 3:</b> Set rules → <b>Step 4:</b> Generate break")
        workflow_label.setStyleSheet("font-size: 13px; margin-bottom: 8px;")
        layout.insertWidget(0, workflow_label)
        # --- Total cards input (must be initialized before any method uses it) ---
        total_row = QHBoxLayout()
        total_label = QLabel("Total cards needed for break:")
        self.total_cards_input = QSpinBox()
        self.total_cards_input.setMinimum(1)
        self.total_cards_input.setMaximum(10000)
        self.total_cards_input.setValue(30)
        self.total_cards_input.setToolTip("Specify the total number of cards needed for the break.")
        self.total_cards_input.valueChanged.connect(self.generate_break_list)
        total_row.addWidget(total_label)
        total_row.addWidget(self.total_cards_input)
        layout.insertLayout(1, total_row)

        # --- Inventory Section ---
        inventory_group = QGroupBox("1. Inventory (Filter & Select)")
        inventory_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bbb; margin-top: 8px; padding: 8px; } ")
        inv_group_layout = QVBoxLayout(inventory_group)
        # Filter sidebar with background
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
        inv_group_layout.addWidget(sidebar)
        # CardTableView for inventory
        from ui.main_window import MainWindow  # for columns
        self.columns = MainWindow.default_columns if hasattr(MainWindow, 'default_columns') else [
            "Name", "Set name", "Set code", "Collector number", "Rarity",
            "Condition", "Foil", "Language", "Purchase price", "Whatnot price"
        ]
        self.card_table = CardTableView(self.inventory, self.columns)
        self.card_table.setSelectionMode(QAbstractItemView.MultiSelection)
        inv_group_layout.addWidget(self.card_table)
        # Pagination widget below the table
        inv_group_layout.addWidget(self.card_table.pagination_widget)
        # Add inventory group to main layout
        layout.insertWidget(1, inventory_group)

        # --- Curated Cards Section ---
        curated_group = QGroupBox("2. Curated Cards (Guaranteed in Break)")
        curated_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bbb; margin-top: 8px; padding: 8px; } ")
        curated_layout = QVBoxLayout(curated_group)
        curated_layout.addWidget(QLabel("Drag to reorder. Remove to exclude from break."))
        # Add/Remove buttons for curated list
        curated_btn_row = QHBoxLayout()
        self.add_to_curated_btn = QPushButton("Add Selected to Curated")
        self.add_to_curated_btn.clicked.connect(self.add_selected_to_curated)
        self.remove_from_curated_btn = QPushButton("Remove Selected from Curated")
        self.remove_from_curated_btn.clicked.connect(self.remove_selected_from_curated)
        curated_btn_row.addWidget(self.add_to_curated_btn)
        curated_btn_row.addWidget(self.remove_from_curated_btn)
        curated_layout.addLayout(curated_btn_row)
        self.curated_table = CardTableView(self, self.columns)
        self.curated_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.curated_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        curated_layout.addWidget(self.curated_table)
        layout.insertWidget(2, curated_group)

        # --- Break List Controls/Preview Section ---
        break_group = QGroupBox("3. Break List Controls & Preview")
        break_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bbb; margin-top: 8px; padding: 8px; } ")
        break_layout = QVBoxLayout(break_group)
        # Add Rule button
        self.add_rule_btn = QPushButton("Add Rule")
        self.add_rule_btn.clicked.connect(self.add_rule)
        break_layout.addWidget(self.add_rule_btn)
        # Rule widgets area
        self.rules_area = QVBoxLayout()
        break_layout.addLayout(self.rules_area)
        # Generate button and preview
        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("Generate Break List")
        self.generate_btn.clicked.connect(self.generate_break_list)
        self.break_preview_label = QLabel("Break List Preview:")
        self.break_preview_box = QLineEdit()
        self.break_preview_box.setReadOnly(True)
        self.filter_hint_label = QLabel("Rules will only select from cards currently visible in the inventory table.")
        self.filter_hint_label.setStyleSheet("color: #888; font-style: italic;")
        btn_row.addWidget(self.generate_btn)
        btn_row.addWidget(self.break_preview_label)
        btn_row.addWidget(self.break_preview_box)
        btn_row.addWidget(self.filter_hint_label)
        break_layout.addLayout(btn_row)
        layout.insertWidget(3, break_group)
        # Add initial rule widget if none exist
        if not self.rule_widgets:
            self.add_rule()
    def _get_all_inventory_fields(self):
        # Get all unique fields from inventory
        fields = set()
        for card in self.inventory.get_all_cards():
            fields.update(card.keys())
        return sorted(fields)
    def add_selected_to_curated(self):
        """
        Add selected cards from the inventory table to the curated list, avoiding duplicates, and update the curated table and break preview.
        """
        selected_rows = self.card_table.selectionModel().selectedRows()
        for idx in selected_rows:
            card = self.card_table.cards[idx.row() - 1]
            if card not in self.curated_cards:
                self.curated_cards.append(card)
        self.update_curated_table()
        self.generate_break_list()  # Always update preview
    def remove_selected_from_curated(self):
        """
        Remove selected cards from the curated list and update the curated table and break preview.
        """
        selected_rows = self.curated_table.selectionModel().selectedRows()
        for idx in sorted(selected_rows, reverse=True):
            if 0 <= idx.row() - 1 < len(self.curated_cards):
                self.curated_cards.pop(idx.row() - 1)
        self.update_curated_table()
        self.generate_break_list()  # Always update preview
    def update_curated_table(self):
        """
        Update the curated table to reflect the current curated_cards list.
        """
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
        # Use self.filter_inputs (sidebar QLineEdits) for filtering
        filters = {col: self.filter_inputs[col].text() for col in self.filter_inputs}
        filtered = self.inventory.filter_cards(filters)
        self.filtered_inventory = filtered  # Store the filtered pool
        self.card_table.update_cards(filtered)
        self.card_table.repaint()
        # --- Active filter chips logic ---
        # Clear old chips
        while self.active_filter_chips_layout.count():
            chip = self.active_filter_chips_layout.takeAt(0)
            if chip.widget():
                chip.widget().deleteLater()
        # Add a chip for each active filter
        for col, val in filters.items():
            if val:
                chip = QPushButton(f"{col}: {val}")
                chip.setStyleSheet("background: #e0e0e0; border-radius: 10px; padding: 2px 8px; margin: 2px; font-size: 11px;")
                chip.setCursor(Qt.PointingHandCursor)
                chip.clicked.connect(lambda _, c=col: self._clear_filter_chip(c))
                self.active_filter_chips_layout.addWidget(chip)
        self.active_filter_chips_layout.addStretch(1)
    def _clear_filter_chip(self, col):
        self.filter_inputs[col].clear()
        self.update_table_filter()
    def export_break_list(self):
        """
        Export the generated break list (from preview) to clipboard and/or CSV.
        """
        import pyperclip
        text = self.break_preview_box.text()
        pyperclip.copy(text)
        fname, _ = QFileDialog.getSaveFileName(self, "Export Break List", "break_list.csv", "CSV Files (*.csv)")
        if fname:
            with open(fname, 'w', encoding='utf-8', newline='') as f:
                for line in text.splitlines():
                    f.write(line + '\n')
        QMessageBox.information(self, "Exported", "Break list exported and copied to clipboard.")
    def clear_all_filters(self):
        for le in self.filter_inputs.values():
            le.clear()
        self.update_table_filter()
    def add_rule(self):
        """
        Add a new rule widget to the break builder, connect its signals to regenerate the break list preview, and update the UI.
        """
        rule_widget = BreakRuleWidget(self)
        self.rule_widgets.append(rule_widget)
        self.rules_area.addWidget(rule_widget)
        # Connect all child widgets to regenerate break list preview
        for child in rule_widget.findChildren(QLineEdit):
            child.textChanged.connect(self.generate_break_list)
        for child in rule_widget.findChildren(QComboBox):
            child.currentIndexChanged.connect(self.generate_break_list)
        for child in rule_widget.findChildren(QSpinBox):
            child.valueChanged.connect(self.generate_break_list)
        for child in rule_widget.findChildren(QDoubleSpinBox):
            child.valueChanged.connect(self.generate_break_list)
        rule_widget.remove_btn.clicked.connect(lambda: self.remove_rule(rule_widget))
        self.generate_break_list() 