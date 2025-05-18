from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
    QFileDialog, QLineEdit, QLabel, QProgressBar, QMessageBox,
    QMenu, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from ui.models.inventory_model import InventoryModel
from core.workers import InventoryLoadWorker
import os

class CollectionTab(QWidget):
    def __init__(self, inventory_manager):
        super().__init__()
        self.inventory_manager = inventory_manager
        self.setup_ui()
        self.setup_connections()
        self.setup_context_menu()
        
    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search inventory...")
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)
        
        # Table
        self.table = QTableView()
        self.model = InventoryModel([])
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.layout.addWidget(self.table)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import Inventory")
        self.export_btn = QPushButton("Export Inventory")
        self.refresh_btn = QPushButton("Refresh")
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.refresh_btn)
        self.layout.addLayout(button_layout)
        
    def setup_connections(self):
        self.import_btn.clicked.connect(self.import_inventory)
        self.export_btn.clicked.connect(self.export_inventory)
        self.refresh_btn.clicked.connect(self.refresh_inventory)
        self.search_input.textChanged.connect(self.filter_inventory)
        self.inventory_manager.inventory_updated.connect(self.update_table)
        
    def setup_context_menu(self):
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
    def import_inventory(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV", "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if file_path:
            self.progress_bar.setVisible(True)
            self.import_btn.setEnabled(False)
            
            self.worker = InventoryLoadWorker(self.inventory_manager, file_path)
            self.worker.progress.connect(self.update_progress)
            self.worker.finished.connect(self.import_finished)
            self.worker.error.connect(self.import_error)
            self.worker.start()
            
    def update_progress(self, message: str):
        self.progress_bar.setFormat(message)
        
    def import_finished(self):
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        self.update_table()
        
    def import_error(self, error: str):
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        QMessageBox.critical(self, "Import Error", str(error))
        
    def export_inventory(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if file_path:
            try:
                self.inventory_manager.save_inventory(file_path)
                QMessageBox.information(self, "Success", "Inventory exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))
                
    def filter_inventory(self, text: str):
        self.model.setFilter(text)
        
    def show_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.table.mapToGlobal(position))
        
        if action == edit_action:
            self.edit_selected_card()
        elif action == delete_action:
            self.delete_selected_card()
            
    def edit_selected_card(self):
        # Implement card editing
        pass
        
    def delete_selected_card(self):
        # Implement card deletion
        pass

    def update_table(self):
        self.model = InventoryModel(self.inventory_manager.inventory)
        self.table.setModel(self.model)
