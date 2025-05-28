from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QComboBox, QDoubleSpinBox

def test_break_builder_sidebar_filters_and_chips(qtbot):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": "Alpha", "Set name": "SetA", "Price": "5"},
                {"Name": "Beta", "Set name": "SetB", "Price": "10"},
                {"Name": "Gamma", "Set name": "SetC", "Price": "15"},
            ]
        def get_all_cards(self):
            return self.cards
        def remove_card(self, card):
            self.cards.remove(card)
        def add_card(self, card):
            self.cards.append(card)
        def filter_cards(self, filters):
            # Substring match for all fields (treat as strings)
            result = []
            for card in self.cards:
                match = True
                for k, v in filters.items():
                    if not v:
                        continue
                    card_val = str(card.get(k, ""))
                    if v.lower() not in card_val.lower():
                        match = False
                        break
                if match:
                    result.append(card)
            return result
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Test sidebar and filter chips
    price_filter = dlg.filter_inputs.get("Price")
    assert price_filter is not None, "Price filter input should exist."
    qtbot.keyClicks(price_filter, "10")
    qtbot.wait(100)
    dlg.update_table_filter()
    # Should show only Beta (check CardTableView model)
    filtered_cards = dlg.card_table.model.cards
    assert len(filtered_cards) == 1
    assert "Beta" in filtered_cards[0]["Name"]
    # Should show a filter chip
    chips = [dlg.active_filter_chips_layout.itemAt(i).widget() for i in range(dlg.active_filter_chips_layout.count()) if dlg.active_filter_chips_layout.itemAt(i).widget()]
    assert any("Price" in chip.text() for chip in chips), "Active filter chip for Price should be shown."
    # Remove filter via chip
    for chip in chips:
        if "Price" in chip.text():
            qtbot.mouseClick(chip, Qt.LeftButton)
            break
    qtbot.wait(100)
    filtered_cards = dlg.card_table.model.cards
    assert len(filtered_cards) == 3, "All cards should be shown after removing filter."
    # Test clear all filters
    qtbot.keyClicks(price_filter, "10")
    qtbot.wait(100)
    qtbot.mouseClick(dlg.clear_filters_btn, Qt.LeftButton)
    qtbot.wait(100)
    filtered_cards = dlg.card_table.model.cards
    assert len(filtered_cards) == 3, "All cards should be shown after clearing all filters."
    # Test resizability
    old_size = dlg.size()
    dlg.resize(1400, 900)
    qtbot.wait(100)
    new_size = dlg.size()
    assert new_size.width() > old_size.width() and new_size.height() > old_size.height(), "Dialog should be resizable."

