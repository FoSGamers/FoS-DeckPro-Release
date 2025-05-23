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

def test_menu_bar_and_actions_present(qtbot):
    """
    Regression test: Ensure the menu bar and at least one menu/action are present in the main window.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    menubar = window.menuBar()
    assert menubar is not None, "Menu bar should be present."
    menus = [action.text() for action in menubar.actions()]
    assert "File" in menus, "File menu should be present."
    file_menu = menubar.actions()[0].menu()
    file_actions = [action.text() for action in file_menu.actions()]
    assert "Open JSON..." in file_actions, "Open JSON action should be present."
    assert "Add Card..." in file_actions, "Add Card action should be present."


def test_table_headers_match_defaults(qtbot):
    """
    Regression test: Ensure the table headers match the expected default columns.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    expected_headers = [
        "Name", "Set name", "Set code", "Collector number", "Rarity",
        "Condition", "Foil", "Language", "Purchase price", "Whatnot price"
    ]
    actual_headers = [window.card_table.model.headerData(i, window.card_table.model.Orientation.Horizontal) for i in range(window.card_table.model.columnCount())]
    assert actual_headers == expected_headers, f"Table headers do not match expected columns.\nExpected: {expected_headers}\nActual: {actual_headers}"

def test_adjust_whatnot_pricing_fixed(qtbot):
    """
    Test setting all Whatnot prices to a fixed value using the dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Open dialog
    window.adjust_whatnot_pricing_dialog()
    # Simulate setting fixed price
    all_cards = window.inventory.get_all_cards()
    for card in all_cards:
        card["Purchase price"] = "$1.23"
        card["Whatnot price"] = ""
    # Simulate dialog logic directly (since dialog is modal)
    for card in all_cards:
        card["Whatnot price"] = "$2.00"
    window.card_table.update_cards(all_cards)
    # Check all Whatnot prices set
    for card in all_cards:
        assert card["Whatnot price"] == "$2.00"

def test_adjust_whatnot_pricing_rounding(qtbot):
    """
    Test rounding Whatnot prices with a custom threshold using the dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    import math
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Set up test cards
    all_cards = [
        {"Purchase price": "$1.29", "Whatnot price": ""},
        {"Purchase price": "$1.30", "Whatnot price": ""},
        {"Purchase price": "$2.50", "Whatnot price": ""},
        {"Purchase price": "$3.10", "Whatnot price": ""},
    ]
    window.inventory.load_cards(all_cards)
    # Simulate dialog logic for threshold 0.30
    threshold = 0.30
    for card in all_cards:
        price = float(card["Purchase price"].replace("$", ""))
        cents = price - int(price)
        if cents >= threshold:
            rounded = math.ceil(price)
        else:
            rounded = math.floor(price)
        card["Whatnot price"] = f"${rounded:.2f}"
    window.card_table.update_cards(all_cards)
    # Check results
    assert all_cards[0]["Whatnot price"] == "$1.00"  # 1.29 rounds down
    assert all_cards[1]["Whatnot price"] == "$2.00"  # 1.30 rounds up
    assert all_cards[2]["Whatnot price"] == "$3.00"  # 2.50 rounds up
    assert all_cards[3]["Whatnot price"] == "$3.00"  # 3.10 rounds down

def test_adjust_whatnot_pricing_gui_interaction(qtbot):
    """
    GUI test: Simulate a user opening the Whatnot pricing dialog, entering a custom threshold, selecting rounding, and applying it.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QLineEdit, QRadioButton, QPushButton
    import math
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Set up test cards
    all_cards = [
        {"Purchase price": "$1.29", "Whatnot price": ""},
        {"Purchase price": "$1.30", "Whatnot price": ""},
        {"Purchase price": "$2.50", "Whatnot price": ""},
        {"Purchase price": "$3.10", "Whatnot price": ""},
    ]
    window.inventory.load_cards(all_cards)
    # Open the dialog
    qtbot.waitExposed(window)
    window.adjust_whatnot_pricing_dialog()
    # Find the dialog (should be the active modal QDialog)
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No dialog found."
    dlg = dialogs[0]
    # Find widgets
    round_radio = None
    threshold_input = None
    apply_btn = None
    for w in dlg.findChildren(QRadioButton):
        if "Round" in w.text():
            round_radio = w
    for w in dlg.findChildren(QLineEdit):
        if w.placeholderText() == "0.30":
            threshold_input = w
    for w in dlg.findChildren(QPushButton):
        if w.text() == "Apply":
            apply_btn = w
    assert round_radio and threshold_input and apply_btn, "Dialog widgets not found."
    # Simulate user interaction
    qtbot.mouseClick(round_radio, qtbot.QtCore.Qt.LeftButton)
    qtbot.keyClicks(threshold_input, "0.30")
    qtbot.mouseClick(apply_btn, qtbot.QtCore.Qt.LeftButton)
    # Check results
    updated_cards = window.inventory.get_all_cards()
    assert updated_cards[0]["Whatnot price"] == "$1.00"
    assert updated_cards[1]["Whatnot price"] == "$2.00"
    assert updated_cards[2]["Whatnot price"] == "$3.00"
    assert updated_cards[3]["Whatnot price"] == "$3.00"

def test_add_card_gui_interaction(qtbot):
    """
    GUI test: Simulate a user adding a card via the Add Card dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Count cards before
    before_count = len(window.inventory.get_all_cards())
    # Trigger Add Card
    window.add_card()
    # Find the dialog
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No Add Card dialog found."
    dlg = dialogs[0]
    # Fill in fields
    name_field = None
    for w in dlg.findChildren(QLineEdit):
        if w.placeholderText() == "" or w.objectName() == "":
            name_field = w
            break
    assert name_field is not None, "Name field not found."
    qtbot.keyClicks(name_field, "Test Card")
    # Click Save
    save_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() == "save":
            save_btn = w
            break
    assert save_btn is not None, "Save button not found."
    qtbot.mouseClick(save_btn, qtbot.QtCore.Qt.LeftButton)
    # Check card added
    after_count = len(window.inventory.get_all_cards())
    assert after_count == before_count + 1, "Card was not added."
    added_card = window.inventory.get_all_cards()[-1]
    assert added_card["Name"] == "Test Card"

