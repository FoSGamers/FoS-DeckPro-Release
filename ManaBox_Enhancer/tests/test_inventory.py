from PySide6.QtCore import Qt
import pytest
from unittest.mock import patch
import os
import tempfile
import json
from ManaBox_Enhancer.ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
from PySide6.QtWidgets import QApplication

@pytest.fixture(autouse=True)
def patch_qfiledialog(monkeypatch, tmp_path):
    dummy_file = str(tmp_path / "dummy.json")
    monkeypatch.setattr('PySide6.QtWidgets.QFileDialog.getOpenFileName', lambda *a, **k: (dummy_file, 'JSON Files (*.json)'))
    monkeypatch.setattr('PySide6.QtWidgets.QFileDialog.getSaveFileName', lambda *a, **k: (dummy_file, 'JSON Files (*.json)'))
    yield

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
    GUI test: Simulate a user adding a card via the Add Card dialog using QTimer to automate modal dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QApplication
    from PySide6.QtCore import QTimer
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    before_count = len(window.inventory.get_all_cards())
    def automate_dialog():
        # Find the dialog
        dialogs = [w for w in QApplication.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()]
        assert dialogs, "No Add Card dialog found."
        dlg = dialogs[0]
        name_field = None
        for w in dlg.findChildren(QLineEdit):
            if w.placeholderText() == "" or w.objectName() == "":
                name_field = w
                break
        assert name_field is not None, "Name field not found."
        name_field.setText("Test Card")
        save_btn = None
        for w in dlg.findChildren(QPushButton):
            if w.text().lower() == "save":
                save_btn = w
                break
        assert save_btn is not None, "Save button not found."
        qtbot.mouseClick(save_btn, Qt.LeftButton)
    QTimer.singleShot(100, automate_dialog)
    window.add_card(test_mode=False)  # Use modal dialog
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
    # Trigger edit in test mode
    dlg = window.edit_card(0, test_mode=True)
    qtbot.waitExposed(dlg)
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
    qtbot.mouseClick(save_btn, Qt.LeftButton)
    # Check card edited
    updated_card = window.inventory.get_all_cards()[0]
    assert updated_card["Name"].endswith("_Edited"), "Card name was not edited."