def test_generate_break_list_with_rules_and_curated(qtbot):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog, BreakRuleWidget
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": f"Card{i}", "Set name": "SetA", "Price": str(i), "Rarity": "rare" if i % 2 == 0 else "common"}
                for i in range(1, 21)
            ]
        def get_all_cards(self):
            return self.cards
        def remove_card(self, card):
            self.cards.remove(card)
        def add_card(self, card):
            self.cards.append(card)
        def filter_cards(self, filters):
            result = []
            for card in self.cards:
                match = True
                for k, v in filters.items():
                    if v and v.lower() not in str(card.get(k, "")).lower():
                        match = False
                        break
                if match:
                    result.append(card)
            return result
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add some curated cards
    dlg.curated_cards = [inv.cards[0], inv.cards[1]]
    dlg.update_curated_table()
    # Add a rule: 3 rare cards, price 5-20 using new API
    rule_widget = BreakRuleWidget(dlg, inventory_fields=dlg.filter_fields, inventory=inv)
    rule_widget.count_type.setCurrentIndex(0)  # Count
    rule_widget.count_value.setValue(3)
    # Set up two criteria: Rarity = 'rare', Price 5-20
    # Remove default criterion row and add two
    while len(rule_widget.criteria_widgets) > 0:
        field_dropdown, input_widget, remove_btn = rule_widget.criteria_widgets[0]
        remove_btn.click()
    rule_widget.add_criterion_row("Rarity")
    field_dropdown, input_widget, _ = rule_widget.criteria_widgets[-1]
    idx = field_dropdown.findText("Rarity")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, QComboBox):
        idx2 = inp.findText("rare")
        if idx2 >= 0:
            inp.setCurrentIndex(idx2)
    rule_widget.add_criterion_row("Price")
    field_dropdown, input_widget, _ = rule_widget.criteria_widgets[-1]
    idx = field_dropdown.findText("Price")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, tuple):
        inp[0].setValue(5)  # min
        inp[1].setValue(20)  # max
    dlg.rule_widgets = [rule_widget]
    # Simulate clicking generate
    dlg.total_cards_input.setValue(8)
    dlg.generate_break_list()
    preview = dlg.break_preview_box.toPlainText()
    # Should have sections for curated, rule, and filler
    assert "Curated Cards:" in preview
    assert any(line.startswith("Rule (") for line in preview.splitlines()), preview
    assert "Filler Cards:" in preview or preview.count("Card") == 8
    # Should not have duplicates
    lines = [line.strip() for line in preview.splitlines() if line.strip() and not line.endswith(":")]
    assert len(set(lines)) == len(lines), "Break list should not have duplicate cards."
    # Should match total needed
    assert len(lines) == 8, f"Expected 8 cards in break, got {len(lines)}"
    # Should warn if not enough cards for a rule
    rule_widget.count_value.setValue(100)
    dlg.generate_break_list()
    # Should still not exceed available cards (10 rare cards in inventory)
    preview2 = dlg.break_preview_box.toPlainText()
    lines2 = [line.strip() for line in preview2.splitlines() if line.strip() and not line.endswith(":")]
    assert len(set(lines2)) == len(lines2)
    assert len(lines2) == 10 or len(lines2) == dlg.total_cards_input.value()

def test_break_builder_total_cards_input_exists_and_usable(qtbot):
    """
    Regression test: Ensure BreakBuilderDialog always initializes total_cards_input before any method uses it.
    All required UI elements must be initialized before use, and tests must catch missing/unused attributes.
    """
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def get_all_cards(self):
            return [{"Name": "Test", "Set name": "SetA", "Price": "5"} for _ in range(10)]
        def filter_cards(self, filters):
            return self.get_all_cards()
        def remove_card(self, card):
            pass
        def add_card(self, card):
            pass
    dlg = BreakBuilderDialog(DummyInventory())
    qtbot.addWidget(dlg)
    # Should not raise AttributeError
    try:
        dlg.generate_break_list()
    except AttributeError as e:
        assert False, f"AttributeError raised: {e}"
    # The input should exist and be functional
    assert hasattr(dlg, "total_cards_input"), "total_cards_input should exist"
    assert dlg.total_cards_input.value() > 0

def test_curated_card_add_animation(qtbot):
    """
    Test that adding a card to the curated list triggers the animation overlay for visual feedback.
    This checks that a QWidget overlay is created and fades out after adding a card.
    """
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": "Alpha", "Set name": "SetA", "Price": "5"},
                {"Name": "Beta", "Set name": "SetB", "Price": "10"},
            ]
        def get_all_cards(self):
            return self.cards
        def filter_cards(self, filters):
            return self.cards
        def remove_card(self, card):
            pass
        def add_card(self, card):
            pass
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    qtbot.waitExposed(dlg)
    # Add a card to curated list
    dlg.curated_cards = [inv.cards[0]]
    # Call animation directly with test_mode=True for robust test
    dlg._animate_table_row(dlg.curated_table, 0, added=True, test_mode=True)
    dlg.curated_table.viewport().repaint()  # Force paint event for overlay
    qtbot.wait(50)  # Allow animation to start
    # Check for overlay widget on the curated_table viewport
    # In headless/minimal environments, isVisible may be False, so check by type only
    overlays = [w for w in dlg.curated_table.viewport().findChildren(QWidget) if w != dlg.curated_table]
    assert overlays, "Animation overlay should be present after adding a curated card (type check, headless safe)."
    # Wait for animation to finish and overlay to be deleted
    qtbot.wait(700)
    overlays_after = [w for w in dlg.curated_table.viewport().findChildren(QWidget) if w.isVisible() and w != dlg.curated_table]
    assert not overlays_after, "Animation overlay should be gone after fade-out."