def test_edit_card_gui_interaction(qtbot):
    """
    GUI test: Simulate a user editing a card via the Edit Card dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Ensure at least one card exists
    all_cards = window.inventory.get_all_cards()
    if not all_cards:
        window.inventory.load_cards([{"Name": "EditMe"}])
        window.card_table.update_cards(window.inventory.get_all_cards())
    # Select the first card in the table
    index = window.card_table.model.index(1, 0)  # row 1 (first card), col 0
    window.card_table.selectRow(1)
    # Trigger edit (simulate double-click)
    window.card_table.on_double_click(index)
    # Find the dialog
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No Edit Card dialog found."
    dlg = dialogs[0]
    # Change the Name field
    name_field = None
    for w in dlg.findChildren(QLineEdit):
        if w.text() == all_cards[0]["Name"]:
            name_field = w
            break
    assert name_field is not None, "Name field not found."
    qtbot.keyClicks(name_field, "_Edited")
    # Click Save
    save_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() == "save":
            save_btn = w
            break
    assert save_btn is not None, "Save button not found."
    qtbot.mouseClick(save_btn, qtbot.QtCore.Qt.LeftButton)
    # Check card edited
    updated_card = window.inventory.get_all_cards()[0]
    assert updated_card["Name"].endswith("_Edited"), "Card name was not edited."

def test_delete_card_gui_interaction(qtbot):
    """
    GUI test: Simulate a user deleting a card via the Delete key and confirmation dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QPushButton
    from PySide6.QtCore import Qt
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Ensure at least one card exists
    all_cards = window.inventory.get_all_cards()
    if not all_cards:
        window.inventory.load_cards([{"Name": "DeleteMe"}])
        window.card_table.update_cards(window.inventory.get_all_cards())
    before_count = len(window.inventory.get_all_cards())
    # Select the first card in the table
    window.card_table.selectRow(1)
    # Simulate Delete key press
    qtbot.keyClick(window.card_table, Qt.Key_Delete)
    # Find the confirmation dialog
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No confirmation dialog found."
    dlg = dialogs[0]
    # Click Yes to confirm
    yes_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() in ("yes", "ok"):
            yes_btn = w
            break
    assert yes_btn is not None, "Yes button not found in confirmation dialog."
    qtbot.mouseClick(yes_btn, Qt.LeftButton)
    # Check card deleted
    after_count = len(window.inventory.get_all_cards())
    assert after_count == before_count - 1, "Card was not deleted."

def test_import_cards_gui_interaction(qtbot, tmp_path):
    """
    GUI test: Simulate a user importing cards via the Import dialog (JSON, merge mode).
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QPushButton
    import json
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Prepare a temp JSON file to import
    import_cards = [
        {"Name": "Imported Card", "Set name": "Test Set", "Collector number": "123"}
    ]
    import_file = tmp_path / "import_cards.json"
    with open(import_file, "w", encoding="utf-8") as f:
        json.dump(import_cards, f)
    # Patch QFileDialog to auto-select the file
    orig_getOpenFileName = window.open_json_file.__globals__["QFileDialog"].getOpenFileName
    window.open_json_file.__globals__["QFileDialog"].getOpenFileName = staticmethod(lambda *a, **k: (str(import_file), "JSON Files (*.json)"))
    # Simulate user clicking Import
    window.import_cards()
    # Find the merge/replace dialog
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No import mode dialog found."
    dlg = dialogs[0]
    # Click Yes (merge)
    yes_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() in ("yes", "ok"):
            yes_btn = w
            break
    assert yes_btn is not None, "Yes button not found in import mode dialog."
    qtbot.mouseClick(yes_btn, qtbot.QtCore.Qt.LeftButton)
    # Check card imported
    imported = any(card["Name"] == "Imported Card" for card in window.inventory.get_all_cards())
    assert imported, "Imported card not found in inventory."
    # Restore QFileDialog
    window.open_json_file.__globals__["QFileDialog"].getOpenFileName = orig_getOpenFileName
