import sys
import json
import re
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QTextEdit, 
                               QMessageBox, QFormLayout, QDialog, QLabel, QComboBox, QSpinBox, 
                               QDoubleSpinBox, QWebEngineView, QCheckBox, QFileDialog, QGroupBox, 
                               QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from datetime import datetime

# Existing Dialog Classes (unchanged from your provided script)
class FieldDialog(QDialog):
    def __init__(self, category, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add Custom Field to {category}")
        self.layout = QFormLayout()
        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["string", "integer", "float", "boolean"])
        self.desc_input = QTextEdit()
        self.layout.addRow("Field Name:", self.name_input)
        self.layout.addRow("Field Type:", self.type_input)
        self.layout.addRow("Description:", self.desc_input)
        self.submit_button = QPushButton("Add Field")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "type": self.type_input.currentText(),
            "description": self.desc_input.toPlainText()
        }

class ItemDialog(QDialog):
    def __init__(self, category, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add New {category}")
        self.layout = QFormLayout()
        self.fields = {}
        for field in fields:
            if field["type"] == "string":
                self.fields[field["name"]] = QLineEdit()
            elif field["type"] == "integer":
                self.fields[field["name"]] = QSpinBox()
            elif field["type"] == "float":
                self.fields[field["name"]] = QDoubleSpinBox()
            elif field["type"] == "boolean":
                self.fields[field["name"]] = QComboBox()
                self.fields[field["name"]].addItems(["True", "False"])
            self.layout.addRow(f"{field['name']}:", self.fields[field["name"]])
        self.submit_button = QPushButton("Add")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def get_data(self):
        return {key: (widget.value() if isinstance(widget, (QSpinBox, QDoubleSpinBox)) 
                      else widget.currentText() if isinstance(widget, QComboBox) 
                      else widget.text()) for key, widget in self.fields.items()}

class MediaDialog(QDialog):
    def __init__(self, current_media=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Media")
        self.layout = QVBoxLayout()
        self.media_list = current_media or []
        self.media_display = QTextEdit()
        self.media_display.setReadOnly(True)
        self.media_display.setText("\n".join(self.media_list))
        self.layout.addWidget(QLabel("Current Media:"))
        self.layout.addWidget(self.media_display)
        self.add_media_button = QPushButton("Add Image/Video")
        self.add_media_button.clicked.connect(self.add_media)
        self.layout.addWidget(self.add_media_button)
        self.submit_button = QPushButton("Save Media")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def add_media(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Media", "", "Images (*.png *.jpg);;Videos (*.mp4)")
        if file_path:
            self.media_list.append(file_path)
            self.media_display.setText("\n".join(self.media_list))
    
    def get_data(self):
        return self.media_list

class BuffDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Buff")
        self.layout = QFormLayout()
        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.effect_type = QComboBox()
        self.effect_type.addItems(["hit_modifier", "stat_boost", "dodge_chance", "damage_resistance"])
        self.effect_value = QLineEdit()
        self.applies_to = QLineEdit()
        self.duration = QComboBox()
        self.duration.addItems(["permanent", "3 rolls", "1 encounter", "1 session", "until_disabled"])
        self.media_button = QPushButton("Add Media")
        self.media_button.clicked.connect(self.add_media)
        self.media_list = []
        self.media_display = QTextEdit()
        self.media_display.setReadOnly(True)
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Description:", self.desc_input)
        self.layout.addRow("Effect Type:", self.effect_type)
        self.layout.addRow("Effect Value:", self.effect_value)
        self.layout.addRow("Applies To (event/stat):", self.applies_to)
        self.layout.addRow("Duration:", self.duration)
        self.layout.addRow("Media:", self.media_button)
        self.layout.addRow("Current Media:", self.media_display)
        self.submit_button = QPushButton("Add Buff")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def add_media(self):
        dialog = MediaDialog(self.media_list, self)
        if dialog.exec():
            self.media_list = dialog.get_data()
            self.media_display.setText("\n".join(self.media_list))
    
    def get_data(self):
        effect = {}
        effect_type = self.effect_type.currentText()
        if effect_type == "hit_modifier":
            effect["hit_modifier"] = int(self.effect_value.text()) if self.effect_value.text().isdigit() else 0
            if self.applies_to.text():
                effect["applies_to"] = self.applies_to.text()
        elif effect_type == "stat_boost":
            stat = self.applies_to.text()
            if stat in ["strength", "agility", "engineering", "intelligence", "luck"]:
                effect[stat] = int(self.effect_value.text()) if self.effect_value.text().isdigit() else 0
        elif effect_type == "dodge_chance":
            effect["dodge_chance"] = float(self.effect_value.text()) if self.effect_value.text().replace('.', '', 1).isdigit() else 0.0
        elif effect_type == "damage_resistance":
            effect["damage_resistance"] = {self.applies_to.text() or "physical": int(self.effect_value.text()) if self.effect_value.text().isdigit() else 0}
        return {
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "media": self.media_list,
            "effect": effect,
            "duration": self.duration.currentText()
        }

class SpecialEffectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Special Effect")
        self.layout = QFormLayout()
        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.probability_input = QDoubleSpinBox()
        self.probability_input.setRange(0.0, 1.0)
        self.probability_input.setSingleStep(0.05)
        self.dice_input = QLineEdit()
        self.damage_type_input = QLineEdit()
        self.media_button = QPushButton("Add Media")
        self.media_button.clicked.connect(self.add_media)
        self.media_list = []
        self.media_display = QTextEdit()
        self.media_display.setReadOnly(True)
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Description:", self.desc_input)
        self.layout.addRow("Probability (0-1):", self.probability_input)
        self.layout.addRow("Damage Dice (e.g., 1d20):", self.dice_input)
        self.layout.addRow("Damage Type:", self.damage_type_input)
        self.layout.addRow("Media:", self.media_button)
        self.layout.addRow("Current Media:", self.media_display)
        self.submit_button = QPushButton("Add Effect")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def add_media(self):
        dialog = MediaDialog(self.media_list, self)
        if dialog.exec():
            self.media_list = dialog.get_data()
            self.media_display.setText("\n".join(self.media_list))
    
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "probability": self.probability_input.value(),
            "dice": self.dice_input.text(),
            "damage_type": self.damage_type_input.text(),
            "media": self.media_list
        }

class ManualRollDialog(QDialog):
    def __init__(self, dice_notation, label="Enter Roll Result", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Manual Dice Roll: {dice_notation}")
        self.layout = QFormLayout()
        self.dice_notation = dice_notation
        self.total_input = QSpinBox()
        self.total_input.setRange(1, 1000)
        self.individual_inputs = []
        match = re.match(r"(\d+)d(\d+)", dice_notation)
        if match:
            num_dice, dice_type = map(int, match.groups())
            self.layout.addRow(f"Total Result ({dice_notation}):", self.total_input)
            for i in range(num_dice):
                input_field = QSpinBox()
                input_field.setRange(1, dice_type)
                self.individual_inputs.append(input_field)
                self.layout.addRow(f"Dice {i+1} (d{dice_type}):", input_field)
        else:
            self.layout.addRow(f"Result ({dice_notation}):", self.total_input)
        self.submit_button = QPushButton("Submit Roll")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def get_data(self):
        return {
            "total": self.total_input.value(),
            "individual": [input_field.value() for input_field in self.individual_inputs]
        }

class EnemySelectionDialog(QDialog):
    def __init__(self, enemies, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select or Create Enemy")
        self.layout = QVBoxLayout()
        self.existing_enemy = QComboBox()
        self.existing_enemy.addItems([e["name"] for e in enemies] + ["Create New Enemy"])
        self.layout.addWidget(QLabel("Select Enemy:"))
        self.layout.addWidget(self.existing_enemy)
        self.new_enemy_widget = QWidget()
        self.new_enemy_layout = QFormLayout()
        self.new_enemy_name = QLineEdit()
        self.new_enemy_desc = QTextEdit()
        self.new_enemy_stats_hp = QSpinBox()
        self.new_enemy_stats_strength = QSpinBox()
        self.new_enemy_stats_agility = QSpinBox()
        self.new_enemy_stats_engineering = QSpinBox()
        self.new_enemy_stats_intelligence = QSpinBox()
        self.new_enemy_stats_luck = QSpinBox()
        self.new_enemy_ac = QSpinBox()
        self.new_enemy_weapon = QLineEdit()
        self.new_enemy_armor = QLineEdit()
        self.new_enemy_items = QLineEdit()
        self.new_enemy_buffs = QLineEdit()
        self.new_enemy_media_button = QPushButton("Add Media")
        self.new_enemy_media_button.clicked.connect(self.add_media)
        self.new_enemy_media_list = []
        self.new_enemy_media_display = QTextEdit()
        self.new_enemy_media_display.setReadOnly(True)
        self.new_enemy_layout.addRow("Name:", self.new_enemy_name)
        self.new_enemy_layout.addRow("Description:", self.new_enemy_desc)
        self.new_enemy_layout.addRow("HP:", self.new_enemy_stats_hp)
        self.new_enemy_layout.addRow("Strength:", self.new_enemy_stats_strength)
        self.new_enemy_layout.addRow("Agility:", self.new_enemy_stats_agility)
        self.new_enemy_layout.addRow("Engineering:", self.new_enemy_stats_engineering)
        self.new_enemy_layout.addRow("Intelligence:", self.new_enemy_stats_intelligence)
        self.new_enemy_layout.addRow("Luck:", self.new_enemy_stats_luck)
        self.new_enemy_layout.addRow("AC:", self.new_enemy_ac)
        self.new_enemy_layout.addRow("Weapon ID:", self.new_enemy_weapon)
        self.new_enemy_layout.addRow("Armor ID:", self.new_enemy_armor)
        self.new_enemy_layout.addRow("Items (comma-separated IDs):", self.new_enemy_items)
        self.new_enemy_layout.addRow("Buffs (comma-separated names):", self.new_enemy_buffs)
        self.new_enemy_layout.addRow("Media:", self.new_enemy_media_button)
        self.new_enemy_layout.addRow("Current Media:", self.new_enemy_media_display)
        self.new_enemy_widget.setLayout(self.new_enemy_layout)
        self.new_enemy_widget.setVisible(False)
        self.layout.addWidget(self.new_enemy_widget)
        self.existing_enemy.currentTextChanged.connect(self.toggle_new_enemy)
        self.submit_button = QPushButton("Confirm")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def toggle_new_enemy(self, text):
        self.new_enemy_widget.setVisible(text == "Create New Enemy")
    
    def add_media(self):
        dialog = MediaDialog(self.new_enemy_media_list, self)
        if dialog.exec():
            self.new_enemy_media_list = dialog.get_data()
            self.new_enemy_media_display.setText("\n".join(self.new_enemy_media_list))
    
    def get_data(self):
        if self.existing_enemy.currentText() == "Create New Enemy":
            return {
                "create_new": True,
                "name": self.new_enemy_name.text(),
                "description": self.new_enemy_desc.toPlainText(),
                "stats": {
                    "hp": self.new_enemy_stats_hp.value(),
                    "strength": self.new_enemy_stats_strength.value(),
                    "agility": self.new_enemy_stats_agility.value(),
                    "engineering": self.new_enemy_stats_engineering.value(),
                    "intelligence": self.new_enemy_stats_intelligence.value(),
                    "luck": self.new_enemy_stats_luck.value()
                },
                "ac": self.new_enemy_ac.value(),
                "equipment": {
                    "weapon": self.new_enemy_weapon.text(),
                    "armor": self.new_enemy_armor.text(),
                    "items": [i.strip() for i in self.new_enemy_items.text().split(",") if i.strip()]
                },
                "buffs": [b.strip() for b in self.new_enemy_buffs.text().split(",") if b.strip()],
                "media": self.new_enemy_media_list
            }
        return {"create_new": False, "name": self.existing_enemy.currentText()}

class LootDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select or Create Loot")
        self.layout = QVBoxLayout()
        self.existing_items = QComboBox()
        self.existing_items.addItems([i["name"] for i in items] + ["Create New Item"])
        self.layout.addWidget(QLabel("Select Item:"))
        self.layout.addWidget(self.existing_items)
        self.new_item_widget = QWidget()
        self.new_item_layout = QFormLayout()
        self.new_item_name = QLineEdit()
        self.new_item_desc = QTextEdit()
        self.new_item_type = QLineEdit()
        self.new_item_hit_modifier = QSpinBox()
        self.new_item_media_button = QPushButton("Add Media")
        self.new_item_media_button.clicked.connect(self.add_media)
        self.new_item_media_list = []
        self.new_item_media_display = QTextEdit()
        self.new_item_media_display.setReadOnly(True)
        self.new_item_layout.addRow("Name:", self.new_item_name)
        self.new_item_layout.addRow("Description:", self.new_item_desc)
        self.new_item_layout.addRow("Type:", self.new_item_type)
        self.new_item_layout.addRow("Hit Modifier:", self.new_item_hit_modifier)
        self.new_item_layout.addRow("Media:", self.new_item_media_button)
        self.new_item_layout.addRow("Current Media:", self.new_item_media_display)
        self.new_item_widget.setLayout(self.new_item_layout)
        self.new_item_widget.setVisible(False)
        self.layout.addWidget(self.new_item_widget)
        self.existing_items.currentTextChanged.connect(self.toggle_new_item)
        self.item_list = []
        self.item_display = QTextEdit()
        self.item_display.setReadOnly(True)
        self.layout.addWidget(QLabel("Selected Items:"))
        self.layout.addWidget(self.item_display)
        self.add_item_button = QPushButton("Add Item")
        self.add_item_button.clicked.connect(self.add_item)
        self.layout.addWidget(self.add_item_button)
        self.submit_button = QPushButton("Confirm")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def toggle_new_item(self, text):
        self.new_item_widget.setVisible(text == "Create New Item")
    
    def add_media(self):
        dialog = MediaDialog(self.new_item_media_list, self)
        if dialog.exec():
            self.new_item_media_list = dialog.get_data()
            self.new_item_media_display.setText("\n".join(self.new_item_media_list))
    
    def add_item(self):
        if self.existing_items.currentText() == "Create New Item":
            item = {
                "name": self.new_item_name.text(),
                "description": self.new_item_desc.toPlainText(),
                "type": self.new_item_type.text(),
                "hit_modifier": self.new_item_hit_modifier.value(),
                "media": self.new_item_media_list
            }
            self.item_list.append(item)
        else:
            self.item_list.append({"name": self.existing_items.currentText()})
        self.item_display.setText("\n".join([i["name"] for i in self.item_list]))
        self.new_item_name.clear()
        self.new_item_desc.clear()
        self.new_item_type.clear()
        self.new_item_hit_modifier.setValue(0)
        self.new_item_media_list = []
        self.new_item_media_display.clear()
        self.existing_items.setCurrentIndex(0)
    
    def get_data(self):
        return self.item_list

class NotesDialog(QDialog):
    def __init__(self, entity_type, entity_id, current_notes="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Notes for {entity_type.capitalize()} {entity_id}")
        self.layout = QVBoxLayout()
        self.notes_input = QTextEdit()
        self.notes_input.setText(current_notes)
        self.layout.addWidget(QLabel("Notes:"))
        self.layout.addWidget(self.notes_input)
        self.submit_button = QPushButton("Save Notes")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def get_data(self):
        return self.notes_input.toPlainText()

class EventRollDialog(QDialog):
    def __init__(self, players, enemies, events, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Roll for Special Event")
        self.layout = QVBoxLayout()
        self.entity_select = QComboBox()
        self.entity_select.addItems([p["name"] for p in players])
        self.event_select = QComboBox()
        self.event_select.addItems([e["name"] for e in events] + ["Custom Event"])
        self.guardian_group = QGroupBox("Guardian Enemy")
        self.guardian_layout = QVBoxLayout()
        self.guardian_check = QCheckBox("Include Guardian Enemy")
        self.guardian_select = EnemySelectionDialog(enemies, self)
        self.guardian_type = QComboBox()
        self.guardian_type.addItems(["battle", "puzzle"])
        self.guardian_layout.addWidget(self.guardian_check)
        self.guardian_layout.addWidget(QLabel("Guardian Type:"))
        self.guardian_layout.addWidget(self.guardian_type)
        self.guardian_group.setLayout(self.guardian_layout)
        self.guardian_group.setVisible(False)
        self.dice_input = QLineEdit()
        self.dice_input.setPlaceholderText("e.g., 1d20")
        self.threshold_input = QSpinBox()
        self.threshold_input.setRange(1, 100)
        self.puzzle_type = QComboBox()
        self.puzzle_type.addItems(["stat-based", "custom", "word", "coded_terminal", "logic"])
        self.puzzle_content = QLineEdit()
        self.puzzle_content_image_button = QPushButton("Upload Puzzle Image")
        self.puzzle_content_image_button.clicked.connect(self.upload_puzzle_image)
        self.puzzle_content_image = ""
        self.puzzle_answer = QLineEdit()
        self.puzzle_solved = QCheckBox("Mark Puzzle as Solved")
        self.notes_input = QTextEdit()
        self.loot_group = QGroupBox("Loot")
        self.loot_layout = QVBoxLayout()
        self.loot_button = QPushButton("Select Loot")
        self.loot_button.clicked.connect(self.select_loot)
        self.loot_display = QTextEdit()
        self.loot_display.setReadOnly(True)
        self.loot_layout.addWidget(self.loot_button)
        self.loot_layout.addWidget(self.loot_display)
        self.loot_group.setLayout(self.loot_layout)
        self.manual_roll_checkbox = QCheckBox("Manual Roll (Enter dice.bee.ac result)")
        self.buff_checkboxes = []
        self.loot_items = []
        self.form_layout = QFormLayout()
        self.form_layout.addRow("Player:", self.entity_select)
        self.form_layout.addRow("Event:", self.event_select)
        self.form_layout.addRow("Dice:", self.dice_input)
        self.form_layout.addRow("Success Threshold:", self.threshold_input)
        self.form_layout.addRow("Puzzle Type:", self.puzzle_type)
        self.form_layout.addRow("Puzzle Content (Text):", self.puzzle_content)
        self.form_layout.addRow("Puzzle Content (Image):", self.puzzle_content_image_button)
        self.form_layout.addRow("Player Answer:", self.puzzle_answer)
        self.form_layout.addRow("Puzzle Solved:", self.puzzle_solved)
        self.form_layout.addRow("Notes:", self.notes_input)
        self.form_layout.addRow("Manual Roll:", self.manual_roll_checksum)
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.guardian_group)
        self.layout.addWidget(self.loot_group)
        self.buff_label = QLabel("Select Buffs:")
        self.layout.addWidget(self.buff_label)
        self.buff_container = QWidget()
        self.buff_layout = QVBoxLayout()
        self.buff_container.setLayout(self.buff_layout)
        self.layout.addWidget(self.buff_container)
        self.submit_button = QPushButton("Roll")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
        self.entity_select.currentTextChanged.connect(self.update_buffs)
        self.event_select.currentTextChanged.connect(self.update_event_fields)
        self.guardian_check.stateChanged.connect(self.toggle_guardian)
        self.update_buffs(players[0]["name"] if players else "")
    
    def toggle_guardian(self, state):
        self.guardian_group.setVisible(state)
    
    def select_loot(self):
        dialog = LootDialog(self.parent().data.get("items", []), self)
        if dialog.exec():
            self.loot_items = dialog.get_data()
            self.loot_display.setText("\n".join([i["name"] for i in self.loot_items]))
    
    def upload_puzzle_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Puzzle Image", "", "Images (*.png *.jpg)")
        if file_path:
            self.puzzle_content_image = file_path
    
    def update_buffs(self, entity_name):
        for checkbox in self.buff_checkboxes:
            self.buff_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.buff_checkboxes = []
        entity = next((p for p in self.parent().data["players"] if p["name"] == entity_name), None)
        if entity:
            weapon_id = entity.get("equipment", {}).get("weapon")
            weapon = next((w for w in self.parent().data["weapons"] if w["id"] == weapon_id), {}) if weapon_id else {}
            for buff in entity.get("buffs", []) + weapon.get("buffs", []):
                checkbox = QCheckBox(buff["name"])
                self.buff_checkboxes.append(checkbox)
                self.buff_layout.addWidget(checkbox)
    
    def update_event_fields(self, event_name):
        self.guardian_group.setVisible(event_name != "Custom Event")
        if event_name == "Custom Event":
            self.dice_input.setEnabled(True)
            self.threshold_input.setEnabled(True)
            self.puzzle_type.setEnabled(True)
            self.puzzle_content.setEnabled(True)
            self.puzzle_content_image_button.setEnabled(True)
            self.loot_group.setVisible(True)
        else:
            event = next((e for e in self.parent().data["events"] if e["name"] == event_name), None)
            if event:
                self.dice_input.setText(event["dice"])
                self.dice_input.setEnabled(False)
                self.threshold_input.setValue(event["success_threshold"])
                self.threshold_input.setEnabled(False)
                self.puzzle_type.setCurrentText(event.get("puzzle_type", "stat-based"))
                self.puzzle_type.setEnabled(False)
                self.puzzle_content.setText(event.get("puzzle_content", {}).get("value", "") if event.get("puzzle_content", {}).get("type") == "text" else "")
                self.puzzle_content.setEnabled(False)
                self.puzzle_content_image = event.get("puzzle_content", {}).get("value", "") if event.get("puzzle_content", {}).get("type") == "image" else ""
                self.puzzle_content_image_button.setEnabled(False)
                self.loot_items = [{"name": i} for i in event.get("loot", [])]
                self.loot_display.setText("\n".join([i["name"] for i in self.loot_items]))
                self.loot_group.setVisible(False)
    
    def get_data(self):
        puzzle_content = {"type": "image" if self.puzzle_content_image else "text", 
                         "value": self.puzzle_content_image or self.puzzle_content.text()}
        return {
            "entity_name": self.entity_select.currentText(),
            "event_name": self.event_select.currentText(),
            "guardian": self.guardian_select.get_data() if self.guardian_check.isChecked() else None,
            "guardian_type": self.guardian_type.currentText() if self.guardian_check.isChecked() else None,
            "dice": self.dice_input.text(),
            "success_threshold": self.threshold_input.value(),
            "puzzle_type": self.puzzle_type.currentText(),
            "puzzle_content": puzzle_content,
            "puzzle_answer": self.puzzle_answer.text(),
            "puzzle_solved": self.puzzle_solved.isChecked(),
            "notes": self.notes_input.toPlainText(),
            "loot": self.loot_items,
            "manual_roll": self.manual_roll_checkbox.isChecked(),
            "buffs": [cb.text() for cb in self.buff_checkboxes if cb.isChecked()]
        }

class SubLocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Sub-Location")
        self.layout = QFormLayout()
        self.name_input = QLineEdit()
        self.desc_input = QTextEdit()
        self.events_input = QLineEdit()
        self.enemies_input = QLineEdit()
        self.items_input = QLineEdit()
        self.radiation_input = QSpinBox()
        self.radiation_input.setRange(0, 100)
        self.media_button = QPushButton("Add Media")
        self.media_button.clicked.connect(self.add_media)
        self.media_list = []
        self.media_display = QTextEdit()
        self.media_display.setReadOnly(True)
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Description:", self.desc_input)
        self.layout.addRow("Events (comma-separated IDs):", self.events_input)
        self.layout.addRow("Enemies (comma-separated IDs):", self.enemies_input)
        self.layout.addRow("Items (comma-separated IDs):", self.items_input)
        self.layout.addRow("Radiation Level:", self.radiation_input)
        self.layout.addRow("Media:", self.media_button)
        self.layout.addRow("Current Media:", self.media_display)
        self.submit_button = QPushButton("Add")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    
    def add_media(self):
        dialog = MediaDialog(self.media_list, self)
        if dialog.exec():
            self.media_list = dialog.get_data()
            self.media_display.setText("\n".join(self.media_list))
    
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "events": [e.strip() for e in self.events_input.text().split(",") if e.strip()],
            "enemies": [e.strip() for e in self.enemies_input.text().split(",") if e.strip()],
            "items": [i.strip() for i in self.items_input.text().split(",") if i.strip()],
            "environmental_effects": {"radiation": {"damage": self.radiation_input.value(), "scale_stat": "intelligence", "scale_factor": 0.5}},
            "media": self.media_list
        }

class PlayerWindow(QWidget):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Player View - A Wasteland Odyssey")
        self.setGeometry(900, 100, 600, 800)
        self.data = data
        self.layout = QVBoxLayout()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout()
        self.player_group = QGroupBox("Player")
        self.player_layout = QGridLayout()
        self.player_info = QTextEdit()
        self.player_info.setReadOnly(True)
        self.player_media = QLabel()
        self.player_media.setFixedSize(100, 100)
        self.player_video = QVideoWidget()
        self.player_video.setFixedSize(200, 150)
        self.player_video.hide()
        self.player_layout.addWidget(QLabel("Info:"), 0, 0)
        self.player_layout.addWidget(self.player_info, 0, 1)
        self.player_layout.addWidget(QLabel("Media:"), 1, 0)
        self.player_layout.addWidget(self.player_media, 1, 1)
        self.player_layout.addWidget(self.player_video, 2, 1)
        self.player_group.setLayout(self.player_layout)
        self.opponent_group = QGroupBox("Opponent")
        self.opponent_layout = QGridLayout()
        self.opponent_info = QTextEdit()
        self.opponent_info.setReadOnly(True)
        self.opponent_media = QLabel()
        self.opponent_media.setFixedSize(100, 100)
        self.opponent_video = QVideoWidget()
        self.opponent_video.setFixedSize(200, 150)
        self.opponent_video.hide()
        self.opponent_layout.addWidget(QLabel("Info:"), 0, 0)
        self.opponent_layout.addWidget(self.opponent_info, 0, 1)
        self.opponent_layout.addWidget(QLabel("Media:"), 1, 0)
        self.opponent_layout.addWidget(self.opponent_media, 1, 1)
        self.opponent_layout.addWidget(self.opponent_video, 2, 1)
        self.opponent_group.setLayout(self.opponent_layout)
        self.event_group = QGroupBox("Event/Combat")
        self.event_layout = QGridLayout()
        self.event_info = QTextEdit()
        self.event_info.setReadOnly(True)
        self.event_media = QLabel()
        self.event_media.setFixedSize(100, 100)
        self.event_video = QVideoWidget()
        self.event_video.setFixedSize(200, 150)
        self.event_video.hide()
        self.event_layout.addWidget(QLabel("Outcome:"), 0, 0)
        self.event_layout.addWidget(self.event_info, 0, 1)
        self.event_layout.addWidget(QLabel("Media:"), 1, 0)
        self.event_layout.addWidget(self.event_media, 1, 1)
        self.event_layout.addWidget(self.event_video, 2, 1)
        self.event_group.setLayout(self.event_layout)
        self.location_group = QGroupBox("Location")
        self.location_layout = QGridLayout()
        self.location_info = QTextEdit()
        self.location_info.setReadOnly(True)
        self.location_media = QLabel()
        self.location_media.setFixedSize(100, 100)
        self.location_video = QVideoWidget()
        self.location_video.setFixedSize(200, 150)
        self.location_video.hide()
        self.location_layout.addWidget(QLabel("Info:"), 0, 0)
        self.location_layout.addWidget(self.location_info, 0, 1)
        self.location_layout.addWidget(QLabel("Media:"), 1, 0)
        self.location_layout.addWidget(self.location_media, 1, 1)
        self.location_layout.addWidget(self.location_video, 2, 1)
        self.location_group.setLayout(self.location_layout)
        self.dice_view = QWebEngineView()
        self.dice_view.setFixedHeight(300)
        self.content_layout.addWidget(self.player_group)
        self.content_layout.addWidget(self.opponent_group)
        self.content_layout.addWidget(self.event_group)
        self.content_layout.addWidget(self.location_group)
        self.content_layout.addWidget(QLabel("Dice Roll"))
        self.content_layout.addWidget(self.dice_view)
        self.content.setLayout(self.content_layout)
        self.scroll.setWidget(self.content)
        self.layout.addWidget(self.scroll)
        self.setLayout(self.layout)
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput([self.player_video, self.opponent_video, self.event_video, self.location_video])
        self.update_display()

    def update_display(self, roll_url=None, video_path=None):
        player = self.data.get("players", [{}])[0]
        opponent = self.data.get("enemies", [{}])[0] if self.parent().selected_target else self.data.get("players", [{}])[1] if len(self.data.get("players", [])) > 1 else {}
        logs = self.data.get("log", [])[-3:]
        current_battle = self.data.get("battles", [{}])[-1]
        event_id = current_battle.get("event_id") or "event_001"
        event = next((e for e in self.data.get("events", []) if e["id"] == event_id), {})
        location = next((loc for loc in self.data.get("locations", []) if loc["id"] == player.get("location")), {})
        sub_location = next((subloc for subloc in location.get("sub_locations", []) if subloc["id"] == player.get("sub_location")), {}) if location else {}
        
        player_weapon = next((w for w in self.data.get("weapons", []) if w["id"] == player.get("equipment", {}).get("weapon")), {})
        player_armor = next((a for a in self.data.get("armor", []) if a["id"] == player.get("equipment", {}).get("armor")), {})
        player_items = [i for i in self.data.get("items", []) if i["id"] in player.get("equipment", {}).get("items", [])]
        player_buffs = [b for b in self.data.get("buffs", []) if b["name"] in [buff["name"] for buff in player.get("buffs", []) + player_weapon.get("buffs", [])]]
        
        hit_modifier = self.parent().calculate_hit_modifier(player, player_weapon, None)
        
        player_text = (f"Name: {player.get('name', '')}\nDescription: {player.get('description', '')}\n"
                      f"HP: {player.get('stats', {}).get('hp', 0)}\nAC: {player.get('ac', 10)}\n"
                      f"Weapon: {player_weapon.get('name', 'None')} (Damage: {player_weapon.get('damage_dice', '0')})\n"
                      f"Armor: {player_armor.get('name', 'None')}\n"
                      f"Location: {location.get('name', 'Unknown')} ({sub_location.get('name', 'Unknown')})\n"
                      f"Hit Modifier: +{hit_modifier}\nBuffs: {', '.join(b['name'] for b in player_buffs)}")
        self.player_info.setText(player_text)
        player_media = player.get("media", [])
        if player_media and player_media[0].endswith((".png", ".jpg")):
            self.player_media.setPixmap(QPixmap(player_media[0]).scaled(100, 100, Qt.KeepAspectRatio))
        else:
            self.player_media.clear()
        
        opponent_weapon = next((w for w in self.data.get("weapons", []) if w["id"] == opponent.get("equipment", {}).get("weapon")), {})
        opponent_armor = next((a for a in self.data.get("armor", []) if a["id"] == opponent.get("equipment", {}).get("armor")), {})
        opponent_items = [i for i in self.data.get("items", []) if i["id"] in opponent.get("equipment", {}).get("items", [])]
        opponent_buffs = [b for b in self.data.get("buffs", []) if b["name"] in [buff["name"] for buff in opponent.get("buffs", []) + opponent_weapon.get("buffs", [])]]
        
        opponent_hit_modifier = self.parent().calculate_hit_modifier(opponent, opponent_weapon, None)
        
        opponent_text = (f"Name: {opponent.get('name', '')}\nDescription: {opponent.get('description', '')}\n"
                        f"HP: {opponent.get('stats', {}).get('hp', 0)}\nAC: {opponent.get('ac', 10)}\n"
                        f"Weapon: {opponent_weapon.get('name', 'None')} (Damage: {opponent_weapon.get('damage_dice', '0')})\n"
                        f"Armor: {opponent_armor.get('name', 'None')}\n"
                        f"Location: {location.get('name', 'Unknown')} ({sub_location.get('name', 'Unknown')})\n"
                        f"Hit Modifier: +{opponent_hit_modifier}\nBuffs: {', '.join(b['name'] for b in opponent_buffs)}")
        self.opponent_info.setText(opponent_text)
        opponent_media = opponent.get("media", [])
        if opponent_media and opponent_media[0].endswith((".png", ".jpg")):
            self.opponent_media.setPixmap(QPixmap(opponent_media[0]).scaled(100, 100, Qt.KeepAspectRatio))
        else:
            self.opponent_media.clear()
        
        event_text = "\n".join([f"{l['details']}" for l in logs]) + (f"\nEvent: {event.get('description', '')}" if event else "")
        if event.get("puzzle_content", {}).get("type") == "text":
            event_text += f"\nPuzzle: {event['puzzle_content']['value']}"
        if event.get("puzzle_resolution", {}).get("solved") is not None:
            event_text += f"\nPuzzle Outcome: {'Solved' if event['puzzle_resolution']['solved'] else 'Not Solved'}"
            if event["puzzle_resolution"].get("answer"):
                event_text += f"\nPlayer Answer: {event['puzzle_resolution']['answer']}"
        self.event_info.setText(event_text)
        event_media = event.get("media", [])
        if event.get("puzzle_content", {}).get("type") == "image" and event["puzzle_content"].get("value"):
            self.event_media.setPixmap(QPixmap(event["puzzle_content"]["value"]).scaled(100, 100, Qt.KeepAspectRatio))
        elif event_media and event_media[0].endswith((".png", ".jpg")):
            self.event_media.setPixmap(QPixmap(event_media[0]).scaled(100, 100, Qt.KeepAspectRatio))
        else:
            self.event_media.clear()
        
        location_text = f"Location: {location.get('name', 'Unknown')}\nDescription: {location.get('description', '')}\n" \
                        f"Sub-Location: {sub_location.get('name', 'Unknown')}\nSub-Location Description: {sub_location.get('description', '')}"
        self.location_info.setText(location_text)
        location_media = sub_location.get("media", []) or location.get("media", [])
        if location_media and location_media[0].endswith((".png", ".jpg")):
            self.location_media.setPixmap(QPixmap(location_media[0]).scaled(100, 100, Qt.KeepAspectRatio))
        else:
            self.location_media.clear()
        
        if roll_url:
            self.dice_view.load(QUrl(roll_url))
        else:
            self.dice_view.load(QUrl("http://dice.bee.ac/?dicehex=4E1E78&chromahex=00FF00"))
        
        if video_path:
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            context = "event" if event else "opponent" if opponent else "player"
            video_widget = {"player": self.player_video, "opponent": self.opponent_video, "event": self.event_video, "location": self.location_video}[context]
            video_widget.show()
            self.media_player.play()
        else:
            for video_widget in [self.player_video, self.opponent_video, self.event_video, self.location_video]:
                video_widget.hide()
            self.media_player.stop()

class WastelandOdysseyGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GM Window - A Wasteland Odyssey")
        self.setGeometry(100, 100, 800, 600)
        self.json_file = "wasteland_odyssey.json"
        self.data = self.load_json()
        self.selected_weapon = None
        self.selected_target = None
        self.attacker_id = None
        self.current_battle = {"rolls_left": {}, "encounters": {}, "sessions": {}}
        
        self.player_window = PlayerWindow(self.data, self)
        self.player_window.show()
        
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        self.player_tab = QWidget()
        self.player_layout = QVBoxLayout()
        self.player_table = QTableWidget()
        self.player_table.cellClicked.connect(self.select_attacker_or_target)
        self.player_layout.addWidget(self.player_table)
        self.add_player_button = QPushButton("Add Player")
        self.add_player_button.clicked.connect(lambda: self.add_item("players"))
        self.add_player_field_button = QPushButton("Add Custom Field")
        self.add_player_field_button.clicked.connect(lambda: self.add_custom_field("players"))
        self.play_player_video_button = QPushButton("Play Player Video")
        self.play_player_video_button.clicked.connect(self.play_player_video)
        self.player_layout.addWidget(self.add_player_button)
        self.player_layout.addWidget(self.add_player_field_button)
        self.player_layout.addWidget(self.play_player_video_button)
        self.player_tab.setLayout(self.player_layout)
        self.tabs.addTab(self.player_tab, "Players")
        
        self.enemy_tab = QWidget()
        self.enemy_layout = QVBoxLayout()
        self.enemy_table = QTableWidget()
        self.enemy_table.cellClicked.connect(self.select_attacker_or_target)
        self.enemy_layout.addWidget(self.enemy_table)
        self.add_enemy_button = QPushButton("Add Enemy")
        self.add_enemy_button.clicked.connect(lambda: self.add_item("enemies"))
        self.add_enemy_field_button = QPushButton("Add Custom Field")
        self.add_enemy_field_button.clicked.connect(lambda: self.add_custom_field("enemies"))
        self.play_enemy_video_button = QPushButton("Play Enemy Video")
        self.play_enemy_video_button.clicked.connect(self.play_enemy_video)
        self.enemy_layout.addWidget(self.add_enemy_button)
        self.enemy_layout.addWidget(self.add_enemy_field_button)
        self.enemy_layout.addWidget(self.play_enemy_video_button)
        self.enemy_tab.setLayout(self.enemy_layout)
        self.tabs.addTab(self.enemy_tab, "Enemies")
        
        self.weapon_tab = QWidget()
        self.weapon_layout = QVBoxLayout()
        self.weapon_table = QTableWidget()
        self.weapon_layout.addWidget(self.weapon_table)
        self.add_weapon_button = QPushButton("Add Weapon")
        self.add_weapon_button.clicked.connect(lambda: self.add_item("weapons"))
        self.add_weapon_field_button = QPushButton("Add Custom Field")
        self.add_weapon_field_button.clicked.connect(lambda: self.add_custom_field("weapons"))
        self.add_weapon_buff_button = QPushButton("Add Weapon Buff")
        self.add_weapon_buff_button.clicked.connect(self.add_weapon_buff)
        self.add_weapon_effect_button = QPushButton("Add Special Effect")
        self.add_weapon_effect_button.clicked.connect(self.add_weapon_special_effect)
        self.play_weapon_video_button = QPushButton("Play Weapon Video")
        self.play_weapon_video_button.clicked.connect(self.play_weapon_video)
        self.weapon_layout.addWidget(self.add_weapon_button)
        self.weapon_layout.addWidget(self.add_weapon_field_button)
        self.weapon_layout.addWidget(self.add_weapon_buff_button)
        self.weapon_layout.addWidget(self.add_weapon_effect_button)
        self.weapon_layout.addWidget(self.play_weapon_video_button)
        self.weapon_tab.setLayout(self.weapon_layout)
        self.tabs.addTab(self.weapon_tab, "Weapons")
        
        self.armor_tab = QWidget()
        self.armor_layout = QVBoxLayout()
        self.armor_table = QTableWidget()
        self.armor_layout.addWidget(self.armor_table)
        self.add_armor_button = QPushButton("Add Armor")
        self.add_armor_button.clicked.connect(lambda: self.add_item("armor"))
        self.add_armor_field_button = QPushButton("Add Custom Field")
        self.add_armor_field_button.clicked.connect(lambda: self.add_custom_field("armor"))
        self.play_armor_video_button = QPushButton("Play Armor Video")
        self.play_armor_video_button.clicked.connect(self.play_armor_video)
        self.armor_layout.addWidget(self.add_armor_button)
        self.armor_layout.addWidget(self.add_armor_field_button)
        self.armor_layout.addWidget(self.play_armor_video_button)
        self.armor_tab.setLayout(self.armor_layout)
        self.tabs.addTab(self.armor_tab, "Armor")
        
        self.item_tab = QWidget()
        self.item_layout = QVBoxLayout()
        self.item_table = QTableWidget()
        self.item_layout.addWidget(self.item_table)
        self.add_item_button = QPushButton("Add Item")
        self.add_item_button.clicked.connect(lambda: self.add_item("items"))
        self.add_item_field_button = QPushButton("Add Custom Field")
        self.add_item_field_button.clicked.connect(lambda: self.add_custom_field("items"))
        self.play_item_video_button = QPushButton("Play Item Video")
        self.play_item_video_button.clicked.connect(self.play_item_video)
        self.item_layout.addWidget(self.add_item_button)
        self.item_layout.addWidget(self.add_item_field_button)
        self.item_layout.addWidget(self.play_item_video_button)
        self.item_tab.setLayout(self.item_layout)
        self.tabs.addTab(self.item_tab, "Items")
        
        self.buff_tab = QWidget()
        self.buff_layout = QVBoxLayout()
        self.buff_table = QTableWidget()
        self.buff_layout.addWidget(self.buff_table)
        self.add_buff_button = QPushButton("Add Buff")
        self.add_buff_button.clicked.connect(self.add_buff)
        self.play_buff_video_button = QPushButton("Play Buff Video")
        self.play_buff_video_button.clicked.connect(self.play_buff_video)
        self.buff_layout.addWidget(self.add_buff_button)
        self.buff_layout.addWidget(self.play_buff_video_button)
        self.buff_tab.setLayout(self.buff_layout)
        self.tabs.addTab(self.buff_tab, "Buffs")
        
        self.vendor_tab = QWidget()
        self.vendor_layout = QVBoxLayout()
        self.vendor_table = QTableWidget()
        self.vendor_layout.addWidget(self.vendor_table)
        self.add_vendor_button = QPushButton("Add Vendor")
        self.add_vendor_button.clicked.connect(lambda: self.add_item("vendors"))
        self.add_vendor_field_button = QPushButton("Add Custom Field")
        self.add_vendor_field_button.clicked.connect(lambda: self.add_custom_field("vendors"))
        self.play_vendor_video_button = QPushButton("Play Vendor Video")
        self.play_vendor_video_button.clicked.connect(self.play_vendor_video)
        self.vendor_layout.addWidget(self.add_vendor_button)
        self.vendor_layout.addWidget(self.add_vendor_field_button)
        self.vendor_layout.addWidget(self.play_vendor_video_button)
        self.vendor_tab.setLayout(self.vendor_layout)
        self.tabs.addTab(self.vendor_tab, "Vendors")
        
        self.location_tab = QWidget()
        self.location_layout = QVBoxLayout()
        self.location_table = QTableWidget()
        self.location_layout.addWidget(self.location_table)
        self.add_location_button = QPushButton("Add Location")
        self.add_location_button.clicked.connect(lambda: self.add_item("locations"))
        self.add_sublocation_button = QPushButton("Add Sub-Location")
        self.add_sublocation_button.clicked.connect(self.add_sub_location)
        self.add_location_field_button = QPushButton("Add Custom Field")
        self.add_location_field_button.clicked.connect(lambda: self.add_custom_field("locations"))
        self.play_location_video_button = QPushButton("Play Location Video")
        self.play_location_video_button.clicked.connect(self.play_location_video)
        self.location_layout.addWidget(self.add_location_button)
        self.location_layout.addWidget(self.add_sublocation_button)
        self.location_layout.addWidget(self.add_location_field_button)
        self.location_layout.addWidget(self.play_location_video_button)
        self.location_tab.setLayout(self.location_layout)
        self.tabs.addTab(self.location_tab, "Locations")
        
        self.entity_tab = QWidget()
        self.entity_layout = QVBoxLayout()
        self.entity_table = QTableWidget()
        self.entity_layout.addWidget(self.entity_table)
        self.add_entity_button = QPushButton("Add Entity")
        self.add_entity_button.clicked.connect(lambda: self.add_item("entities"))
        self.add_entity_field_button = QPushButton("Add Custom Field")
        self.add_entity_field_button.clicked.connect(lambda: self.add_custom_field("entities"))
        self.play_entity_video_button = QPushButton("Play Entity Video")
        self.play_entity_video_button.clicked.connect(self.play_entity_video)
        self.entity_layout.addWidget(self.add_entity_button)
        self.entity_layout.addWidget(self.add_entity_field_button)
        self.entity_layout.addWidget(self.play_entity_video_button)
        self.entity_tab.setLayout(self.entity_layout)
        self.tabs.addTab(self.entity_tab, "Entities")
        
        self.event_tab = QWidget()
        self.event_layout = QVBoxLayout()
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.roll_event_button = QPushButton("Roll for Special Event")
        self.roll_event_button.clicked.connect(self.roll_for_event)
        self.add_event_button = QPushButton("Add New Event")
        self.add_event_button.clicked.connect(self.add_new_event)
        self.play_event_video_button = QPushButton("Play Event Video")
        self.play_event_video_button.clicked.connect(self.play_event_video)
        self.edit_event_notes_button = QPushButton("View/Edit Event Notes")
        self.edit_event_notes_button.clicked.connect(self.edit_event_notes)
        self.event_layout.addWidget(self.event_log)
        self.event_layout.addWidget(self.roll_event_button)
        self.event_layout.addWidget(self.add_event_button)
        self.event_layout.addWidget(self.play_event_video_button)
        self.event_layout.addWidget(self.edit_event_notes_button)
        self.event_tab.setLayout(self.event_layout)
        self.tabs.addTab(self.event_tab, "Events")
        
        self.battle_tab = QWidget()
        self.battle_layout = QVBoxLayout()
        self.battle_status = QLabel("Select an attacker and target to attack.")
        self.target_select = EnemySelectionDialog(self.data.get("enemies", []), self)
        self.body_part_select = QComboBox()
        self.body_part_select.addItems(["torso", "head", "limbs"])
        self.manual_roll_checkbox = QCheckBox("Manual Roll (Enter dice.bee.ac result)")
        self.roll_attack_button = QPushButton("Roll for Attack")
        self.roll_attack_button.clicked.connect(self.roll_for_attack)
        self.roll_attack_button.setEnabled(False)
        self.battle_log = QTextEdit()
        self.battle_log.setReadOnly(True)
        self.edit_battle_notes_button = QPushButton("View/Edit Battle Notes")
        self.edit_battle_notes_button.clicked.connect(self.edit_battle_notes)
        self.battle_layout.addWidget(self.battle_status)
        self.battle_layout.addWidget(QLabel("Target:"))
        self.battle_layout.addWidget(QLabel("Target Body Part:"))
        self.battle_layout.addWidget(self.body_part_select)
        self.battle_layout.addWidget(QLabel("Manual Roll:"))
        self.battle_layout.addWidget(self.manual_roll_checkbox)
        self.battle_layout.addWidget(self.roll_attack_button)
        self.battle_layout.addWidget(self.battle_log)
        self.battle_layout.addWidget(self.edit_battle_notes_button)
        self.battle_tab.setLayout(self.battle_layout)
        self.tabs.addTab(self.battle_tab, "Battles")
        
        self.log_tab = QWidget()
        self.log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_layout.addWidget(self.log_text)
        self.log_tab.setLayout(self.log_layout)
        self.tabs.addTab(self.log_tab, "Log")
        
        self.update_tables()
        self.update_log()

    def load_json(self):
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "players": [], "enemies": [], "battles": [], "dice_rolls": [], "log": [], 
                "schema": {}, "weapons": [], "armor": [], "items": [], "buffs": [], 
                "vendors": [], "locations": [], "entities": [], "events": []
            }

    def save_json(self):
        with open(self.json_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        self.player_window.data = self.data
        self.player_window.update_display()

    def update_tables(self):
        for category, table in [
            ("players", self.player_table), ("enemies", self.enemy_table), 
            ("weapons", self.weapon_table), ("armor", self.armor_table), 
            ("items", self.item_table), ("buffs", self.buff_table), 
            ("vendors", self.vendor_table), ("locations", self.location_table), 
            ("entities", self.entity_table)
        ]:
            fields = (self.data["schema"].get(category, {}).get("default_fields", []) + 
                      [f["name"] for f in self.data["schema"].get(category, {}).get("custom_fields", [])])
            table.setColumnCount(len(fields))
            table.setHorizontalHeaderLabels(fields)
            table.setRowCount(len(self.data.get(category, [])))
            for i, item in enumerate(self.data.get(category, [])):
                for j, field in enumerate(fields):
                    value = str(item.get(field, ""))
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    table.setItem(i, j, QTableWidgetItem(value))

    def update_log(self):
        log_entries = self.data.get("log", [])
        self.log_text.setText("\n".join([f"{entry['timestamp']}: {entry['details']}" for entry in log_entries]))

    def select_attacker_or_target(self, row, column):
        sender = self.sender()
        if sender == self.player_table:
            entity = self.data.get("players", [])[row]
            entity_type = "player"
        else:
            entity = self.data.get("enemies", [])[row]
            entity_type = "enemy"
        
        if not self.attacker_id:
            self.attacker_id = entity["id"]
            self.selected_weapon = entity.get("equipment", {}).get("weapon")
        self.update_battle_status()

    def update_battle_status(self):
        if self.selected_weapon and self.attacker_id:
            weapon = next((w for w in self.data.get("weapons", []) if w["id"] == self.selected_weapon), {"name": "Attack"})
            attacker = next((p for p in self.data.get("players", []) if p["id"] == self.attacker_id), 
                           next((e for e in self.data.get("enemies", []) if e["id"] == self.attacker_id), {}))
            self.battle_status.setText(f"Ready: {attacker.get('name', '')}'s {weapon['name']} vs. Target")
            self.roll_attack_button.setEnabled(True)
        else:
            self.battle_status.setText("Select an attacker and target to attack.")
            self.roll_attack_button.setEnabled(False)

    def add_custom_field(self, category):
        dialog = FieldDialog(category, self)
        if dialog.exec():
            new_field = dialog.get_data()
            self.data["schema"].setdefault(category, {"default_fields": [], "custom_fields": []})
            self.data["schema"][category]["custom_fields"].append(new_field)
            log_entry = {
                "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "schema",
                "details": f"Added custom field '{new_field['name']}' to {category}"
            }
            self.data["log"].append(log_entry)
            self.save_json()
            self.update_tables()

    def add_item(self, category):
        fields = (self.data["schema"].get(category, {}).get("default_fields", []) + 
                  [f["name"] for f in self.data["schema"].get(category, {}).get("custom_fields", [])])
        fields = [{"name": f, "type": "string" if f not in ["hit_modifier", "success_threshold", "radiation_mod", "dodge_modifier", "scope_accuracy"] else "integer"} for f in fields]
        dialog = ItemDialog(category.capitalize(), fields, self)
        if dialog.exec():
            new_data = dialog.get_data()
            new_id = f"{category[:-1]}_{len(self.data.get(category, [])) + 1:03d}"
            new_data["id"] = new_id
            if category == "events" and "stat_bonuses" in new_data:
                new_data["stat_bonuses"] = new_data["stat_bonuses"].split(",")
            if category == "vendors" and "inventory" in new_data:
                self.update_shared_inventory(new_data)
            media_dialog = MediaDialog(new_data.get("media", []), self)
            if media_dialog.exec():
                new_data["media"] = media_dialog.get_data()
            self.data.setdefault(category, []).append(new_data)
            log_entry = {
                "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": category,
                "details": f"Added new {category[:-1]}: {new_data.get('name', new_id)}"
            }
            self.data["log"].append(log_entry)
            self.save_json()
            self.update_tables()

    def update_shared_inventory(self, vendor_data):
        shared_id = vendor_data.get("shared_inventory_id")
        if shared_id:
            for vendor in self.data.get("vendors", []):
                if vendor.get("shared_inventory_id") == shared_id and vendor["id"] != vendor_data["id"]:
                    vendor["inventory"] = vendor_data["inventory"]

    def add_buff(self):
        dialog = BuffDialog(self)
        if dialog.exec():
            new_buff = dialog.get_data()
            self.data.setdefault("buffs", []).append(new_buff)
            log_entry = {
                "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "buffs",
                "details": f"Added new buff: {new_buff['name']}"
            }
            self.data["log"].append(log_entry)
            self.save_json()
            self.update_tables()

    def add_weapon_buff(self):
        row = self.weapon_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a weapon first.")
            return
        weapon = self.data.get("weapons", [])[row]
        dialog = BuffDialog(self)
        if dialog.exec():
            new_buff = dialog.get_data()
            weapon.setdefault("buffs", []).append(new_buff)
            log_entry = {
                "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "weapons",
                "details": f"Added buff '{new_buff['name']}' to weapon {weapon['name']}"
            }
            self.data["log"].append(log_entry)
            self.save_json()
            self.update_tables()

    def add_weapon_special_effect(self):
        row = self.weapon_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a weapon first.")
            return
        weapon = self.data.get("weapons", [])[row]
        dialog = SpecialEffectDialog(self)
        if dialog.exec():
            new_effect = dialog.get_data()
            weapon.setdefault("special_effects", []).append(new_effect)
            log_entry = {
                "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "weapons",
                "details": f"Added special effect '{new_effect['name']}' to weapon {weapon['name']}"
            }
            self.data["log"].append(log_entry)
            self.save_json()
            self.update_tables()

    def add_sub_location(self):
        dialog = SubLocationDialog(self)
        if dialog.exec():
            new_data = dialog.get_data()
            new_data["id"] = f"subloc_{len(self.data.get('locations', [{}])[0].get('sub_locations', [])) + 1:03d}"
            location_id = self.data["locations"][0]["id"] if self.data.get("locations") else "location_001"
            self.data.setdefault("locations", [{"id": location_id, "sub_locations": []}])
            self.data["locations"][0].setdefault("sub_locations", []).append(new_data)
            log_entry = {
                "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "sub_location",
                "details": f"Added sub-location '{new_data['name']}' to {location_id}"
            }
            self.data["log"].append(log_entry)
            self.save_json()

    def add_new_event(self):
        fields = self.data["schema"].get("events", {}).get("default_fields", []) + \
                 [f["name"] for f in self.data["schema"].get("events", {}).get("custom_fields", [])]
        fields = [{"name": f, "type": "string" if f not in ["success_threshold"] else "integer"} for f in fields] + \
                 [{"name": "puzzle_type", "type": "string"}, {"name": "puzzle_content", "type": "string"}, {"name": "notes", "type": "string"}]
        dialog = ItemDialog("Event", fields, self)
        if dialog.exec():
            new_data = dialog.get_data()
            new_id = f"event_{len(self.data['events']) + 1:03d}"
            new_data["id"] = new_id
            if "stat_bonuses" in new_data:
                new_data["stat_bonuses"] = new_data["stat_bonuses"].split(",")
            if new_data.get("puzzle_content"):
                new_data["puzzle_content"] = {"type": "text" if not new_data["puzzle_content"].endswith((".png", ".jpg")) else "image", 
                                             "value": new_data["puzzle_content"]}
            media_dialog = MediaDialog(new_data.get("media", []), self)
            if media_dialog.exec():
                new_data["media"] = media_dialog.get_data()
            self.data["events"].append(new_data)
            log_entry = {
                "id": f"log_{len(self.data['log']) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "events",
                "details": f"Added new event: {new_data['name']}"
            }
            self.data["log"].append(log_entry)
            self.save_json()
            self.update_tables()

    def edit_event_notes(self):
        if not self.data.get("events"):
            QMessageBox.warning(self, "Error", "No events available.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Event for Notes")
        layout = QVBoxLayout()
        event_select = QComboBox()
        event_select.addItems([e["name"] for e in self.data["events"]])
        layout.addWidget(QLabel("Select Event:"))
        layout.addWidget(event_select)
        submit_button = QPushButton("Edit Notes")
        layout.addWidget(submit_button)
        dialog.setLayout(layout)
        
        def open_notes_dialog():
            event = next((e for e in self.data["events"] if e["name"] == event_select.currentText()), None)
            if event:
                notes_dialog = NotesDialog("event", event["id"], event.get("notes", ""), self)
                if notes_dialog.exec():
                    event["notes"] = notes_dialog.get_data()
                    log_entry = {
                        "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "category": "event_notes",
                        "details": f"Updated notes for event {event['name']}"
                    }
                    self.data["log"].append(log_entry)
                    self.save_json()
                    self.update_log()
                    self.event_log.setText(f"Notes for {event['name']}: {event['notes']}")
                dialog.accept()

        submit_button.clicked.connect(open_notes_dialog)
        dialog.exec()

    def edit_battle_notes(self):
        if not self.data.get("battles"):
            QMessageBox.warning(self, "Error", "No battles available.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Battle for Notes")
        layout = QVBoxLayout()
        battle_select = QComboBox()
        battle_select.addItems([f"Battle {b['id']} at {b['timestamp']}" for b in self.data["battles"]])
        layout.addWidget(QLabel("Select Battle:"))
        layout.addWidget(battle_select)
        submit_button = QPushButton("Edit Notes")
        layout.addWidget(submit_button)
        dialog.setLayout(layout)
        
        def open_notes_dialog():
            battle_index = battle_select.currentIndex()
            battle = self.data["battles"][battle_index]
            notes_dialog = NotesDialog("battle", battle["id"], battle.get("notes", ""), self)
            if notes_dialog.exec():
                battle["notes"] = notes_dialog.get_data()
                log_entry = {
                    "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "category": "battle_notes",
                    "details": f"Updated notes for battle {battle['id']}"
                }
                self.data["log"].append(log_entry)
                self.save_json()
                self.update_log()
                self.battle_log.setText(f"Notes for {battle['id']}: {battle['notes']}")
            dialog.accept()

        submit_button.clicked.connect(open_notes_dialog)
        dialog.exec()

    def play_player_video(self):
        row = self.player_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a player first.")
            return
        player = self.data.get("players", [])[row]
        video_files = [m for m in player.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this player.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for player {player['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_enemy_video(self):
        row = self.enemy_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an enemy first.")
            return
        enemy = self.data.get("enemies", [])[row]
        video_files = [m for m in enemy.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this enemy.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for enemy {enemy['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_weapon_video(self):
        row = self.weapon_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a weapon first.")
            return
        weapon = self.data.get("weapons", [])[row]
        video_files = [m for m in weapon.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this weapon.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for weapon {weapon['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_armor_video(self):
        row = self.armor_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an armor first.")
            return
        armor = self.data.get("armor", [])[row]
        video_files = [m for m in armor.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this armor.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for armor {armor['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_item_video(self):
        row = self.item_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an item first.")
            return
        item = self.data.get("items", [])[row]
        video_files = [m for m in item.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this item.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for item {item['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_buff_video(self):
        row = self.buff_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a buff first.")
            return
        buff = self.data.get("buffs", [])[row]
        video_files = [m for m in buff.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this buff.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for buff {buff['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_vendor_video(self):
        row = self.vendor_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a vendor first.")
            return
        vendor = self.data.get("vendors", [])[row]
        video_files = [m for m in vendor.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this vendor.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for vendor {vendor['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_location_video(self):
        row = self.location_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a location first.")
            return
        location = self.data.get("locations", [])[row]
        video_files = [m for m in location.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this location.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for location {location['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_entity_video(self):
        row = self.entity_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select an entity first.")
            return
        entity = self.data.get("entities", [])[row]
        video_files = [m for m in entity.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this entity.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for entity {entity['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def play_event_video(self):
        if not self.data.get("battles"):
            QMessageBox.warning(self, "Error", "No active event.")
            return
        event_id = self.data.get("battles", [{}])[-1].get("event_id")
        event = next((e for e in self.data.get("events", []) if e["id"] == event_id), {})
        video_files = [m for m in event.get("media", []) if m.endswith(".mp4")]
        if not video_files:
            QMessageBox.warning(self, "Error", "No video available for this event.")
            return
        self.player_window.update_display(video_path=video_files[0])
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "video_playback",
            "details": f"GM triggered video {video_files[0]} for event {event['name']}"
        }
        self.data["log"].append(log_entry)
        self.save_json()
        self.update_log()

    def roll_for_attack(self):
        if not self.selected_weapon or not self.attacker_id:
            QMessageBox.warning(self, "Error", "Select an attacker and weapon.")
            return
        
        target_dialog = self.target_select
        if target_dialog.exec():
            target_data = target_dialog.get_data()
            if target_data["create_new"]:
                new_enemy = {
                    "id": f"enemy_{len(self.data.get('enemies', [])) + 1:03d}",
                    "name": target_data["name"],
                    "description": target_data["description"],
                    "media": target_data["media"],
                    "stats": target_data["stats"],
                    "ac": target_data["ac"],
                    "equipment": target_data["equipment"],
                    "buffs": target_data["buffs"],
                    "location": self.data["players"][0]["location"],
                    "sub_location": self.data["players"][0]["sub_location"]
                }
                self.data.setdefault("enemies", []).append(new_enemy)
                self.selected_target = new_enemy["id"]
            else:
                target = next((e for e in self.data.get("enemies", []) if e["name"] == target_data["name"]), None)
                if not target:
                    QMessageBox.warning(self, "Error", "Invalid target.")
                    return
                self.selected_target = target["id"]
        
        dice_notation = "1d20"
        body_part = self.body_part_select.currentText()
        manual_roll = self.manual_roll_checkbox.isChecked()
        
        roll_url = f"http://dice.bee.ac/?dicehex=4E1E78&labelhex=CC9EEC&chromahex=00FF00&d={dice_notation}&roll&resultsize=24"
        
        if manual_roll:
            dialog = ManualRollDialog(dice_notation, "Enter Attack Roll (1d20)", self)
            if dialog.exec():
                roll_data = dialog.get_data()
                attack_result = str(roll_data["total"])
                manual_results = roll_data["individual"]
            else:
                return
        else:
            dialog = ManualRollDialog(dice_notation, "Enter dice.bee.ac Attack Roll (1d20)", self)
            if dialog.exec():
                roll_data = dialog.get_data()
                attack_result = str(roll_data["total"])
                manual_results = roll_data["individual"]
            else:
                return
        
        hit_chance_dialog = ManualRollDialog("1d100", "Enter Body Part Hit Chance Roll (1d100)", self)
        if hit_chance_dialog.exec():
            hit_chance_result = hit_chance_dialog.get_data()["total"]
        else:
            hit_chance_result = 50
        
        roll_entry = {
            "id": f"roll_{len(self.data.get('dice_rolls', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dice_notation": dice_notation,
            "result": attack_result,
            "manual_entry": True,
            "manual_results": manual_results,
            "breakdown": [{"die": "d20", "value": int(attack_result)}],
            "attacker_id": self.attacker_id,
            "target_id": self.selected_target,
            "url": roll_url
        }
        self.data.setdefault("dice_rolls", []).append(roll_entry)
        
        weapon = next((w for w in self.data.get("weapons", []) if w["id"] == self.selected_weapon), {})
        special_effects = weapon.get("special_effects", [])
        special_damages = []
        for effect in special_effects:
            prob_dialog = ManualRollDialog("1d4", f"Enter {effect['name']} Probability Roll (1d4, 1 triggers)", self)
            if prob_dialog.exec():
                prob_result = prob_dialog.get_data()["total"]
                if prob_result == 1:
                    damage_dialog = ManualRollDialog(effect["dice"], f"Enter {effect['name']} Damage Roll ({effect['dice']})", self)
                    if damage_dialog.exec():
                        damage_result = damage_dialog.get_data()["total"]
                        effect_roll_entry = {
                            "id": f"roll_{len(self.data.get('dice_rolls', [])) + 1:03d}",
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "dice_notation": effect["dice"],
                            "result": str(damage_result),
                            "manual_entry": True,
                            "manual_results": damage_dialog.get_data()["individual"],
                            "breakdown": [{"die": effect["dice"].split("d")[1], "value": damage_result}],
                            "attacker_id": self.attacker_id,
                            "target_id": self.selected_target,
                            "url": roll_url
                        }
                        self.data["dice_rolls"].append(effect_roll_entry)
                        special_damages.append({"type": effect["damage_type"], "amount": damage_result})
        
        attacker = next((p for p in self.data["players"] if p["id"] == self.attacker_id), 
                       next((e for e in self.data["enemies"] if e["id"] == self.attacker_id), {}))
        target = next((p for p in self.data["players"] if p["id"] == self.selected_target), 
                     next((e for e in self.data["enemies"] if e["id"] == self.selected_target), {}))
        hit_modifier = self.calculate_hit_modifier(attacker, weapon, None)
        
        body_parts = self.data["schema"]["body_parts"]["default"]
        scope_accuracy = weapon.get("scope_accuracy", 0)
        adjusted_ranges = []
        for bp in body_parts:
            start, end = bp["hit_range"]
            delta = int((end - start + 1) * scope_accuracy)
            adjusted_ranges.append({"name": bp["name"], "range": [start, end + delta], "multiplier": bp["damage_multiplier"]})
        hit_body_part = "torso"
        for bp in adjusted_ranges:
            if bp["range"][0] <= hit_chance_result <= bp["range"][1]:
                hit_body_part = bp["name"]
                break
        damage_multiplier = next((bp["multiplier"] for bp in adjusted_ranges if bp["name"] == hit_body_part), 1.0)
        
        damage_dice = weapon.get("damage_dice", "1d4")
        damage_dialog = ManualRollDialog(dice_notation=damage_dice, label=f"Enter Damage Roll ({damage_dice})", parent=self)
        if damage_dialog.exec():
            damage_result = damage_dialog.get_data()["total"]
            damage_roll_entry = {
                "id": f"roll_{len(self.data.get('dice_rolls', [])) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "dice_notation": damage_dice,
                "result": str(damage_result),
                "manual_entry": True,
                "manual_results": damage_dialog.get_data()["individual"],
                "breakdown": [{"die": damage_dice.split("d")[1], "value": v} for v in damage_dialog.get_data()["individual"]],
                "attacker_id": self.attacker_id,
                "target_id": self.selected_target,
                "url": roll_url
            }
            self.data["dice_rolls"].append(damage_roll_entry)
        else:
            damage_result = 0
        
        damage = int(damage_result * damage_multiplier)
        radiation_damage = int(damage * weapon.get("radiation_mod", 1.0))
        
        target_armor = next((a for a in self.data["armor"] if a["id"] == target["equipment"].get("armor")), {})
        physical_resistance = target_armor.get("damage_resistance", {}).get("physical", 0)
        radiation_resistance = target_armor.get("damage_resistance", {}).get("radiation", 0)
        damage = max(0, damage - physical_resistance)
        radiation_damage = max(0, radiation_damage - radiation_resistance)
        
        location = next((loc for loc in self.data["locations"] if loc["id"] == attacker["location"]), {})
        sub_location = next((subloc for subloc in location.get("sub_locations", []) if subloc["id"] == attacker["sub_location"]), {})
        env_effects = sub_location.get("environmental_effects", location.get("environmental_effects", {}))
        env_damage = 0
        if "radiation" in env_effects:
            rad = env_effects["radiation"]
            env_damage = max(0, rad["damage"] - int(rad["scale_factor"] * target["stats"].get(rad["scale_stat"], 0)))
        
        total_damage = damage + radiation_damage + sum(d["amount"] for d in special_damages) + env_damage
        
        dodge_chance = target_armor.get("dodge_modifier", 0) + sum(b["effect"].get("dodge_chance", 0) for b in target.get("buffs", []))
        dodge_roll = random.randint(1, 20)
        hit_success = (int(attack_result) + hit_modifier >= target["ac"]) and (dodge_roll / 20 > dodge_chance)
        
        if hit_success:
            target["stats"]["hp"] = max(0, target["stats"]["hp"] - total_damage)
        
        battle_entry = {
            "id": f"battle_{len(self.data.get('battles', [])) + 1:03d}",
            "event_id": None,
            "participants": [self.attacker_id, self.selected_target],
            "location": attacker["location"],
            "sub_location": attacker["sub_location"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "log": [{
                "turn": 1,
                "action": f"{attacker['name']} attacked {target['name']}",
                "dice_roll_id": roll_entry["id"],
                "damage_dice": damage_dice,
                "damage": damage,
                "radiation_damage": radiation_damage,
                "special_damage": special_damages,
                "body_part": hit_body_part,
                "hit_modifier": hit_modifier
            }],
            "notes": ""
        }
        self.data["battles"].append(battle_entry)
        
        log_details = (f"{attacker['name']} rolled 1d20={attack_result} (+{hit_modifier}) vs AC {target['ac']}, "
                      f"{'hit' if hit_success else 'missed'} {hit_body_part} for {damage} damage "
                      f"+ {radiation_damage} radiation + {sum(d['amount'] for d in special_damages)} special "
                      f"+ {env_damage} environmental.")
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "category": "battle",
            "details": log_details
        }
        self.data["log"].append(log_entry)
        
        self.update_buff_durations(attacker, "rolls")
        
        self.save_json()
        self.update_tables()
        self.update_log()
        self.battle_log.setText(log_details)
        self.player_window.update_display(roll_url=roll_url)

    def roll_for_event(self):
        dialog = EventRollDialog(self.data.get("players", []), self.data.get("enemies", []), 
                                self.data.get("events", []), self.data.get("items", []), self)
        if dialog.exec():
            event_data = dialog.get_data()
            entity = next((p for p in self.data["players"] if p["name"] == event_data["entity_name"]), 
                         next((e for e in self.data["enemies"] if e["name"] == event_data["entity_name"]), None))
            if not entity:
                QMessageBox.warning(self, "Error", "Invalid entity.")
                return
            
            event = next((e for e in self.data["events"] if e["name"] == event_data["event_name"]), None)
            if event_data["event_name"] == "Custom Event":
                event = {
                    "id": f"event_{len(self.data['events']) + 1:03d}",
                    "name": f"Custom Event {len(self.data['events']) + 1}",
                    "description": "Custom event created on-the-fly",
                    "dice": event_data["dice"],
                    "success_threshold": event_data["success_threshold"],
                    "stat_bonuses": event_data.get("stat_bonuses", "").split(",") if event_data.get("stat_bonuses") else [],
                    "loot": [item["name"] for item in event_data["loot"]],
                    "media": [],
                    "puzzle_type": event_data["puzzle_type"],
                    "puzzle_content": event_data["puzzle_content"],
                    "puzzle_resolution": {"solved": event_data["puzzle_solved"], "answer": event_data["puzzle_answer"]},
                    "notes": event_data["notes"]
                }
                self.data["events"].append(event)
            else:
                event["puzzle_resolution"] = {"solved": event_data["puzzle_solved"], "answer": event_data["puzzle_answer"]}
                event["notes"] = event_data["notes"]
            
            guardian = event_data["guardian"]
            guardian_success = True
            if guardian and event_data["guardian_type"]:
                if guardian["create_new"]:
                    new_enemy = {
                        "id": f"enemy_{len(self.data['enemies']) + 1:03d}",
                        "name": guardian["name"],
                        "description": guardian["description"],
                        "media": guardian["media"],
                        "stats": guardian["stats"],
                        "ac": guardian["ac"],
                        "equipment": guardian["equipment"],
                        "buffs": guardian["buffs"],
                        "location": entity["location"],
                        "sub_location": entity["sub_location"]
                    }
                    self.data["enemies"].append(new_enemy)
                    guardian_id = new_enemy["id"]
                else:
                    guardian_entity = next((e for e in self.data["enemies"] if e["name"] == guardian["name"]), None)
                    if not guardian_entity:
                        QMessageBox.warning(self, "Error", "Invalid guardian.")
                        return
                    guardian_id = guardian_entity["id"]
                
                if event_data["guardian_type"] == "battle":
                    self.attacker_id = entity["id"]
                    self.selected_weapon = entity["equipment"].get("weapon")
                    self.selected_target = guardian_id
                    self.body_part_select.setCurrentText("torso")
                    self.roll_for_attack()
                    guardian_entity = next((e for e in self.data["enemies"] if e["id"] == guardian_id), {})
                    guardian_success = guardian_entity["stats"]["hp"] <= 0
                elif event_data["guardian_type"] == "puzzle":
                    puzzle_event = {
                        "id": f"event_{len(self.data['events']) + 1:03d}",
                        "name": f"Puzzle for {event['name']}",
                        "description": "Solve the puzzle to proceed",
                        "dice": "1d20",
                        "success_threshold": 15,
                        "stat_bonuses": ["intelligence", "engineering"],
                        "loot": [],
                        "media": [],
                        "puzzle_type": event_data["puzzle_type"],
                        "puzzle_content": event_data["puzzle_content"],
                        "puzzle_resolution": {"solved": event_data["puzzle_solved"], "answer": event_data["puzzle_answer"]},
                        "notes": event_data["notes"]
                    }
                    self.data["events"].append(puzzle_event)
                    guardian_success = event_data["puzzle_solved"] or self.process_event_roll(entity, puzzle_event, event_data["buffs"], event_data["manual_roll"])
            
            if not guardian_success:
                log_entry = {
                    "id": f"log_{len(self.data['log']) + 1:03d}",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "category": "event",
                    "details": f"{entity['name']} failed guardian challenge for {event['name']}"
                }
                self.data["log"].append(log_entry)
                self.save_json()
                self.update_log()
                self.event_log.setText(log_entry["details"])
                self.player_window.update_display()
                return
            
            success = event["puzzle_resolution"]["solved"] if event.get("puzzle_type") in ["word", "coded_terminal", "logic"] else \
                     self.process_event_roll(entity, event, event_data["buffs"], event_data["manual_roll"])
            
            for loot_item in event_data["loot"]:
                if "id" not in loot_item:
                    new_item = {
                        "id": f"item_{len(self.data['items']) + 1:03d}",
                        "name": loot_item["name"],
                        "description": loot_item.get("description", ""),
                        "type": loot_item.get("type", "Loot"),
                        "hit_modifier": loot_item.get("hit_modifier", 0),
                        "media": loot_item.get("media", [])
                    }
                    self.data["items"].append(new_item)
                    entity["equipment"]["items"].append(new_item["id"])
            
            log_details = (f"{entity['name']} attempted {event['name']} ({event['puzzle_type']} puzzle), "
                          f"{'Succeeded' if success else 'Failed'}. Answer: {event['puzzle_resolution']['answer']}")
            log_entry = {
                "id": f"log_{len(self.data['log']) + 1:03d}",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "category": "event",
                "details": log_details
            }
            self.data["log"].append(log_entry)
            
            self.update_buff_durations(entity, "rolls")
            
            self.save_json()
            self.update_log()
            self.event_log.setText(log_details + f"\nNotes: {event['notes']}")
            roll_url = f"http://dice.bee.ac/?dicehex=4E1E78&labelhex=CC9EEC&chromahex=00FF00&d={event['dice']}&roll&resultsize=24"
            self.player_window.update_display(roll_url=roll_url)

    def calculate_hit_modifier(self, entity, weapon, event):
        hit_modifier = 0
        stats = entity.get("stats", {})
        weapon = weapon or {}
        buffs = entity.get("buffs", []) + weapon.get("buffs", [])
        
        for stat in ["strength", "agility", "engineering", "intelligence", "luck"]:
            if weapon.get(f"{stat}_bonus", False):
                hit_modifier += stats.get(stat, 0)
            if event and stat in event.get("stat_bonuses", []):
                hit_modifier += stats.get(stat, 0)
        
        hit_modifier += weapon.get("hit_modifier", 0)
        armor = next((a for a in self.data["armor"] if a["id"] == entity["equipment"].get("armor")), {})
        hit_modifier += armor.get("hit_modifier", 0)
        for item_id in entity["equipment"].get("items", []):
            item = next((i for i in self.data["items"] if i["id"] == item_id), {})
            hit_modifier += item.get("hit_modifier", 0)
        
        for buff in buffs:
            effect = buff.get("effect", {})
            if "hit_modifier" in effect:
                if event and effect.get("applies_to_event") == event["name"]:
                    hit_modifier += effect["hit_modifier"]
                elif effect.get("applies_to") and weapon.get(f"{effect['applies_to']}_bonus", False):
                    hit_modifier += effect["hit_modifier"]
                elif not effect.get("applies_to_event") and not effect.get("applies_to"):
                    hit_modifier += effect["hit_modifier"]
            for stat in ["strength", "agility", "engineering", "intelligence", "luck"]:
                if stat in effect:
                    hit_modifier += effect[stat]
        
        return hit_modifier

    def process_event_roll(self, entity, event, selected_buffs, manual_roll):
        roll_url = f"http://dice.bee.ac/?dicehex=4E1E78&labelhex=CC9EEC&chromahex=00FF00&d={event['dice']}&roll&resultsize=24"
        if manual_roll:
            dialog = ManualRollDialog(event["dice"], f"Enter Event Roll ({event['dice']})", self)
            if dialog.exec():
                roll_data = dialog.get_data()
                roll_result = roll_data["total"]
                manual_results = roll_data["individual"]
            else:
                return False
        else:
            dialog = ManualRollDialog(event["dice"], f"Enter dice.bee.ac Event Roll ({event['dice']})", self)
            if dialog.exec():
                roll_data = dialog.get_data()
                roll_result = roll_data["total"]
                manual_results = roll_data["individual"]
            else:
                return False
        
        roll_entry = {
            "id": f"roll_{len(self.data['dice_rolls']) + 1:03d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "dice_notation": event["dice"],
            "result": str(roll_result),
            "manual_entry": True,
            "manual_results": manual_results,
            "breakdown": [{"die": event["dice"].split("d")[1], "value": v} for v in manual_results],
            "attacker_id": entity["id"],
            "event_name": event["name"],
            "url": roll_url
        }
        self.data["dice_rolls"].append(roll_entry)
        
        weapon = next((w for w in self.data["weapons"] if w["id"] == entity["equipment"].get("weapon")), {})
        hit_modifier = self.calculate_hit_modifier(entity, weapon, event)
        total = roll_result + hit_modifier
        success = total >= event["success_threshold"]
        
        location = next((loc for loc in self.data["locations"] if loc["id"] == entity["location"]), {})
        sub_location = next((subloc for subloc in location.get("sub_locations", []) if subloc["id"] == entity["sub_location"]), {})
        env_effects = sub_location.get("environmental_effects", location.get("environmental_effects", {}))
        if "radiation" in env_effects and success:
            rad = env_effects["radiation"]
            env_damage = max(0, rad["damage"] - int(rad["scale_factor"] * entity["stats"].get(rad["scale_stat"], 0)))
            entity["stats"]["hp"] = max(0, entity["stats"]["hp"] - env_damage)
        
        return success

    def update_buff_durations(self, entity, trigger_type):
        buffs = entity.get("buffs", []) + self.current_battle.get("rolls_left", {})
        weapon = next((w for w in self.data["weapons"] if w["id"] == entity["equipment"].get("weapon")), {})
        buffs.extend(weapon.get("buffs", []))
        
        for buff in buffs[:]:
            duration = buff.get("duration")
            if duration == "3 rolls" and trigger_type == "rolls":
                self.current_battle["rolls_left"][buff["name"]] = self.current_battle.get("rolls_left", {}).get(buff["name"], 3) - 1
                if self.current_battle["rolls_left"][buff["name"]] <= 0:
                    if buff in entity["buffs"]:
                        entity["buffs"].remove(buff)
                    elif buff in weapon["buffs"]:
                        weapon["buffs"].remove(buff)
            elif duration == "1 encounter" and trigger_type == "encounter":
                if buff in entity["buffs"]:
                    entity["buffs"].remove(buff)
                elif buff in weapon["buffs"]:
                    weapon["buffs"].remove(buff)
            elif duration == "1 session" and trigger_type == "session":
                if buff in entity["buffs"]:
                    entity["buffs"].remove(buff)
                elif buff in weapon["buffs"]:
                    weapon["buffs"].remove(buff)
        
        self.save_json()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WastelandOdysseyGUI()
    window.show()
    sys.exit(app.exec())