def test_multiple_enabled_rules(qtbot):
    """
    Test that multiple enabled rules are all used, and disabling a rule excludes it from the break list.
    """
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": f"Card{i}", "Set name": "SetA", "Price": str(i), "Rarity": "rare" if i % 2 == 0 else "common"}
                for i in range(1, 21)
            ]
        def get_all_cards(self):
            return self.cards
        def filter_cards(self, filters):
            return self.cards
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add two rules via UI
    dlg.add_rule()
    dlg.add_rule()
    # Set up Rule 1: 3 rare cards
    group1 = dlg.rules_area_layout.itemAt(0).widget()
    rule1 = getattr(group1, '_rule_widget')
    rule1.count_type.setCurrentIndex(0)
    rule1.count_value.setValue(3)
    # Remove default criterion row and add Rarity=rare
    while len(rule1.criteria_widgets) > 0:
        field_dropdown, input_widget, remove_btn = rule1.criteria_widgets[0]
        remove_btn.click()
    rule1.add_criterion_row("Rarity")
    field_dropdown, input_widget, _ = rule1.criteria_widgets[-1]
    idx = field_dropdown.findText("Rarity")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, QComboBox):
        idx2 = inp.findText("rare")
        if idx2 >= 0:
            inp.setCurrentIndex(idx2)
    # Set up Rule 2: 2 common cards
    group2 = dlg.rules_area_layout.itemAt(1).widget()
    rule2 = getattr(group2, '_rule_widget')
    rule2.count_type.setCurrentIndex(0)
    rule2.count_value.setValue(2)
    while len(rule2.criteria_widgets) > 0:
        field_dropdown, input_widget, remove_btn = rule2.criteria_widgets[0]
        remove_btn.click()
    rule2.add_criterion_row("Rarity")
    field_dropdown, input_widget, _ = rule2.criteria_widgets[-1]
    idx = field_dropdown.findText("Rarity")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, QComboBox):
        idx2 = inp.findText("common")
        if idx2 >= 0:
            inp.setCurrentIndex(idx2)
    # Enable both rules
    getattr(group1, '_enable_checkbox').setChecked(True)
    getattr(group2, '_enable_checkbox').setChecked(True)
    dlg.total_cards_input.setValue(6)
    dlg.generate_break_list()
    preview = dlg.break_preview_box.toPlainText()
    # Check for both rule section headers in the new format
    assert any(line.startswith("Rule (") and "Rarity: rare" in line for line in preview.splitlines()), preview
    assert any(line.startswith("Rule (") and "Rarity: common" in line for line in preview.splitlines()), preview
    # Disable Rule 2
    getattr(group2, '_enable_checkbox').setChecked(False)
    dlg.generate_break_list()
    preview2 = dlg.break_preview_box.toPlainText()
    # Only the rare rule should be present
    assert any(line.startswith("Rule (") and "Rarity: rare" in line for line in preview2.splitlines()), preview2
    assert not any(line.startswith("Rule (") and "Rarity: common" in line for line in preview2.splitlines()), preview2