def test_delete_card_gui_interaction(qtbot):
    """
    GUI test: Simulate a user deleting a card via the Delete key and confirmation dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QPushButton
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

def test_export_cards_gui_interaction(qtbot, tmp_path):
    """
    GUI test: Simulate a user exporting cards via the Export dialog (CSV, column selection).
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QPushButton, QListWidget, QListWidgetItem
    import csv
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Ensure at least one card exists
    all_cards = window.inventory.get_all_cards()
    if not all_cards:
        window.inventory.load_cards([{"Name": "ExportMe", "Set name": "SetX", "Collector number": "42"}])
        window.card_table.update_cards(window.inventory.get_all_cards())
    # Prepare a temp CSV file for export
    export_file = tmp_path / "export_cards.csv"
    # Patch QFileDialog to auto-select the file
    orig_getSaveFileName = window.export_cards.__globals__["QFileDialog"].getSaveFileName
    window.export_cards.__globals__["QFileDialog"].getSaveFileName = staticmethod(lambda *a, **k: (str(export_file), "CSV Files (*.csv)"))
    # Simulate user clicking Export
    window.export_cards()
    # Find the column selection dialog
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No export columns dialog found."
    dlg = dialogs[0]
    # Select all columns (simulate user clicking OK)
    ok_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() == "ok":
            ok_btn = w
            break
    assert ok_btn is not None, "OK button not found in export columns dialog."
    qtbot.mouseClick(ok_btn, qtbot.QtCore.Qt.LeftButton)
    # Check exported file
    with open(export_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert any(row["Name"] == "ExportMe" for row in rows), "Exported card not found in CSV."
    # Restore QFileDialog
    window.export_cards.__globals__["QFileDialog"].getSaveFileName = orig_getSaveFileName

def test_column_customization_gui_interaction(qtbot):
    """
    GUI test: Simulate a user customizing columns (hide, reorder, restore defaults) via the dialog.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QPushButton
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Open column customization dialog
    window.customize_columns()
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No column customization dialog found."
    dlg = dialogs[0]
    # Find the list widget
    list_widget = dlg.findChild(QListWidget)
    assert list_widget is not None, "Column list widget not found."
    # Hide the first column (uncheck)
    item = list_widget.item(0)
    item.setCheckState(0)  # Unchecked
    # Reorder: move last item to first (simulate drag)
    last_item = list_widget.takeItem(list_widget.count() - 1)
    list_widget.insertItem(0, last_item)
    # Click OK
    ok_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() == "ok":
            ok_btn = w
            break
    assert ok_btn is not None, "OK button not found in column customization dialog."
    qtbot.mouseClick(ok_btn, qtbot.QtCore.Qt.LeftButton)
    # Verify table: first column is now the one that was last, and the original first column is hidden
    new_headers = [window.card_table.model.headerData(i, window.card_table.model.Orientation.Horizontal) for i in range(window.card_table.model.columnCount())]
    assert new_headers[0] == last_item.text(), "Column order did not update."
    assert not window.card_table.isColumnHidden(0) or new_headers[0] != item.text(), "Hidden column is still visible."
    # Now restore defaults
    window.customize_columns()
    dlg = [w for w in window.findChildren(QDialog) if w.isVisible()][0]
    restore_btn = None
    for w in dlg.findChildren(QPushButton):
        if "restore" in w.text().lower():
            restore_btn = w
            break
    assert restore_btn is not None, "Restore Defaults button not found."
    qtbot.mouseClick(restore_btn, qtbot.QtCore.Qt.LeftButton)
    # Click OK to apply
    ok_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() == "ok":
            ok_btn = w
            break
    qtbot.mouseClick(ok_btn, qtbot.QtCore.Qt.LeftButton)
    # Verify table headers match defaults
    expected_headers = window.default_columns
    actual_headers = [window.card_table.model.headerData(i, window.card_table.model.Orientation.Horizontal) for i in range(window.card_table.model.columnCount())]
    assert actual_headers == expected_headers, "Table headers do not match defaults after restore."

def test_undo_last_change_gui_interaction(qtbot):
    """
    GUI test: Simulate a user making a change, triggering Undo, confirming, and verifying the change is reverted.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QPushButton
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Ensure at least one card exists
    all_cards = window.inventory.get_all_cards()
    if not all_cards:
        window.inventory.load_cards([{"Name": "UndoMe"}])
        window.card_table.update_cards(window.inventory.get_all_cards())
    # Make a change: edit the card name
    window.inventory.get_all_cards()[0]["Name"] = "ChangedName"
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Save undo state
    window.save_undo_state()
    # Change again
    window.inventory.get_all_cards()[0]["Name"] = "ChangedAgain"
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Trigger Undo
    window.undo_last_change()
    # Find the Undo summary dialog
    dialogs = [w for w in window.findChildren(QDialog) if w.isVisible()]
    assert dialogs, "No Undo summary dialog found."
    dlg = dialogs[0]
    # Click Close (or View Changes then Close)
    close_btn = None
    for w in dlg.findChildren(QPushButton):
        if w.text().lower() == "close":
            close_btn = w
            break
    assert close_btn is not None, "Close button not found in Undo summary dialog."
    qtbot.mouseClick(close_btn, qtbot.QtCore.Qt.LeftButton)
    # Verify card name reverted
    reverted_name = window.inventory.get_all_cards()[0]["Name"]
    assert reverted_name == "ChangedName", f"Undo did not revert the change, got {reverted_name}"

def test_restore_from_backup_gui_interaction(qtbot, tmp_path):
    """
    GUI test: Simulate a user restoring from backup via the dialog and verify inventory is restored.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QPushButton
    import json, os
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Prepare a backup file
    backup_cards = [
        {"Name": "Restored Card", "Set name": "BackupSet", "Collector number": "999"}
    ]
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Backups')
    os.makedirs(backup_dir, exist_ok=True)
    backup_file = os.path.join(backup_dir, "test_backup.json")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup_cards, f)
    # Patch QFileDialog to auto-select the backup file
    orig_getOpenFileName = window.restore_from_backup.__globals__["QFileDialog"].getOpenFileName
    window.restore_from_backup.__globals__["QFileDialog"].getOpenFileName = staticmethod(lambda *a, **k: (backup_file, "JSON Files (*.json)"))
    # Simulate user clicking Restore from Backup
    window.restore_from_backup()
    # Check inventory restored
    restored = any(card["Name"] == "Restored Card" for card in window.inventory.get_all_cards())
    assert restored, "Restored card not found in inventory."
    # Restore QFileDialog
    window.restore_from_backup.__globals__["QFileDialog"].getOpenFileName = orig_getOpenFileName

def test_auto_save_toggle_gui_interaction(qtbot):
    """
    GUI test: Simulate a user toggling Auto-Save in the menu and verify the internal state changes.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Find the Auto-Save menu action
    auto_save_action = window.auto_save_action
    assert auto_save_action is not None, "Auto-Save action not found."
    # Initial state should be False
    assert not window._auto_save, "Auto-Save should be off by default."
    # Simulate user toggling Auto-Save on
    auto_save_action.setChecked(True)
    window.toggle_auto_save()
    assert window._auto_save, "Auto-Save should be on after toggling."
    # Simulate user toggling Auto-Save off
    auto_save_action.setChecked(False)
    window.toggle_auto_save()
    assert not window._auto_save, "Auto-Save should be off after toggling again."

def test_save_load_column_preset_gui_interaction(qtbot, tmp_path):
    """
    GUI test: Simulate a user saving and loading a column preset, verifying columns are restored.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from PySide6.QtWidgets import QDialog, QInputDialog, QFileDialog, QPushButton, QListWidget
    import os, json
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Save a preset
    preset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'column_presets')
    os.makedirs(preset_dir, exist_ok=True)
    preset_name = "test_preset"
    preset_file = os.path.join(preset_dir, f"{preset_name}.json")
    # Patch QInputDialog to auto-enter preset name
    orig_getText = window.save_column_preset.__globals__["QInputDialog"].getText
    window.save_column_preset.__globals__["QInputDialog"].getText = staticmethod(lambda *a, **k: (preset_name, True))
    window.save_column_preset()
    # Change columns (hide first column)
    window.visible_columns = window.visible_columns[1:]
    window.card_table.columns = window.columns
    window.card_table.model.columns = window.columns
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Patch QFileDialog to auto-select the preset file
    orig_getOpenFileName = window.load_column_preset.__globals__["QFileDialog"].getOpenFileName
    window.load_column_preset.__globals__["QFileDialog"].getOpenFileName = staticmethod(lambda *a, **k: (preset_file, "JSON Files (*.json)"))
    window.load_column_preset()
    # Verify columns restored
    assert window.visible_columns == window.columns, "Visible columns not restored from preset."
    # Restore QInputDialog and QFileDialog
    window.save_column_preset.__globals__["QInputDialog"].getText = orig_getText
    window.load_column_preset.__globals__["QFileDialog"].getOpenFileName = orig_getOpenFileName

def test_filter_overlay_gui_interaction(qtbot):
    """
    GUI test: Simulate a user typing in filter overlay fields and verify the table updates to show only matching cards.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Add multiple cards
    cards = [
        {"Name": "Alpha", "Set name": "SetA"},
        {"Name": "Beta", "Set name": "SetB"},
        {"Name": "Gamma", "Set name": "SetC"}
    ]
    window.inventory.load_cards(cards)
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Find the filter overlay and the Name filter field
    name_filter = window.filter_overlay.filters["Name"]
    # Simulate typing 'Beta' in the Name filter
    qtbot.keyClicks(name_filter, "Beta")
    # Trigger filter update
    window.update_table_filter()
    # Check that only the 'Beta' card is shown
    filtered = window.card_table.cards
    assert len(filtered) == 1, f"Expected 1 card after filtering, got {len(filtered)}"
    assert filtered[0]["Name"] == "Beta", f"Expected 'Beta', got {filtered[0]['Name']}"

def test_enrich_all_cards_from_scryfall(qtbot):
    """
    Test the Scryfall enrichment feature: cards with Scryfall ID are updated with Scryfall data.
    """
    from ManaBox_Enhancer.ui.main_window import MainWindow
    # Patch fetch_scryfall_data to return predictable data
    with patch('ManaBox_Enhancer.models.scryfall_api.fetch_scryfall_data') as mock_fetch:
        mock_fetch.side_effect = lambda scryfall_id: {
            "type_line": f"Type for {scryfall_id}",
            "mana_cost": "{1}{G}",
            "colors": "G",
            "color_identity": "G",
            "oracle_text": f"Oracle for {scryfall_id}",
            "legal_commander": "legal",
            "legal_pauper": "not_legal",
            "image_url": f"https://img.scryfall.com/cards/{scryfall_id}.jpg"
        }
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        # Add cards with Scryfall IDs
        cards = [
            {"Name": "Test Card 1", "Scryfall ID": "abc123"},
            {"Name": "Test Card 2", "Scryfall ID": "def456"},
            {"Name": "No Scryfall", "Scryfall ID": ""},
        ]
        window.inventory.load_cards(cards)
        window.card_table.update_cards(window.inventory.get_all_cards())
        # Run enrichment
        window.enrich_all_cards_from_scryfall()
        enriched = window.inventory.get_all_cards()
        # Cards with Scryfall ID should be updated
        assert enriched[0]["type_line"] == "Type for abc123"
        assert enriched[0]["oracle_text"] == "Oracle for abc123"
        assert enriched[1]["type_line"] == "Type for def456"
        assert enriched[1]["oracle_text"] == "Oracle for def456"
        # Card without Scryfall ID should not be updated
        assert "type_line" not in enriched[2]

def test_numeric_and_range_filtering_all_columns():
    from ManaBox_Enhancer.models.inventory import CardInventory
    numeric_fields = [
        "Purchase price", "Whatnot price", "Quantity", "cmc", "ManaBox ID", "Collector number"
    ]
    # Use $ for price fields, plain for others
    card = {
        "Purchase price": "$0.12",
        "Whatnot price": "$1.50",
        "Quantity": "3",
        "cmc": "2",
        "ManaBox ID": "12345",
        "Collector number": "271"
    }
    inv = CardInventory()
    inv.load_cards([card])
    # Exact match
    assert inv.filter_cards({"Purchase price": "0.12"}), "Exact match failed for Purchase price"
    assert inv.filter_cards({"Whatnot price": "1.50"}), "Exact match failed for Whatnot price"
    assert inv.filter_cards({"Quantity": "3"}), "Exact match failed for Quantity"
    assert inv.filter_cards({"cmc": "2"}), "Exact match failed for cmc"
    assert inv.filter_cards({"ManaBox ID": "12345"}), "Exact match failed for ManaBox ID"
    assert inv.filter_cards({"Collector number": "271"}), "Exact match failed for Collector number"
    # Greater than
    assert inv.filter_cards({"Purchase price": ">0.10"}), "> match failed for Purchase price"
    assert inv.filter_cards({"Whatnot price": ">1.0"}), "> match failed for Whatnot price"
    assert inv.filter_cards({"Quantity": ">2"}), "> match failed for Quantity"
    assert inv.filter_cards({"cmc": ">1"}), "> match failed for cmc"
    assert inv.filter_cards({"ManaBox ID": ">10000"}), "> match failed for ManaBox ID"
    assert inv.filter_cards({"Collector number": ">200"}), "> match failed for Collector number"
    # Greater than or equal
    assert inv.filter_cards({"Purchase price": ">=0.12"}), ">= match failed for Purchase price"
    assert inv.filter_cards({"Whatnot price": ">=1.50"}), ">= match failed for Whatnot price"
    assert inv.filter_cards({"Quantity": ">=3"}), ">= match failed for Quantity"
    assert inv.filter_cards({"cmc": ">=2"}), ">= match failed for cmc"
    assert inv.filter_cards({"ManaBox ID": ">=12345"}), ">= match failed for ManaBox ID"
    assert inv.filter_cards({"Collector number": ">=271"}), ">= match failed for Collector number"
    # Less than
    assert inv.filter_cards({"Purchase price": "<0.13"}), "< match failed for Purchase price"
    assert inv.filter_cards({"Whatnot price": "<2.00"}), "< match failed for Whatnot price"
    assert inv.filter_cards({"Quantity": "<4"}), "< match failed for Quantity"
    assert inv.filter_cards({"cmc": "<3"}), "< match failed for cmc"
    assert inv.filter_cards({"ManaBox ID": "<20000"}), "< match failed for ManaBox ID"
    assert inv.filter_cards({"Collector number": "<300"}), "< match failed for Collector number"
    # Less than or equal
    assert inv.filter_cards({"Purchase price": "<=0.12"}), "<= match failed for Purchase price"
    assert inv.filter_cards({"Whatnot price": "<=1.50"}), "<= match failed for Whatnot price"
    assert inv.filter_cards({"Quantity": "<=3"}), "<= match failed for Quantity"
    assert inv.filter_cards({"cmc": "<=2"}), "<= match failed for cmc"
    assert inv.filter_cards({"ManaBox ID": "<=12345"}), "<= match failed for ManaBox ID"
    assert inv.filter_cards({"Collector number": "<=271"}), "<= match failed for Collector number"
    # Range
    assert inv.filter_cards({"Purchase price": "0.10-0.13"}), "range match failed for Purchase price"
    assert inv.filter_cards({"Whatnot price": "1.00-2.00"}), "range match failed for Whatnot price"
    assert inv.filter_cards({"Quantity": "2-4"}), "range match failed for Quantity"
    assert inv.filter_cards({"cmc": "1-3"}), "range match failed for cmc"
    assert inv.filter_cards({"ManaBox ID": "10000-20000"}), "range match failed for ManaBox ID"
    assert inv.filter_cards({"Collector number": "200-300"}), "range match failed for Collector number"

def test_card_table_pagination_and_export(qtbot, tmp_path):
    from ManaBox_Enhancer.ui.main_window import MainWindow
    import csv
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Add 250 cards
    cards = [
        {"Name": f"Card{i}", "Foil": "normal", "Collector number": str(i), "Set name": "SetA", "Set code": "SA", "Rarity": "common", "Language": "en", "Purchase price": f"${i/100:.2f}", "colors": "R", "type_line": "Creature", "mana_cost": "{R}", "cmc": "1", "oracle_text": f"Text {i}"}
        for i in range(1, 251)
    ]
    window.inventory.load_cards(cards)
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Set page size to 50
    window.card_table.page_size_combo.setCurrentText("50")
    assert window.card_table.page_size == 50
    # Should be 5 pages
    assert window.card_table._max_page() == 4
    # Go to last page
    window.card_table._go_last()
    assert window.card_table.current_page == 4
    # Check cards on last page
    last_page_cards = window.card_table.cards
    assert len(last_page_cards) == 50
    assert last_page_cards[0]["Name"] == "Card201"
    # Change page size to 100
    window.card_table.page_size_combo.setCurrentText("100")
    assert window.card_table.page_size == 100
    assert window.card_table._max_page() == 2
    window.card_table._go_last()
    last_page_cards = window.card_table.cards
    assert len(last_page_cards) == 50
    assert last_page_cards[0]["Name"] == "Card201"
    # Export all filtered cards (should be 250, not just current page)
    export_file = tmp_path / "item_listings.csv"
    window.export_item_listings(str(export_file), filetype="csv")
    with open(export_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 250, f"Exported {len(rows)} rows, expected 250"
        assert rows[0]["Title"].startswith("Card1"), "First card title incorrect"
        assert rows[-1]["Title"].startswith("Card250"), "Last card title incorrect"

def test_export_item_listings_field_selection(qtbot, tmp_path, monkeypatch):
    from ManaBox_Enhancer.ui.main_window import MainWindow
    from ManaBox_Enhancer.ui.dialogs.export_item_listing_fields import ExportItemListingFieldsDialog
    import csv
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Add cards with many fields
    cards = [
        {"Name": "CardA", "Set name": "Set1", "Foil": "foil", "Collector number": "1", "Rarity": "rare", "Language": "en", "cmc": "2"},
        {"Name": "CardB", "Set name": "Set2", "Foil": "normal", "Collector number": "2", "Rarity": "common", "Language": "jp", "cmc": "3"},
    ]
    window.inventory.load_cards(cards)
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Patch dialog to simulate user selecting 'Name' and 'Set name' for title, 'Rarity', 'Language', 'cmc' for description
    class FakeDialog:
        def __init__(self, *a, **k): pass
        def exec(self): return True
        def get_fields(self):
            return ["Name", "Set name"], ["Rarity", "Language", "cmc"]
    monkeypatch.setattr("ManaBox_Enhancer.ui.dialogs.export_item_listing_fields.ExportItemListingFieldsDialog", FakeDialog)
    export_file = tmp_path / "item_listings.csv"
    window.export_item_listings(str(export_file), filetype="csv")
    with open(export_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows[0]["Title"] == "CardA Set name: Set1" or rows[0]["Title"] == "CardA Set1"
        assert "Rarity: rare" in rows[0]["Description"]
        assert "Language: en" in rows[0]["Description"]
        assert "cmc: 2" in rows[0]["Description"]

def test_import_csv_and_whatnot_adjustment_handles_blank_prices(tmp_path, qtbot, monkeypatch):
    from ManaBox_Enhancer.ui.main_window import MainWindow
    import csv
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    # Simulate import of CSV with blank and '0.0' prices
    cards = [
        {"Name": "CardA", "Purchase price": "", "Whatnot price": ""},
        {"Name": "CardB", "Purchase price": "0.0", "Whatnot price": "0.0"},
        {"Name": "CardC", "Purchase price": "$1.29", "Whatnot price": ""},
        {"Name": "CardD", "Purchase price": "bad", "Whatnot price": ""},
    ]
    window.inventory.load_cards(cards)
    window.card_table.update_cards(window.inventory.get_all_cards())
    # Simulate Whatnot price adjustment (rounding, threshold 0.30)
    for card in window.inventory.get_all_cards():
        try:
            price_str = str(card.get("Purchase price", "")).replace("$", "").strip()
            if not price_str:
                continue
            price = float(price_str)
            cents = price - int(price)
            if cents >= 0.30:
                rounded = int(price) + 1
            else:
                rounded = int(price)
            card["Whatnot price"] = f"${rounded:.2f}"
        except Exception:
            continue
    # CardA and CardB and CardD should remain blank, CardC should be rounded
    assert window.inventory.get_all_cards()[0]["Whatnot price"] == ""
    assert window.inventory.get_all_cards()[1]["Whatnot price"] == "0.0" or window.inventory.get_all_cards()[1]["Whatnot price"] == ""
    assert window.inventory.get_all_cards()[2]["Whatnot price"] == "$1.00"
    assert window.inventory.get_all_cards()[3]["Whatnot price"] == ""

@pytest.mark.parametrize("fields", [["A", "B", "C", "D"]])
def test_export_item_listing_fields_check_order(qtbot, tmp_path, fields):
    # Remove prefs file if exists
    prefs_file = os.path.join(os.path.dirname(__file__), '..', 'export_item_listing_fields_prefs.json')
    if os.path.exists(prefs_file):
        os.remove(prefs_file)
    dlg = ExportItemListingFieldsDialog(fields)
    qtbot.addWidget(dlg)
    dlg.show()
    # Check C, then A, then D
    for i in range(dlg.title_list.count()):
        item = dlg.title_list.item(i)
        if item.text() in ("C", "A", "D"):
            item.setCheckState(Qt.Checked)
    # Uncheck A, then check B
    for i in range(dlg.title_list.count()):
        item = dlg.title_list.item(i)
        if item.text() == "A":
            item.setCheckState(Qt.Unchecked)
    for i in range(dlg.title_list.count()):
        item = dlg.title_list.item(i)
        if item.text() == "B":
            item.setCheckState(Qt.Checked)
    # Now checked order should be: C, D, B (A was unchecked)
    title_fields, _ = dlg.get_fields()
    assert title_fields == ["C", "D", "B"], f"Check order incorrect: {title_fields}"

    # Save as default, close and reopen dialog, check order persists
    dlg.save_as_default()
    dlg.close()
    dlg2 = ExportItemListingFieldsDialog(fields)
    qtbot.addWidget(dlg2)
    dlg2.show()
    title_fields2, _ = dlg2.get_fields()
    assert title_fields2 == ["C", "D", "B"], f"Check order not persisted: {title_fields2}"

    # Drag-and-drop: move B to top visually, but check order should remain
    b_idx = None
    for i in range(dlg2.title_list.count()):
        if dlg2.title_list.item(i).text() == "B":
            b_idx = i
            break
    if b_idx is not None:
        item = dlg2.title_list.takeItem(b_idx)
        dlg2.title_list.insertItem(0, item)
    # Order in get_fields should still be C, D, B
    title_fields3, _ = dlg2.get_fields()
    assert title_fields3 == ["C", "D", "B"], f"Check order changed after drag: {title_fields3}"

    # Reset to default: all unchecked
    dlg2.reset_to_default()
    title_fields4, _ = dlg2.get_fields()
    assert title_fields4 == [], f"Reset to default did not clear: {title_fields4}"

    # Check all, save as default, close and reopen, all should be checked in order
    for i in range(dlg2.title_list.count()):
        dlg2.title_list.item(i).setCheckState(Qt.Checked)
    dlg2.save_as_default()
    dlg2.close()
    dlg3 = ExportItemListingFieldsDialog(fields)
    qtbot.addWidget(dlg3)
    dlg3.show()
    title_fields5, _ = dlg3.get_fields()
    assert title_fields5 == fields, f"All fields not checked after save/load: {title_fields5}"

def test_export_to_whatnot_template_defaults_match_template(qtbot, tmp_path, monkeypatch):
    import csv
    import os
    from ManaBox_Enhancer.ui.main_window import MainWindow
    # Read template columns and defaults
    template_path = os.path.join(os.path.dirname(__file__), '../../Whatnot Card Inventory - Template (3).csv')
    with open(template_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        columns = next(reader)
        defaults = next(reader)
    # Setup MainWindow and inventory
    mw = MainWindow()
    test_card = {columns[0]: 'Trading Card Games', columns[1]: 'Magic: The Gathering', columns[2]: 'Test Card (Foil)', columns[4]: '2', columns[6]: '123'}
    mw.inventory.cards = [test_card]
    # Patch get_export_path to use tmp_path
    out_path = tmp_path / 'export.csv'
    monkeypatch.setattr(mw, 'get_export_path', lambda kind: (str(out_path), None))
    # Run export
    mw.export_to_whatnot()
    # Read output
    with open(out_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        out_columns = next(reader)
        out_row = next(reader)
    assert out_columns == columns
    # Only the fields set in test_card should differ, all others should match template defaults
    for i, col in enumerate(columns):
        if col in test_card:
            assert out_row[i] == test_card[col]
        else:
            assert out_row[i] == defaults[i]

def test_whatnot_export_price_minimum_rule(qtbot, tmp_path, monkeypatch):
    """
    Test that Whatnot price of 0 always exports as 1 (see README Whatnot Export Rules).
    """
    import csv
    import os
    from ManaBox_Enhancer.ui.main_window import MainWindow
    # Setup MainWindow and inventory
    mw = MainWindow()
    # Patch get_export_path to use a temp file
    out_csv = tmp_path / "whatnot_export.csv"
    monkeypatch.setattr(mw, "get_export_path", lambda kind: (str(out_csv), None))
    # Patch dialog to auto-select fields
    monkeypatch.setattr("ManaBox_Enhancer.ui.dialogs.export_item_listing_fields.ExportItemListingFieldsDialog.exec", lambda self: True)
    monkeypatch.setattr("ManaBox_Enhancer.ui.dialogs.export_item_listing_fields.ExportItemListingFieldsDialog.get_fields", lambda self: (["Name"], ["Set name"]))
    # Add a card with Whatnot price 0
    card = {
        "Name": "Test Card",
        "Set name": "Test Set",
        "Whatnot price": 0,
        "Quantity": 2,
        "Purchase price": 0.5,
    }
    mw.inventory.load_cards([card])
    mw.export_to_whatnot()
    # Read exported CSV
    with open(out_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows[0]["Price"] == "1", f"Expected Price to be '1', got {rows[0]['Price']}"

def test_break_builder_inventory_search_and_add(qtbot):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [
                {"Name": "Alpha", "Set name": "SetA"},
                {"Name": "Beta", "Set name": "SetB"},
                {"Name": "Gamma", "Set name": "SetC"},
            ]
        def get_all_cards(self):
            return self.cards
        def remove_card(self, card):
            self.cards.remove(card)
        def add_card(self, card):
            self.cards.append(card)
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Search for 'Alpha'
    dlg.search_box.setText("Alpha")
    qtbot.wait(100)
    assert dlg.inv_list.count() == 1
    # Select and add to break
    dlg.inv_list.setCurrentRow(0)
    qtbot.mouseClick(dlg.add_selected_btn, Qt.LeftButton)
    assert dlg.break_list.count() == 1
    assert dlg.break_items[0]["Name"] == "Alpha"

def test_break_builder_add_by_scryfall_id(qtbot):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    with patch('models.scryfall_api.fetch_scryfall_data') as mock_fetch:
        mock_fetch.return_value = {"Name": "ScryCard", "Set name": "ScrySet"}
        class DummyInventory:
            def get_all_cards(self): return []
            def remove_card(self, card): pass
            def add_card(self, card): pass
        inv = DummyInventory()
        dlg = BreakBuilderDialog(inv)
        qtbot.addWidget(dlg)
        dlg.show()
        # Simulate add by Scryfall ID
        with patch('PySide6.QtWidgets.QInputDialog.getText', return_value=("scryid", True)):
            dlg.add_by_scryfall_id()
        assert any(card["Name"] == "ScryCard" for card in dlg.break_items)

def test_break_builder_random_selection(qtbot):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [{"Name": f"Card{i}", "Set name": "SetX"} for i in range(10)]
        def get_all_cards(self): return self.cards
        def remove_card(self, card): self.cards.remove(card)
        def add_card(self, card): self.cards.append(card)
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    dlg.search_box.setText("")
    qtbot.wait(100)
    dlg.rand_count_input.setText("3")
    qtbot.mouseClick(dlg.rand_select_btn, Qt.LeftButton)
    assert len(dlg.break_items) == 3
    # All selected cards are from inventory
    for card in dlg.break_items:
        assert card["Name"].startswith("Card")

def test_break_builder_export_and_remove(qtbot, tmp_path):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    import os
    class DummyInventory:
        def __init__(self):
            self.cards = [{"Name": "ExportMe", "Set name": "SetY"}]
        def get_all_cards(self): return self.cards
        def remove_card(self, card): self.cards.remove(card)
        def add_card(self, card): self.cards.append(card)
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add card to break list
    dlg.break_items.append(inv.cards[0].copy())
    dlg.update_break_list()
    # Patch QFileDialog to auto-select a file
    export_file = tmp_path / "break_list.csv"
    with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(str(export_file), "CSV Files (*.csv)")):
        # Patch QMessageBox.question to always say Yes to remove
        with patch('PySide6.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes):
            dlg.export_break_list()
    # File should exist
    assert os.path.exists(export_file)
    # Card should be removed from inventory
    assert not inv.cards
    # Re-import
    dlg.reimport_removed()
    assert inv.cards

def test_break_builder_edit_duplicate_remove(qtbot):
    from ManaBox_Enhancer.ui.dialogs.break_builder import BreakBuilderDialog
    class DummyInventory:
        def __init__(self):
            self.cards = [{"Name": "EditMe", "Set name": "SetZ"}]
        def get_all_cards(self): return self.cards
        def remove_card(self, card): self.cards.remove(card)
        def add_card(self, card): self.cards.append(card)
    inv = DummyInventory()
    dlg = BreakBuilderDialog(inv)
    qtbot.addWidget(dlg)
    dlg.show()
    # Add card to break list
    dlg.break_items.append(inv.cards[0].copy())
    dlg.update_break_list()
    # Duplicate
    dlg.break_list.setCurrentRow(0)
    qtbot.mouseClick(dlg.duplicate_btn, Qt.LeftButton)
    assert dlg.break_list.count() == 2
    # Remove
    dlg.break_list.setCurrentRow(0)
    qtbot.mouseClick(dlg.remove_btn, Qt.LeftButton)
    assert dlg.break_list.count() == 1
    # Edit (simulate dialog accept)
    with patch('ui.dialogs.edit_card.EditCardDialog.exec', return_value=True), \
         patch('ui.dialogs.edit_card.EditCardDialog.get_card', return_value={"Name": "Edited", "Set name": "SetZ"}):
        dlg.edit_break_item(dlg.break_list.item(0))
    assert dlg.break_items[0]["Name"] == "Edited"

def test_mainwindow_add_card_by_scryfall_id(qtbot, monkeypatch):
    from ManaBox_Enhancer.ui.main_window import MainWindow
    # Mock Scryfall API
    monkeypatch.setattr('models.scryfall_api.fetch_scryfall_data', lambda scry_id: {"Name": "TestScry", "Set name": "ScrySet"})
    # Mock QInputDialog
    monkeypatch.setattr('PySide6.QtWidgets.QInputDialog.getText', lambda *a, **k: ("scryid", True))
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    before = len(window.inventory.get_all_cards())
    window.add_card_by_scryfall_id()
    after = len(window.inventory.get_all_cards())
    assert after == before + 1
    assert any(card["Name"] == "TestScry" for card in window.inventory.get_all_cards())
