from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QListWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox, QCheckBox, QFileDialog, QInputDialog, QWidget, QFormLayout, QScrollArea, QSizePolicy, QFrame, QSpinBox, QDoubleSpinBox, QGroupBox, QAbstractItemView, QSplitter, QTextEdit, QStyle)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from models.scryfall_api import fetch_scryfall_data
import random
import json
from ui.card_table import CardTableView
from ui.filter_overlay import FilterOverlay
from ui.image_preview import ImagePreview
from ui.card_details import CardDetails
from ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
import csv
import os
from ui.columns_config import DEFAULT_COLUMNS

# Centralized config/constants for break builder
BREAK_BUILDER_CONFIG = {
    'rule_fields': [
        {'name': 'Price', 'type': 'float', 'label': 'Price ($)', 'min': 0, 'max': 10000, 'step': 0.01},
        {'name': 'Whatnot price', 'type': 'float', 'label': 'Whatnot Price', 'min': 0, 'max': 10000, 'step': 0.01},
        {'name': 'Purchase price', 'type': 'float', 'label': 'Purchase Price', 'min': 0, 'max': 10000, 'step': 0.01},
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
    Supports AND logic: user can add multiple field criteria per rule.
    """
    def __init__(self, parent=None, inventory_fields=None, inventory=None):
        super().__init__(parent)
        self.inventory = inventory
        self.inventory_fields = inventory_fields or []
        layout = QVBoxLayout(self)
        # Top row: count/percent
        count_row = QHBoxLayout()
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
        count_row.addWidget(QLabel("Select:"))
        count_row.addWidget(self.count_type)
        count_row.addWidget(self.count_value)
        count_row.addWidget(self.percent_value)
        count_row.addStretch(1)
        layout.addLayout(count_row)
        # Criteria area
        self.criteria_area = QVBoxLayout()
        self.criteria_widgets = []  # List of (field_dropdown, input_widget, remove_btn)
        layout.addLayout(self.criteria_area)
        # Add Field button
        add_field_btn = QPushButton("+ Add Field")
        add_field_btn.setStyleSheet("background: #e3eaf7; color: #1976d2; font-weight: bold; border-radius: 6px; padding: 4px 12px;")
        add_field_btn.clicked.connect(self.add_criterion_row)
        layout.addWidget(add_field_btn)
        # Remove rule button
        self.remove_btn = QPushButton("Remove Rule")
        self.remove_btn.setStyleSheet("color: red;")
        layout.addWidget(self.remove_btn)
        layout.addStretch(1)
        # Add initial criterion row
        self.add_criterion_row()
    def add_criterion_row(self, field=None):
        row = QHBoxLayout()
        field_dropdown = QComboBox()
        field_dropdown.addItems([f for f in self.inventory_fields])
        if field:
            idx = field_dropdown.findText(field)
            if idx >= 0:
                field_dropdown.setCurrentIndex(idx)
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        # Build input for selected field
        self._build_field_input(field_dropdown.currentText(), input_layout, input_widget)
        field_dropdown.currentTextChanged.connect(lambda f, l=input_layout, w=input_widget: self._on_field_changed(f, l, w))
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setStyleSheet("color: #e53935; font-weight: bold; border: none; background: transparent;")
        remove_btn.clicked.connect(lambda: self._remove_criterion_row(row, (field_dropdown, input_widget, remove_btn)))
        row.addWidget(field_dropdown)
        row.addWidget(input_widget)
        row.addWidget(remove_btn)
        self.criteria_area.addLayout(row)
        self.criteria_widgets.append((field_dropdown, input_widget, remove_btn))
    def _remove_criterion_row(self, row_layout, widget_tuple):
        for i in reversed(range(row_layout.count())):
            item = row_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.criteria_area.removeItem(row_layout)
        if widget_tuple in self.criteria_widgets:
            self.criteria_widgets.remove(widget_tuple)
    def _on_field_changed(self, field, input_layout, input_widget):
        # Clear old input
        for i in reversed(range(input_layout.count())):
            item = input_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        self._build_field_input(field, input_layout, input_widget)
    def _build_field_input(self, field, input_layout, input_widget):
        values = [c.get(field, "") for c in self.inventory.get_all_cards()] if self.inventory else []
        try:
            nums = [float(str(v).replace("$", "").strip()) for v in values if str(v).replace("$", "").strip() != ""]
        except Exception:
            nums = []
        if len(nums) >= len(values) * 0.8 and len(nums) > 0:
            min_box = QDoubleSpinBox()
            min_box.setMinimum(-100000)
            min_box.setMaximum(100000)
            min_box.setSingleStep(0.01)
            min_box.setPrefix(">= ")
            max_box = QDoubleSpinBox()
            max_box.setMinimum(-100000)
            max_box.setMaximum(100000)
            max_box.setSingleStep(0.01)
            max_box.setPrefix("<= ")
            input_layout.addWidget(min_box)
            input_layout.addWidget(max_box)
            input_widget._field_input = (min_box, max_box)
        elif 1 < len(set(values)) <= 12:
            combo = QComboBox()
            combo.addItem("")
            combo.addItems(sorted(set(str(v) for v in values if v != "")))
            input_layout.addWidget(combo)
            input_widget._field_input = combo
        else:
            edit = QLineEdit()
            edit.setPlaceholderText(f"Filter {field}")
            input_layout.addWidget(edit)
            input_widget._field_input = edit
    def get_rule(self):
        rule = {}
        rule['count_type'] = self.count_type.currentText()
        rule['count'] = self.count_value.value() if self.count_type.currentIndex() == 0 else self.percent_value.value()
        rule['criteria'] = []
        for field_dropdown, input_widget, _ in self.criteria_widgets:
            field = field_dropdown.currentText()
            inp = getattr(input_widget, '_field_input', None)
            if isinstance(inp, tuple):
                min_val = inp[0].value()
                max_val = inp[1].value()
                rule['criteria'].append((field, (min_val, max_val)))
            elif isinstance(inp, QComboBox):
                rule['criteria'].append((field, inp.currentText()))
            elif isinstance(inp, QLineEdit):
                rule['criteria'].append((field, inp.text().strip()))
        return rule
    def set_rule(self, rule):
        self.count_type.setCurrentIndex(0 if rule.get('count_type') == 'Count' else 1)
        if rule.get('count_type') == 'Count':
            self.count_value.setValue(int(rule.get('count', 1)))
        else:
            self.percent_value.setValue(float(rule.get('count', 1)))
        # Remove all but one criterion row
        while len(self.criteria_widgets) > 1:
            self._remove_criterion_row(self.criteria_area.itemAt(0), self.criteria_widgets[0])
        # Set criteria
        for i, (field, val) in enumerate(rule.get('criteria', [])):
            if i >= len(self.criteria_widgets):
                self.add_criterion_row(field)
            field_dropdown, input_widget, _ = self.criteria_widgets[i]
            idx = field_dropdown.findText(field)
            if idx >= 0:
                field_dropdown.setCurrentIndex(idx)
            inp = getattr(input_widget, '_field_input', None)
            if isinstance(inp, tuple):
                inp[0].setValue(val[0])
                inp[1].setValue(val[1])
            elif isinstance(inp, QComboBox):
                idx2 = inp.findText(val)
                if idx2 >= 0:
                    inp.setCurrentIndex(idx2)
            elif isinstance(inp, QLineEdit):
                inp.setText(val)
    def _toggle_count_type(self, idx):
        if idx == 0:
            self.count_value.setVisible(True)
            self.percent_value.setVisible(False)
        else:
            self.count_value.setVisible(False)
            self.percent_value.setVisible(True)

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
        # --- Total cards input (must be initialized before any method uses it) ---
        self.total_cards_input = QSpinBox()
        self.total_cards_input.setMinimum(1)
        self.total_cards_input.setMaximum(10000)
        self.total_cards_input.setValue(30)
        self.total_cards_input.setToolTip("Specify the total number of cards needed for the break.")
        self.total_cards_input.valueChanged.connect(self.generate_break_list)  # Always trigger full break list regeneration
        # All required attributes must be initialized before any method that uses them (regression rule)
        self.filtered_inventory = self.inventory.get_all_cards()
        self.break_items = []  # List of dicts (cards/items)
        self.curated_cards = []  # List of curated card dicts
        self.rules = []  # List of rule dicts
        self.rule_widgets = []  # List of BreakRuleWidget
        self.current_break_list = []  # Flat list of cards in break (for export)
        self.current_break_list_details = []  # [(section_type, section_info, [cards])]
        # --- Tabbed workflow ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        self.tabs.setStyleSheet("QTabBar::tab { min-width: 180px; font-size: 15px; font-weight: bold; padding: 8px 18px; } QTabBar::tab:selected { background: #1976d2; color: white; border-radius: 8px; }")
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tabs)
        # --- Step 1: Filter Inventory Tab ---
        filter_tab = QWidget()
        filter_layout = QVBoxLayout(filter_tab)
        # --- Inventory Section ---
        inventory_group = QGroupBox("1. Inventory (Filter & Select)")
        inventory_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bbb; margin-top: 8px; padding: 12px 8px 18px 8px; background: #f7f7fa; } ")
        inv_group_layout = QVBoxLayout(inventory_group)
        inv_group_layout.setSpacing(10)
        # Inventory area: table (left) + preview (right)
        inv_hbox = QHBoxLayout()
        # --- Dynamically get all fields from inventory for filtering ---
        self.filter_fields = self._get_all_inventory_fields()
        self.columns = DEFAULT_COLUMNS + [f for f in self.filter_fields if f not in DEFAULT_COLUMNS]
        self.card_table = CardTableView(self.inventory, self.columns)
        self.card_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.card_table.setMinimumHeight(220)
        self.card_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Add FilterOverlay above the table
        self.filter_overlay = FilterOverlay(self.card_table, self.columns)
        self.filter_overlay.show()
        for col, filt in self.filter_overlay.filters.items():
            filt.textChanged.connect(self.update_table_filter)
        # --- Add Clear All Filters button above overlay ---
        clear_filters_btn = QPushButton("Clear All Filters")
        clear_filters_btn.setStyleSheet("padding: 4px 16px; border-radius: 8px; background: #e0e0e0; font-weight: bold;")
        clear_filters_btn.clicked.connect(lambda: [f.clear() for f in self.filter_overlay.filters.values()])
        clear_filters_btn.clicked.connect(self.update_table_filter)
        self.clear_filters_btn = clear_filters_btn
        # --- Group filter controls in a styled QFrame above the table ---
        filter_controls_frame = QFrame()
        filter_controls_frame.setFrameShape(QFrame.StyledPanel)
        filter_controls_frame.setStyleSheet("background: #f5f7fa; border: 1.5px solid #b3c6e0; border-radius: 10px; padding: 2px 18px 2px 18px; margin-bottom: 2px;")
        filter_controls_hbox = QHBoxLayout(filter_controls_frame)
        filter_controls_hbox.setContentsMargins(0, 0, 0, 0)
        filter_controls_hbox.setSpacing(10)
        filter_controls_hbox.addWidget(self.filter_overlay, 1)
        filter_controls_hbox.addWidget(clear_filters_btn, 0, Qt.AlignRight)
        # --- Style the filter overlay for clarity ---
        self.filter_overlay.setStyleSheet("background: #eaf1fb; border: 1px solid #b3c6e0; border-radius: 6px; padding: 2px 0 2px 0;")
        # --- Table and preview layout ---
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setStyleSheet("background: #f8fafd; border: 1.5px solid #b3c6e0; border-radius: 10px; padding: 10px 10px 10px 10px;")
        preview_vbox = QVBoxLayout(preview_frame)
        preview_vbox.setContentsMargins(0, 0, 0, 0)
        preview_vbox.setSpacing(8)
        self.image_preview = ImagePreview()
        self.image_preview.setMinimumHeight(100)
        self.image_preview.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.card_details = CardDetails()
        self.card_details.setMinimumHeight(100)
        self.card_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        preview_vbox.addWidget(self.image_preview)
        preview_vbox.addWidget(self.card_details)
        # --- Use QSplitter for table/preview, but add spacing and frame ---
        table_preview_splitter = QSplitter()
        table_preview_splitter.setOrientation(Qt.Horizontal)
        table_preview_splitter.addWidget(self.card_table)
        table_preview_splitter.addWidget(preview_frame)
        table_preview_splitter.setSizes([700, 300])
        table_preview_splitter.setChildrenCollapsible(False)
        table_preview_splitter.setHandleWidth(8)
        table_preview_splitter.setMinimumWidth(200)
        table_preview_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # --- Main inventory area layout ---
        table_vbox = QVBoxLayout()
        table_vbox.setContentsMargins(12, 12, 12, 12)
        table_vbox.setSpacing(10)
        table_vbox.addWidget(filter_controls_frame)
        table_vbox.addWidget(table_preview_splitter)
        table_vbox.addWidget(self.card_table.pagination_widget)
        self.inventory_placeholder = QLabel("No cards in inventory.")
        self.inventory_placeholder.setStyleSheet("color: #888; font-style: italic; padding: 6px;")
        if not self.inventory.get_all_cards():
            table_vbox.addWidget(self.inventory_placeholder)
        inv_hbox.addLayout(table_vbox, 1)
        inv_group_layout.addLayout(inv_hbox)
        filter_layout.insertWidget(0, inventory_group)
        # --- Ensure inventory table is populated on launch ---
        self.card_table.update_cards(self.inventory.get_all_cards())
        # --- Connect card_selected signal to preview widgets ---
        def _debug_card_selected(card):
            print(f"DEBUG: BreakBuilderDialog received card_selected: {card}")
            self.image_preview.show_card_image(card)
            self.card_details.show_card_details(card)
        self.card_table.card_selected.connect(_debug_card_selected)
        # --- Step 2: Curate Must-Haves Tab ---
        curate_tab = QWidget()
        curate_layout = QVBoxLayout(curate_tab)
        curated_group = QGroupBox("2. Curated Cards (Guaranteed in Break)")
        curated_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bbb; margin-top: 8px; padding: 12px 8px 18px 8px; background: #f7f7fa; } ")
        curated_layout = QVBoxLayout(curated_group)
        curated_layout.setSpacing(10)
        curated_layout.addWidget(QLabel("Drag to reorder. Remove to exclude from break."))
        # Add/Remove buttons for curated list (modern, with icons)
        curated_btn_row = QHBoxLayout()
        self.add_to_curated_btn = QPushButton(" Add Selected to Curated")
        self.add_to_curated_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton))
        self.add_to_curated_btn.setStyleSheet("padding: 6px 18px; border-radius: 8px; background: #1976d2; color: white; font-weight: bold; font-size: 13px;")
        self.add_to_curated_btn.setToolTip("Add selected cards from inventory to curated list.")
        self.add_to_curated_btn.clicked.connect(self.add_selected_to_curated)
        self.remove_from_curated_btn = QPushButton(" Remove Selected from Curated")
        self.remove_from_curated_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogNoButton))
        self.remove_from_curated_btn.setStyleSheet("padding: 6px 18px; border-radius: 8px; background: #e53935; color: white; font-weight: bold; font-size: 13px;")
        self.remove_from_curated_btn.setToolTip("Remove selected cards from curated list.")
        self.remove_from_curated_btn.clicked.connect(self.remove_selected_from_curated)
        curated_btn_row.addWidget(self.add_to_curated_btn)
        curated_btn_row.addWidget(self.remove_from_curated_btn)
        curated_btn_row.addStretch(1)
        curated_layout.addLayout(curated_btn_row)
        self.curated_table = CardTableView(self, self.columns)
        self.curated_table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.curated_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.curated_table.setMinimumHeight(140)
        curated_layout.addWidget(self.curated_table)
        # Placeholder for empty curated table
        self.curated_placeholder = QLabel("No curated cards yet.")
        self.curated_placeholder.setStyleSheet("color: #888; font-style: italic; padding: 6px;")
        if not self.curated_cards:
            curated_layout.addWidget(self.curated_placeholder)
        self._curated_layout = curated_layout  # Save for dynamic placeholder
        curate_layout.insertWidget(0, curated_group)
        # --- Step 3: Set Rules Tab ---
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)
        # --- Save/Load Rule Set buttons (move to top of rules tab) ---
        self._add_rule_set_buttons(rules_layout)
        # --- Break List Controls/Preview Section ---
        break_group = QGroupBox("3. Break List Controls  Preview")
        break_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #bbb; margin-top: 8px; padding: 12px 8px 18px 8px; background: #f7f7fa; } ")
        break_layout = QVBoxLayout(break_group)
        break_layout.setSpacing(10)
        # Collapsible rule builder area (expanded by default)
        self.rules_collapsed = False
        self.toggle_rules_btn = QPushButton("▼ Rules")
        self.toggle_rules_btn.setCheckable(True)
        self.toggle_rules_btn.setChecked(True)
        self.toggle_rules_btn.setStyleSheet("font-weight: bold; font-size: 14px; background: #f5f5f5; border: none; text-align: left; padding: 4px 8px;")
        self.toggle_rules_btn.setToolTip("Show/hide the rule builder area.")
        self.toggle_rules_btn.toggled.connect(self._toggle_rules_area)
        break_layout.addWidget(self.toggle_rules_btn)
        # Rule widgets area (as a QWidget for animation)
        self.rules_area_scroll = QScrollArea()
        self.rules_area_scroll.setWidgetResizable(True)
        self.rules_area_widget = QWidget()
        self.rules_area_layout = QVBoxLayout(self.rules_area_widget)
        self.rules_area_layout.setContentsMargins(0, 0, 0, 0)
        self.rules_area_layout.setSpacing(8)
        self.rules_area_scroll.setWidget(self.rules_area_widget)
        self.rules_area_scroll.setMinimumHeight(120)
        self.rules_area_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        break_layout.addWidget(self.rules_area_scroll)
        # Add Rule button (modern, with icon)
        self.add_rule_btn = QPushButton(" Add Rule")
        self.add_rule_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.add_rule_btn.setStyleSheet("padding: 6px 18px; border-radius: 8px; background: #43a047; color: white; font-weight: bold; font-size: 13px;")
        self.add_rule_btn.setToolTip("Add a new rule for break composition.")
        self.add_rule_btn.clicked.connect(self.add_rule)
        break_layout.addWidget(self.add_rule_btn)
        rules_layout.insertWidget(1, break_group)
        # --- Step 4: Generate Break Tab ---
        generate_tab = QWidget()
        generate_layout = QVBoxLayout(generate_tab)
        generate_layout.setContentsMargins(18, 18, 18, 18)
        generate_layout.setSpacing(16)
        # Add total cards input at the top of the Generate tab
        total_row = QHBoxLayout()
        total_label = QLabel("Total cards needed for break:")
        total_label.setStyleSheet("font-weight: bold; font-size: 15px; margin-right: 12px;")
        total_row.addWidget(total_label)
        total_row.addWidget(self.total_cards_input)
        generate_layout.addLayout(total_row)
        # --- Modern, clean button row ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(18)
        self.generate_btn = QPushButton(" Generate Break List")
        self.generate_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.generate_btn.setStyleSheet("padding: 8px 24px; border-radius: 10px; background: #1976d2; color: white; font-weight: bold; font-size: 15px;")
        self.generate_btn.setToolTip("Generate the break list using curated cards and rules, from the currently filtered inventory.")
        self.generate_btn.clicked.connect(self.generate_break_list)
        self.export_btn = QPushButton(" Export Break List")
        self.export_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.export_btn.setStyleSheet("padding: 8px 24px; border-radius: 10px; background: #388e3c; color: white; font-weight: bold; font-size: 15px;")
        self.export_btn.setToolTip("Export the break list in Title/Description format (CSV)")
        self.export_btn.clicked.connect(self.export_break_list_item_listing)
        self.remove_from_inventory_btn = QPushButton(" Remove from Inventory")
        self.remove_from_inventory_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.remove_from_inventory_btn.setStyleSheet("padding: 8px 24px; border-radius: 10px; background: #e53935; color: white; font-weight: bold; font-size: 15px;")
        self.remove_from_inventory_btn.setToolTip("Remove all cards in the current break list from inventory (with confirmation)")
        self.remove_from_inventory_btn.clicked.connect(self.remove_break_cards_from_inventory)
        self.undo_remove_btn = QPushButton(" Undo Remove")
        self.undo_remove_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.undo_remove_btn.setStyleSheet("padding: 8px 24px; border-radius: 10px; background: #1976d2; color: white; font-weight: bold; font-size: 15px;")
        self.undo_remove_btn.setToolTip("Undo the last removal of break cards from inventory")
        self.undo_remove_btn.clicked.connect(self.undo_remove_from_inventory)
        self.undo_remove_btn.setEnabled(False)
        self.last_removed_cards = []
        btn_row.addWidget(self.generate_btn)
        btn_row.addWidget(self.export_btn)
        btn_row.addWidget(self.remove_from_inventory_btn)
        btn_row.addWidget(self.undo_remove_btn)
        generate_layout.addLayout(btn_row)
        # --- Total and average cost labels ---
        self.total_cost_label = QLabel()
        self.avg_cost_label = QLabel()
        cost_row = QHBoxLayout()
        cost_row.setSpacing(24)
        cost_row.addWidget(self.total_cost_label)
        cost_row.addWidget(self.avg_cost_label)
        cost_row.addStretch(1)
        generate_layout.addLayout(cost_row)
        # --- Modern, scrollable break preview box ---
        preview_group = QFrame()
        preview_group.setFrameShape(QFrame.StyledPanel)
        preview_group.setStyleSheet("background: #f8fafd; border: 1.5px solid #b3c6e0; border-radius: 10px; padding: 10px 10px 10px 10px;")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)
        self.break_preview_label = QLabel("Break List Preview:")
        self.break_preview_box = QTextEdit()
        self.break_preview_box.setReadOnly(True)
        self.break_preview_box.setStyleSheet("background: #fafafa; border: 1px solid #bbb; border-radius: 6px; font-family: monospace; font-size: 13px; padding: 6px;")
        self.break_preview_box.setMinimumHeight(180)
        preview_layout.addWidget(self.break_preview_label)
        preview_layout.addWidget(self.break_preview_box)
        generate_layout.addWidget(preview_group)
        self.filter_hint_label = QLabel("Rules will only select from cards currently visible in the inventory table.")
        self.filter_hint_label.setStyleSheet("color: #888; font-style: italic; margin-top: 8px;")
        generate_layout.addWidget(self.filter_hint_label)
        # --- Add tabs ---
        self.tabs.addTab(filter_tab, "1. Filter Inventory")
        self.tabs.addTab(curate_tab, "2. Curate Must-Haves")
        self.tabs.addTab(rules_tab, "3. Set Rules")
        self.tabs.addTab(generate_tab, "4. Generate Break")
        # --- Floating help button (add to main_layout) ---
        self.help_btn = QPushButton()
        self.help_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))
        self.help_btn.setToolTip("Show quick tips and workflow guidance.")
        self.help_btn.setFixedSize(44, 44)
        self.help_btn.setStyleSheet("border-radius: 22px; background: #1976d2; color: white; position: absolute; bottom: 24px; right: 24px; font-size: 22px; box-shadow: 0 2px 8px rgba(0,0,0,0.18);")
        self.help_btn.clicked.connect(self.show_help_dialog)
        self.help_btn.setAccessibleName("Help")
        main_layout.addWidget(self.help_btn, 0, Qt.AlignBottom | Qt.AlignRight)
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
        Animate added/removed rows for visual feedback.
        Show/hide the empty placeholder dynamically.
        """
        # Store previous set for animation
        prev_set = set(id(card) for card in getattr(self, '_last_curated_cards', []))
        new_set = set(id(card) for card in self.curated_cards)
        self.curated_table.update_cards(self.curated_cards)
        self.curated_table.repaint()
        # Animate added rows
        for row, card in enumerate(self.curated_cards):
            if id(card) not in prev_set:
                self._animate_table_row(self.curated_table, row, added=True)
        # Animate removed rows (optional, not shown since row is gone)
        self._last_curated_cards = list(self.curated_cards)
        # --- Dynamic placeholder logic ---
        if hasattr(self, 'curated_placeholder') and hasattr(self, '_curated_layout'):
            if not self.curated_cards:
                if self._curated_layout.indexOf(self.curated_placeholder) == -1:
                    self._curated_layout.addWidget(self.curated_placeholder)
            else:
                self.curated_placeholder.setParent(None)
    def _animate_table_row(self, table, row, added=True, test_mode=False):
        """
        Animate a table row background color for add/remove feedback.
        If test_mode is True, always create the overlay for test detection.
        """
        # Get the rect for the row (fix: do not offset by +1)
        rect = table.visualRect(table.model.index(row, 0))
        if (not rect.isValid() or rect.height() == 0) and not test_mode:
            return
        # If in test mode and rect is invalid, create a default rect
        if test_mode and (not rect.isValid() or rect.height() == 0):
            rect = QRect(0, 0, 120, 32)
        # Create a QWidget overlay for animation
        overlay = QWidget(table.viewport())
        overlay.setGeometry(rect)
        color_start = "#c8e6c9" if added else "#ffcdd2"
        color_end = "#ffffff"
        overlay.setStyleSheet(f"background: {color_start}; border-radius: 4px;")
        overlay.show()
        anim = QPropertyAnimation(overlay, b"windowOpacity")
        anim.setDuration(600)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.finished.connect(overlay.deleteLater)
        overlay._row_anim = anim  # Prevent GC until finished
        anim.start()
    def _rule_to_str(self, rule):
        """Return a human-readable string for a rule's criteria."""
        parts = []
        for field, val in rule.get('criteria', []):
            if isinstance(val, tuple):
                min_val, max_val = val
                parts.append(f"{field} >= {min_val}, <= {max_val}")
            elif isinstance(val, str) and val:
                parts.append(f"{field}: {val}")
        count_type = rule.get('count_type', '')
        count = rule.get('count', '')
        if count_type == '% of available':
            return f"{count}% of filtered ({', '.join(parts)})"
        else:
            return f"{count} cards ({', '.join(parts)})"
    def generate_break_list(self):
        """
        Combine curated and rule-based selections, deduplicate, and match total.
        Store both a flat list and a detailed breakdown for preview/export sync.
        Show preview with sections for curated, each rule-based group (with rule info), and filler.
        """
        total_needed = self.total_cards_input.value()
        curated = list(self.curated_cards)
        all_cards = self.filtered_inventory
        used_ids = set(id(c) for c in curated)
        rule_cards_by_rule = []
        allocations = []  # (rule, filtered, n)
        enabled_rules = []
        for i in range(self.rules_area_layout.count()):
            item = self.rules_area_layout.itemAt(i)
            if not item or not item.widget():
                continue
            group = item.widget()
            rule_widget = getattr(group, '_rule_widget', None)
            enable_checkbox = getattr(group, '_enable_checkbox', None)
            if not rule_widget or not enable_checkbox or not enable_checkbox.isChecked():
                continue
            rule = rule_widget.get_rule()
            filtered = []
            for card in all_cards:
                if id(card) in used_ids:
                    continue
                match = True
                for field, val in rule.get('criteria', []):
                    if isinstance(val, tuple):
                        min_val, max_val = val
                        try:
                            card_val = card.get(field, 0)
                            if isinstance(card_val, str):
                                card_val = card_val.replace("$", "").strip()
                            card_val = float(card_val)
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
            n = 0
            if rule.get("count_type") == "Count":
                n = int(rule.get("count", 1))
            else:
                percent = float(rule.get("count", 1))
                n = int(total_needed * percent / 100)
            n = min(n, len(filtered))
            allocations.append((rule, filtered, n))
            enabled_rules.append((rule, filtered))
        # Adjust allocations if sum exceeds total_needed
        total_alloc = sum(n for _, _, n in allocations)
        if total_alloc > total_needed:
            over = total_alloc - total_needed
            for i in reversed(range(len(allocations))):
                rule, filtered, n = allocations[i]
                reduce_by = min(over, n-1 if n>1 else over)
                allocations[i] = (rule, filtered, n - reduce_by)
                over -= reduce_by
                if over <= 0:
                    break
        # Second pass: select cards for each rule
        rule_cards_by_rule = []
        for rule, filtered, n in allocations:
            selected = random.sample(filtered, n) if n > 0 else []
            for card in selected:
                used_ids.add(id(card))
            rule_cards_by_rule.append((rule, selected))
        final_list = list(curated)
        break_details = []
        if curated:
            break_details.append(("Curated", None, curated))
        for i, (rule, cards) in enumerate(rule_cards_by_rule):
            break_details.append(("Rule", rule, cards))
            final_list.extend(cards)
        filler = []
        if len(final_list) < total_needed:
            for card in all_cards:
                if id(card) not in used_ids:
                    filler.append(card)
                    final_list.append(card)
                    used_ids.add(id(card))
                    if len(final_list) >= total_needed:
                        break
        if filler:
            break_details.append(("Filler", None, filler))
        # Store for export
        self.current_break_list = final_list[:total_needed]
        self.current_break_list_details = break_details
        # Show preview with sections and rule info
        lines = []
        for section in break_details:
            section_type, rule, cards = section
            if not cards:
                continue
            if section_type == "Curated":
                lines.append("Curated Cards:")
            elif section_type == "Rule":
                lines.append(f"Rule ({self._rule_to_str(rule)}):")
            elif section_type == "Filler":
                lines.append("Filler Cards:")
            for c in cards:
                # For rules, show relevant fields next to the card name
                if section_type == "Rule" and rule:
                    crit_fields = [field for field, _ in rule.get('criteria', [])]
                    crit_values = []
                    for field in crit_fields:
                        val = c.get(field, None)
                        if val is not None and val != '':
                            crit_values.append(f"{field}: {val}")
                    crit_str = f" ({', '.join(crit_values)})" if crit_values else ""
                else:
                    crit_str = ""
                lines.append(f"  {c.get('Name', '')} [{c.get('Set name', '')}]{crit_str}")
        self.break_preview_box.setText("\n".join(lines[:total_needed + 10]))
        # --- Compute and display total and average cost ---
        prices = []
        for card in self.current_break_list:
            price = card.get('Purchase price') or card.get('Whatnot price')
            if price is not None:
                try:
                    if isinstance(price, str):
                        price = price.replace("$", "").strip()
                    price = float(price)
                    prices.append(price)
                except Exception:
                    continue
        total_cost = sum(prices)
        avg_cost = (total_cost / len(prices)) if prices else 0.0
        self.total_cost_label.setText(f"<b>Total Card Cost:</b> ${total_cost:,.2f}")
        self.avg_cost_label.setText(f"<b>Average Card Cost:</b> ${avg_cost:,.2f}")
    def update_table_filter(self):
        """
        Update the inventory table based on the FilterOverlay fields.
        This method is now unified with the main GUI's filtering logic for modularity.
        """
        filters = {col: self.filter_overlay.filters[col].text() for col in self.columns}
        filtered = self.inventory.filter_cards(filters)
        self.filtered_inventory = filtered  # Store the filtered pool
        self.card_table.update_cards(filtered)
        self.card_table.repaint()
        # Inventory placeholder logic
        if hasattr(self, 'inventory_placeholder'):
            if not filtered:
                parent = self.card_table.parentWidget()
                if parent and parent.layout() and self.inventory_placeholder.parent() != parent:
                    parent.layout().addWidget(self.inventory_placeholder)
                self.inventory_placeholder.show()
            else:
                self.inventory_placeholder.hide()
    def export_break_list_item_listing(self):
        """
        Export the generated break list (from preview) in Title/Description format (CSV), using the same logic and templates as the main export_item_listings.
        Only export the cards in self.current_break_list, in order.
        """
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        final_list = self.current_break_list
        if not final_list:
            QMessageBox.warning(self, "Export Error", "No break list generated. Please generate the break list first.")
            return
        all_fields = set()
        for card in final_list:
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
        listings = []
        for card in final_list:
            title = " ".join(str(card.get(f, "")) for f in title_fields if f in card)
            desc_lines = [f"{f}: {card.get(f, '')}" for f in desc_fields if f in card]
            desc = "\n".join(desc_lines)
            listings.append((title.strip(), desc))
        fname, _ = QFileDialog.getSaveFileName(self, "Export Break List (Item Listing)", "break_list.csv", "CSV Files (*.csv)")
        if not fname:
            return
        with open(fname, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Description"])
            for title, desc in listings:
                writer.writerow([title, desc])
        QMessageBox.information(self, "Exported", f"Break list exported as item listing CSV with {len(listings)} cards.")
    def clear_all_filters(self):
        for le in self.filter_overlay.filters.values():
            le.clear()
        self.update_table_filter()
    def _toggle_rules_area(self, checked):
        self.rules_area_widget.setVisible(checked)
        self.toggle_rules_btn.setText("▼ Rules" if checked else "► Rules")
    def _enforce_percent_rule_limits(self):
        """Ensure the sum of all enabled percent-based rules does not exceed 100%. If exceeded, adjust the last changed rule."""
        percent_rules = []
        for i in range(self.rules_area_layout.count()):
            item = self.rules_area_layout.itemAt(i)
            if not item or not item.widget():
                continue
            group = item.widget()
            rule_widget = getattr(group, '_rule_widget', None)
            enable_checkbox = getattr(group, '_enable_checkbox', None)
            if not rule_widget or not enable_checkbox or not enable_checkbox.isChecked():
                continue
            rule = rule_widget.get_rule()
            if rule.get('count_type') == '% of available':
                percent_rules.append((rule_widget, rule))
        total_percent = sum(float(r['count']) for _, r in percent_rules)
        if total_percent > 100 and percent_rules:
            # Reduce the last changed rule to fit
            excess = total_percent - 100
            last_widget, last_rule = percent_rules[-1]
            new_val = float(last_rule['count']) - excess
            if new_val < 0:
                new_val = 0
            last_widget.percent_value.blockSignals(True)
            last_widget.percent_value.setValue(new_val)
            last_widget.percent_value.blockSignals(False)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Percent Rule Limit", "Total percent for all enabled percent-based rules cannot exceed 100%. The last rule was adjusted to fit.")
    def add_rule(self, rule_data=None):
        rule_widget = BreakRuleWidget(self, inventory_fields=self.filter_fields, inventory=self.inventory)
        if rule_data:
            rule_widget.set_rule(rule_data)
        group = QGroupBox(f"Rule {len(self.rule_widgets)+1}")
        group.setCheckable(True)
        group.setChecked(True)
        group.setStyleSheet("QGroupBox { background: #f8fafd; border: 1.5px solid #b3c6e0; border-radius: 10px; margin: 6px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); font-weight: bold; } QGroupBox::indicator { width: 24px; height: 24px; }")
        vbox = QVBoxLayout(group)
        vbox.setContentsMargins(8, 4, 8, 4)
        enable_row = QHBoxLayout()
        enable_checkbox = QCheckBox("Enable Rule")
        enable_checkbox.setChecked(True)
        enable_checkbox.setToolTip("Enable or disable this rule without deleting it.")
        enable_checkbox.stateChanged.connect(self.generate_break_list)
        enable_checkbox.stateChanged.connect(self._enforce_percent_rule_limits)
        vbox.addLayout(enable_row)
        vbox.addWidget(rule_widget)
        # Remove forced collapse logic: allow multiple rules to be expanded at once
        def on_toggle(checked):
            rule_widget.setVisible(checked)
        group.toggled.connect(on_toggle)
        remove_btn = QPushButton()
        remove_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        remove_btn.setToolTip("Remove this rule")
        remove_btn.setFixedSize(28, 28)
        remove_btn.setStyleSheet("border: none; background: transparent;")
        remove_btn.clicked.connect(lambda: self.remove_rule_card(group, rule_widget))
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(remove_btn)
        vbox.addLayout(hbox)
        group._rule_widget = rule_widget
        group._enable_checkbox = enable_checkbox
        self.rules_area_layout.addWidget(group)
        self.rule_widgets.append(rule_widget)
        # Connect percent_value change to enforcement
        rule_widget.percent_value.valueChanged.connect(self._enforce_percent_rule_limits)
        self.generate_break_list()
        group.setChecked(True)  # Expand the new rule by default
    def remove_rule_card(self, group, rule_widget):
        # Animate rule removal (optional, can use QPropertyAnimation for fade-out)
        group.setVisible(False)
        self.rules_area_layout.removeWidget(group)
        group.deleteLater()
        if rule_widget in self.rule_widgets:
            self.rule_widgets.remove(rule_widget)
        self.generate_break_list()
    def show_help_dialog(self):
        msg = (
            "<b>Break/Autobox Builder Quick Tips</b><br><br>"
            "<b>Step 1:</b> <b>Filter Inventory</b> — Use the sidebar to filter your cards. Only visible cards are used for rules.<br>"
            "<b>Step 2:</b> <b>Curate Must-Haves</b> — Select cards you want guaranteed in the break and add them to the curated list.<br>"
            "<b>Step 3:</b> <b>Set Rules</b> — Add rules to select cards by price, rarity, set, etc. Rules only use filtered cards.<br>"
            "<b>Step 4:</b> <b>Generate Break</b> — Click 'Generate Break List' to preview and export your break.<br><br>"
            "<b>Tips:</b><ul>"
            "<li>Click filter chips to remove individual filters.</li>"
            "<li>Use the 'Clear All Filters' button to reset filters.</li>"
            "<li>Collapse the rule builder for a simpler view.</li>"
            "<li>All actions are keyboard accessible and have tooltips.</li>"
            "<li>Use the 'Simple/Advanced' toggle (coming soon) for more/less options.</li>"
            "</ul>"
        )
        QMessageBox.information(self, "Break Builder Help", msg)
    # --- Save/Load Rule Set ---
    def save_rule_set(self):
        """Save the current set of rules (enabled and disabled) to a template file."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        rules = []
        for i in range(self.rules_area_layout.count()):
            item = self.rules_area_layout.itemAt(i)
            if not item or not item.widget():
                continue
            group = item.widget()
            rule_widget = getattr(group, '_rule_widget', None)
            enable_checkbox = getattr(group, '_enable_checkbox', None)
            if not rule_widget or not enable_checkbox:
                continue
            rule = rule_widget.get_rule()
            rule['enabled'] = enable_checkbox.isChecked()
            rules.append(rule)
        if not rules:
            QMessageBox.warning(self, "Save Rule Set", "No rules to save.")
            return
        fname, _ = QFileDialog.getSaveFileName(self, "Save Rule Set", "break_rule_set.json", "JSON Files (*.json)")
        if not fname:
            return
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=2)
        QMessageBox.information(self, "Saved", f"Rule set saved to {fname}.")

    def load_rule_set(self):
        """Load a rule set from a template file, replacing current rules."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        fname, _ = QFileDialog.getOpenFileName(self, "Load Rule Set", "", "JSON Files (*.json)")
        if not fname:
            return
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                rules = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Load Rule Set", f"Failed to load rule set: {e}")
            return
        # Remove all current rules
        for i in reversed(range(self.rules_area_layout.count())):
            item = self.rules_area_layout.itemAt(i)
            if item and item.widget():
                group = item.widget()
                rule_widget = getattr(group, '_rule_widget', None)
                self.rules_area_layout.removeWidget(group)
                group.deleteLater()
                if rule_widget in self.rule_widgets:
                    self.rule_widgets.remove(rule_widget)
        # Add loaded rules (restore enabled/disabled state)
        for rule_data in rules:
            rule = dict(rule_data)
            enabled = rule.pop('enabled', True)
            self.add_rule(rule)
            group = self.rules_area_layout.itemAt(self.rules_area_layout.count()-1).widget()
            enable_checkbox = getattr(group, '_enable_checkbox', None)
            if enable_checkbox:
                enable_checkbox.setChecked(enabled)
        self.generate_break_list()

    # Add Save/Load Rule Set buttons to the rules area
    def _add_rule_set_buttons(self, parent_layout):
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save Rule Set")
        save_btn.setStyleSheet("padding: 6px 18px; border-radius: 8px; background: #1976d2; color: white; font-weight: bold; font-size: 13px;")
        save_btn.setToolTip("Save the current set of rules as a template.")
        save_btn.clicked.connect(self.save_rule_set)
        load_btn = QPushButton("📂 Load Rule Set")
        load_btn.setStyleSheet("padding: 6px 18px; border-radius: 8px; background: #388e3c; color: white; font-weight: bold; font-size: 13px;")
        load_btn.setToolTip("Load a saved rule set template, replacing current rules.")
        load_btn.clicked.connect(self.load_rule_set)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(load_btn)
        btn_row.addStretch(1)
        parent_layout.addLayout(btn_row)
    def remove_break_cards_from_inventory(self):
        """Remove all cards in the current break list from the inventory, with confirmation."""
        from PySide6.QtWidgets import QMessageBox
        if not self.current_break_list:
            QMessageBox.warning(self, "Remove from Inventory", "No break list generated. Please generate the break list first.")
            return
        card_count = len(self.current_break_list)
        reply = QMessageBox.question(
            self,
            "Confirm Remove from Inventory",
            f"Are you sure you want to remove all {card_count} cards in the current break list from inventory? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.last_removed_cards = list(self.current_break_list)
        # Use batch removal for robustness
        if hasattr(self.inventory, 'remove_cards'):
            self.inventory.remove_cards(self.current_break_list)
            removed = len(self.last_removed_cards)
        else:
            removed = 0
            for card in self.current_break_list:
                try:
                    self.inventory.remove_card(card)
                    removed += 1
                except Exception:
                    pass
        self.filtered_inventory = self.inventory.get_all_cards()
        self.card_table.update_cards(self.filtered_inventory)
        self.card_table.repaint()
        self.generate_break_list()
        self.undo_remove_btn.setEnabled(bool(self.last_removed_cards))
        QMessageBox.information(self, "Removed from Inventory", f"Removed {removed} cards from inventory.")

    def undo_remove_from_inventory(self):
        """Restore the last removed set of cards to inventory."""
        from PySide6.QtWidgets import QMessageBox
        if not self.last_removed_cards:
            QMessageBox.information(self, "Undo Remove", "No removal to undo.")
            return
        # Use batch add if available, else loop
        if hasattr(self.inventory, 'add_cards'):
            self.inventory.add_cards(self.last_removed_cards)
            restored = len(self.last_removed_cards)
        else:
            restored = 0
            for card in self.last_removed_cards:
                try:
                    self.inventory.add_card(card)
                    restored += 1
                except Exception:
                    pass
        self.filtered_inventory = self.inventory.get_all_cards()
        self.card_table.update_cards(self.filtered_inventory)
        self.card_table.repaint()
        self.generate_break_list()
        self.last_removed_cards = []
        self.undo_remove_btn.setEnabled(False)
        QMessageBox.information(self, "Undo Remove", f"Restored {restored} cards to inventory.") 