def test_save_load_rule_set(qtbot, tmp_path):
    """
    Test saving and loading a rule set template.
    """
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    import os, json
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": f"Card{i}", "Set name": "SetA", "Price": str(i), "Rarity": "rare" if i % 2 == 0 else "common"}
                for i in range(1, 21)
            ]
        def get_all_cards(self):
            return self.cards
        def filter_cards(self, filters):
            return self.cards
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add a rule and set it up
    dlg.add_rule()
    group = dlg.rules_area_layout.itemAt(0).widget()
    rule = getattr(group, '_rule_widget')
    rule.count_type.setCurrentIndex(2)  # % of available
    rule.percent_value.setValue(50)
    # Save rule set
    fname = tmp_path / "test_rule_set.json"
    rules = [rule.get_rule()]
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2)
    # Remove all rules
    for i in reversed(range(dlg.rules_area_layout.count())):
        item = dlg.rules_area_layout.itemAt(i)
        if item and item.widget():
            group = item.widget()
            rule_widget = getattr(group, '_rule_widget', None)
            dlg.rules_area_layout.removeWidget(group)
            group.deleteLater()
            if rule_widget in dlg.rule_widgets:
                dlg.rule_widgets.remove(rule_widget)
    # Load rule set
    with open(fname, 'r', encoding='utf-8') as f:
        loaded_rules = json.load(f)
    for rule_data in loaded_rules:
        dlg.add_rule(rule_data)
    dlg.generate_break_list()
    preview = dlg.break_preview_box.toPlainText()
    assert any(line.startswith("Rule (") for line in preview.splitlines()), "Loaded rule should be used in break list.\n" + preview

def test_percent_based_rules_allocation(qtbot):
    """
    Test that percent-based rules allocate the correct number of cards from the total break size.
    """
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": f"Card{i}", "Set name": "SetA", "Price": str(i), "Rarity": "rare" if i % 2 == 0 else "common"}
                for i in range(1, 21)
            ]
        def get_all_cards(self):
            return self.cards
        def filter_cards(self, filters):
            return self.cards
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add two percent-based rules via UI
    dlg.add_rule()
    dlg.add_rule()
    group1 = dlg.rules_area_layout.itemAt(0).widget()
    rule1 = getattr(group1, '_rule_widget')
    rule1.count_type.setCurrentIndex(1)  # % of available
    rule1.percent_value.setValue(60)
    # Remove default criterion row and add Rarity=rare
    while len(rule1.criteria_widgets) > 0:
        field_dropdown, input_widget, remove_btn = rule1.criteria_widgets[0]
        remove_btn.click()
    rule1.add_criterion_row("Rarity")
    field_dropdown, input_widget, _ = rule1.criteria_widgets[-1]
    idx = field_dropdown.findText("Rarity")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, QComboBox):
        idx2 = inp.findText("rare")
        if idx2 >= 0:
            inp.setCurrentIndex(idx2)
    group2 = dlg.rules_area_layout.itemAt(1).widget()
    rule2 = getattr(group2, '_rule_widget')
    rule2.count_type.setCurrentIndex(1)
    rule2.percent_value.setValue(40)
    while len(rule2.criteria_widgets) > 0:
        field_dropdown, input_widget, remove_btn = rule2.criteria_widgets[0]
        remove_btn.click()
    rule2.add_criterion_row("Rarity")
    field_dropdown, input_widget, _ = rule2.criteria_widgets[-1]
    idx = field_dropdown.findText("Rarity")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, QComboBox):
        idx2 = inp.findText("common")
        if idx2 >= 0:
            inp.setCurrentIndex(idx2)
    getattr(group1, '_enable_checkbox').setChecked(True)
    getattr(group2, '_enable_checkbox').setChecked(True)
    dlg.total_cards_input.setValue(10)
    dlg.generate_break_list()
    preview = dlg.break_preview_box.toPlainText()
    # Should allocate 6 to rule 1, 4 to rule 2
    assert "Rule (60.0% of filtered (Rarity: rare)):" in preview
    assert "Rule (40.0% of filtered (Rarity: common)):" in preview
    rule1_count = sum(1 for line in preview.splitlines() if line.strip() and not line.endswith(":") and "Rarity: rare" in line)
    rule2_count = sum(1 for line in preview.splitlines() if line.strip() and not line.endswith(":") and "Rarity: common" in line)
    assert rule1_count == 6, f"Expected 6 cards for rule 1, got {rule1_count}"
    assert rule2_count == 4, f"Expected 4 cards for rule 2, got {rule2_count}"
    # Now test sum > 100%: set both to 70% (should allocate 7 and 3)
    rule1.percent_value.setValue(70)
    rule2.percent_value.setValue(70)
    dlg.generate_break_list()
    preview2 = dlg.break_preview_box.toPlainText()
    rule1_count2 = sum(1 for line in preview2.splitlines() if line.strip() and not line.endswith(":") and "Rarity: rare" in line)
    rule2_count2 = sum(1 for line in preview2.splitlines() if line.strip() and not line.endswith(":") and "Rarity: common" in line)
    assert rule1_count2 + rule2_count2 == 10, f"Total allocated should be 10, got {rule1_count2 + rule2_count2}"
    assert rule1_count2 >= 1 and rule2_count2 >= 1, "Each rule should get at least 1 card if possible."

