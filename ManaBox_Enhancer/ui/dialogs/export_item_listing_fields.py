from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

class ExportItemListingFieldsDialog(QDialog):
    def __init__(self, all_fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Fields for Title and Description")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select and order fields for the Title:"))
        self.title_list = QListWidget()
        self.title_list.setSelectionMode(QListWidget.MultiSelection)
        for field in all_fields:
            item = QListWidgetItem(field)
            self.title_list.addItem(item)
        layout.addWidget(self.title_list)
        btns1 = QHBoxLayout()
        self.up_title = QPushButton("Up")
        self.down_title = QPushButton("Down")
        btns1.addWidget(self.up_title)
        btns1.addWidget(self.down_title)
        layout.addLayout(btns1)
        layout.addWidget(QLabel("Select and order fields for the Description:"))
        self.desc_list = QListWidget()
        self.desc_list.setSelectionMode(QListWidget.MultiSelection)
        for field in all_fields:
            item = QListWidgetItem(field)
            self.desc_list.addItem(item)
        layout.addWidget(self.desc_list)
        btns2 = QHBoxLayout()
        self.up_desc = QPushButton("Up")
        self.down_desc = QPushButton("Down")
        btns2.addWidget(self.up_desc)
        btns2.addWidget(self.down_desc)
        layout.addLayout(btns2)
        btns = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.up_title.clicked.connect(lambda: self.move_selected(self.title_list, -1))
        self.down_title.clicked.connect(lambda: self.move_selected(self.title_list, 1))
        self.up_desc.clicked.connect(lambda: self.move_selected(self.desc_list, -1))
        self.down_desc.clicked.connect(lambda: self.move_selected(self.desc_list, 1))
    def move_selected(self, list_widget, direction):
        selected = list_widget.selectedItems()
        if not selected:
            return
        row = list_widget.row(selected[0])
        if (direction == -1 and row == 0) or (direction == 1 and row == list_widget.count() - 1):
            return
        item = list_widget.takeItem(row)
        list_widget.insertItem(row + direction, item)
        item.setSelected(True)
    def get_fields(self):
        title_fields = [self.title_list.item(i).text() for i in range(self.title_list.count()) if self.title_list.item(i).isSelected()]
        desc_fields = [self.desc_list.item(i).text() for i in range(self.desc_list.count()) if self.desc_list.item(i).isSelected()]
        return title_fields, desc_fields 