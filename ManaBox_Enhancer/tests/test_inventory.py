def test_export_to_whatnot(tmp_path):
    from ManaBox_Enhancer.ui.main_window import MainWindow
    import csv
    mw = MainWindow()
    # Sample card
    cards = [{
        "Name": "Paradise Plume",
        "Set name": "Time Spiral Remastered",
        "Collector number": "271",
        "Whatnot price": "$1.00",
        "Condition": "Near Mint",
        "Purchase price": "$0.25",
        "Quantity": "2",
        "SKU": "TSR-271",
        "Scryfall image": "https://img.scryfall.com/cards/large/front/2/7/271.jpg"
    }]
    mw.card_table.update_cards(cards)
    # Patch QFileDialog to auto-select a file
    out_csv = tmp_path / "whatnot_export.csv"
    mw.QFileDialog = type("QFileDialog", (), {"getSaveFileName": staticmethod(lambda *a, **k: (str(out_csv), "CSV Files (*.csv)"))})
    mw.export_to_whatnot()
    # Check output
    with open(out_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        row = rows[0]
        assert row["Title"] == "Paradise Plume"
        assert row["Description"] == "Paradise Plume - Time Spiral Remastered (271)"
        assert row["Quantity"] == "2"
        assert row["Price"] == "$1.00"
        assert row["Condition"] == "Near Mint"
        assert row["Cost Per Item"] == "$0.25"
        assert row["SKU"] == "TSR-271"
        assert row["Image URL 1"] == "https://img.scryfall.com/cards/large/front/2/7/271.jpg"

def test_bulk_remove_and_edit(tmp_path):
    from ManaBox_Enhancer.models.inventory import CardInventory
    from ManaBox_Enhancer.ui.dialogs.bulk_edit_remove import BulkEditRemoveDialog
    # Setup inventory
    cards = [
        {"Name": "A", "Set name": "Set1", "Collector number": "1", "Condition": "NM"},
        {"Name": "B", "Set name": "Set2", "Collector number": "2", "Condition": "NM"},
        {"Name": "C", "Set name": "Set3", "Collector number": "3", "Condition": "NM"},
    ]
    inv = CardInventory()
    inv.load_cards(cards)
    # Bulk remove
    inv.remove_cards([cards[0], cards[2]])
    remaining = inv.get_all_cards()
    assert len(remaining) == 1
    assert remaining[0]["Name"] == "B"
    # Bulk edit
    inv.load_cards(cards)
    for card in cards:
        card["Condition"] = "NM"
    # Simulate bulk edit: set Condition to 'PL' for all
    for card in cards:
        card["Condition"] = "PL"
    inv.load_cards(cards)
    for card in inv.get_all_cards():
        assert card["Condition"] == "PL"

def test_main_window_gui_interaction(qtbot):
    """
    Advanced GUI test: Open the main window, simulate menu interaction, and check UI state.
    Requires pytest-qt (pip install pytest-qt).
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    # Create the main window
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Simulate clicking the 'File' menu and 'Add Card...'
    menubar = window.menuBar()
    file_menu = menubar.actions()[0].menu()  # 'File' menu
    add_card_action = None
    for action in file_menu.actions():
        if action.text() == 'Add Card...':
            add_card_action = action
            break
    assert add_card_action is not None, "Add Card action not found in File menu."
    # Trigger the action (would open the Add Card dialog)
    qtbot.mouseClick(menubar, qtbot.QtCore.Qt.LeftButton)
    add_card_action.trigger()
    # The dialog should appear; we can check for its existence
    # (In a real test, you would interact with the dialog here)
    assert window.isVisible(), "Main window should remain visible after menu interaction."