def test_break_preview_shows_rule_fields(qtbot):
    """
    Test that the break list preview shows rule-relevant fields next to each card name for rule-based selections.
    """
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog, BreakRuleWidget
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": "CardA", "Set name": "SetX", "Price": "5", "Rarity": "rare", "Foil": "Yes"},
                {"Name": "CardB", "Set name": "SetY", "Price": "10", "Rarity": "common", "Foil": "No"},
                {"Name": "CardC", "Set name": "SetZ", "Price": "15", "Rarity": "rare", "Foil": "No"},
            ]
        def get_all_cards(self):
            return self.cards
        def filter_cards(self, filters):
            return self.cards
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add a rule: select 2 cards, Rarity=rare, Price 5-15
    dlg.add_rule()
    group = dlg.rules_area_layout.itemAt(0).widget()
    rule_widget = getattr(group, '_rule_widget')
    rule_widget.count_type.setCurrentIndex(0)  # Count
    rule_widget.count_value.setValue(2)
    # Remove default criterion row and add Rarity and Price
    while len(rule_widget.criteria_widgets) > 0:
        field_dropdown, input_widget, remove_btn = rule_widget.criteria_widgets[0]
        remove_btn.click()
    rule_widget.add_criterion_row("Rarity")
    field_dropdown, input_widget, _ = rule_widget.criteria_widgets[-1]
    idx = field_dropdown.findText("Rarity")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, QComboBox):
        idx2 = inp.findText("rare")
        if idx2 >= 0:
            inp.setCurrentIndex(idx2)
    rule_widget.add_criterion_row("Price")
    field_dropdown, input_widget, _ = rule_widget.criteria_widgets[-1]
    idx = field_dropdown.findText("Price")
    if idx >= 0:
        field_dropdown.setCurrentIndex(idx)
    inp = getattr(input_widget, '_field_input', None)
    if isinstance(inp, tuple):
        inp[0].setValue(5)
        inp[1].setValue(15)
    # Generate break list
    dlg.total_cards_input.setValue(2)
    dlg.generate_break_list()
    preview = dlg.break_preview_box.toPlainText()
    # Both rare cards should be present, with Price and Rarity shown next to name
    assert "CardA [SetX]" in preview
    assert "CardC [SetZ]" in preview
    # Should show (Price: 5, Rarity: rare) and (Price: 15, Rarity: rare) in the preview lines
    assert any("CardA [SetX]" in line and "Price: 5" in line and "Rarity: rare" in line for line in preview.splitlines()), preview
    assert any("CardC [SetZ]" in line and "Price: 15" in line and "Rarity: rare" in line for line in preview.splitlines()), preview 