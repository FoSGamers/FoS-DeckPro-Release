from PySide6.QtCore import Qt

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
    # Add a rule: 3 rare cards, price 5-20
    rule_widget = BreakRuleWidget(dlg)
    rule_widget.count_type.setCurrentIndex(0)  # Count
    rule_widget.count_value.setValue(3)
    # Set rarity to 'rare'
    for field, widget in rule_widget.field_selectors.items():
        if field == "Rarity":
            idx = widget.findText("rare")
            widget.setCurrentIndex(idx)
        if field == "Price":
            widget[0].setValue(5)  # min
            widget[1].setValue(20)  # max
    dlg.rule_widgets = [rule_widget]
    # Simulate clicking generate
    dlg.total_cards_input.setValue(8)
    dlg.generate_break_list()
    preview = dlg.break_preview_box.text()
    # Should have sections for curated, rule, and filler
    assert "Curated Cards:" in preview
    assert "Rule 1 (Count 3):" in preview
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
    preview2 = dlg.break_preview_box.text()
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