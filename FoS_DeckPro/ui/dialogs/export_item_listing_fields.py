from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
import os
import json

PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'export_item_listing_fields_prefs.json')

class ExportItemListingFieldsDialog(QDialog):
    def __init__(self, all_fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Fields for Title and Description")
        self.resize(600, 400)
        self.all_fields = all_fields
        self.prefs = self.load_prefs()
        # Track check order as {field: order_index}
        self.title_check_order = {}
        self.desc_check_order = {}
        self._check_counter = 0
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select and order fields for the Title (checked = included, drag to reorder):"))
        self.title_list = QListWidget()
        self.title_list.setSelectionMode(QListWidget.SingleSelection)
        self.title_list.setDragDropMode(QListWidget.InternalMove)
        self.populate_list(self.title_list, 'title')
        self.title_list.itemChanged.connect(lambda item: self.handle_check(item, 'title'))
        layout.addWidget(self.title_list)
        layout.addWidget(QLabel("Select and order fields for the Description (checked = included, drag to reorder):"))
        self.desc_list = QListWidget()
        self.desc_list.setSelectionMode(QListWidget.SingleSelection)
        self.desc_list.setDragDropMode(QListWidget.InternalMove)
        self.populate_list(self.desc_list, 'desc')
        self.desc_list.itemChanged.connect(lambda item: self.handle_check(item, 'desc'))
        layout.addWidget(self.desc_list)
        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.save_default_btn = QPushButton("Save as default")
        self.reset_default_btn = QPushButton("Reset to default")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.save_default_btn)
        btns.addWidget(self.reset_default_btn)
        layout.addLayout(btns)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.save_default_btn.clicked.connect(self.save_as_default)
        self.reset_default_btn.clicked.connect(self.reset_to_default)

    def populate_list(self, list_widget, key):
        # key: 'title' or 'desc'
        selected = self.prefs.get(f'selected_{key}', [])
        order = self.prefs.get(f'order_{key}', self.all_fields)
        check_order = self.prefs.get(f'check_order_{key}', {})
        # Ensure all fields are present
        ordered_fields = [f for f in order if f in self.all_fields] + [f for f in self.all_fields if f not in order]
        for field in ordered_fields:
            item = QListWidgetItem(field)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
            if field in selected:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            list_widget.addItem(item)
        # Restore check order
        if key == 'title':
            self.title_check_order = dict(check_order)
        else:
            self.desc_check_order = dict(check_order)
        # Set counter to max used + 1
        all_orders = list(check_order.values()) if check_order else []
        if all_orders:
            self._check_counter = max(self._check_counter, max(all_orders) + 1)

    def handle_check(self, item, key):
        field = item.text()
        if key == 'title':
            check_order = self.title_check_order
        else:
            check_order = self.desc_check_order
        if item.checkState() == Qt.Checked:
            if field not in check_order:
                check_order[field] = self._check_counter
                self._check_counter += 1
        else:
            if field in check_order:
                del check_order[field]

    def get_fields(self):
        def get_checked(list_widget, check_order):
            checked = [list_widget.item(i).text() for i in range(list_widget.count()) if list_widget.item(i).checkState() == Qt.Checked]
            # Sort by check order
            checked.sort(key=lambda f: check_order.get(f, float('inf')))
            return checked
        title_fields = get_checked(self.title_list, self.title_check_order)
        desc_fields = get_checked(self.desc_list, self.desc_check_order)
        return title_fields, desc_fields

    def save_as_default(self):
        prefs = {
            'selected_title': [self.title_list.item(i).text() for i in range(self.title_list.count()) if self.title_list.item(i).checkState() == Qt.Checked],
            'order_title': [self.title_list.item(i).text() for i in range(self.title_list.count())],
            'check_order_title': self.title_check_order,
            'selected_desc': [self.desc_list.item(i).text() for i in range(self.desc_list.count()) if self.desc_list.item(i).checkState() == Qt.Checked],
            'order_desc': [self.desc_list.item(i).text() for i in range(self.desc_list.count())],
            'check_order_desc': self.desc_check_order,
        }
        try:
            with open(PREFS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Saved", "Default fields and order saved.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save preferences: {e}")

    def reset_to_default(self):
        self.title_list.clear()
        self.desc_list.clear()
        self.title_check_order = {}
        self.desc_check_order = {}
        for field in self.all_fields:
            item1 = QListWidgetItem(field)
            item1.setFlags(item1.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
            item1.setCheckState(Qt.Unchecked)
            self.title_list.addItem(item1)
            item2 = QListWidgetItem(field)
            item2.setFlags(item2.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled)
            item2.setCheckState(Qt.Unchecked)
            self.desc_list.addItem(item2)
        self._check_counter = 0

    def load_prefs(self):
        if os.path.exists(PREFS_FILE):
            try:
                with open(PREFS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {} 