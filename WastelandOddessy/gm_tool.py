import sys
import json
import re
import random
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QTextEdit, 
                               QMessageBox, QFormLayout, QDialog, QLabel, QComboBox, QSpinBox, 
                               QDoubleSpinBox, QCheckBox, QFileDialog, QGroupBox, 
                               QScrollArea, QGridLayout, QListWidget, QListWidgetItem, QInputDialog,
                               QDialogButtonBox)
from PySide6.QtCore import Qt, QUrl, Signal, Slot, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWebEngineWidgets import QWebEngineView
from datetime import datetime, timezone
from dateutil.parser import isoparse

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

        # --- Resistances with pick-list ---
        all_resistances = set()
        parent_data = getattr(parent, 'data', {}) if parent else {}
        for a in parent_data.get('armor', []):
            for k in a.get('resistances', {}).keys():
                all_resistances.add(k)
        for w in parent_data.get('weapons', []):
            for eff in w.get('special_effects', []):
                if eff.get('damage_type'):
                    all_resistances.add(eff['damage_type'])
        for i in parent_data.get('items', []):
            for k in i.get('resistances', {}).keys():
                all_resistances.add(k)
        for b in parent_data.get('buffs', []):
            for k in b.get('resistances', {}).keys():
                all_resistances.add(k)
        all_resistances = sorted(s for s in all_resistances if s)
        self.resistances = {}
        resist_pick = QComboBox()
        resist_pick.addItem('(Add New Resistance)')
        for r in all_resistances:
            resist_pick.addItem(r)
        resist_list = QListWidget()
        def add_resist():
            idx = resist_pick.currentIndex()
            if idx == 0:
                text, ok = QInputDialog.getText(self, "Add Resistance Type", "Type:")
                if ok and text:
                    self.resistances[text] = 0
                    resist_list.addItem(f"{text}: 0")
            else:
                t = resist_pick.currentText()
                if t not in self.resistances:
                    self.resistances[t] = 0
                    resist_list.addItem(f"{t}: 0")
        add_resist_btn = QPushButton('Add Resistance')
        add_resist_btn.clicked.connect(add_resist)
        def edit_resist():
            idx = resist_list.currentRow()
            if idx >= 0:
                key = list(self.resistances.keys())[idx]
                val, ok = QInputDialog.getInt(self, "Edit Resistance Value", f"Value for {key}:", self.resistances[key], -99, 999)
                if ok:
                    self.resistances[key] = val
                    resist_list.item(idx).setText(f"{key}: {val}")
        edit_resist_btn = QPushButton('Edit Selected Resistance')
        edit_resist_btn.clicked.connect(edit_resist)
        def remove_resist():
            idx = resist_list.currentRow()
            if idx >= 0:
                key = list(self.resistances.keys())[idx]
                del self.resistances[key]
                resist_list.takeItem(idx)
        remove_resist_btn = QPushButton('Remove Selected Resistance')
        remove_resist_btn.clicked.connect(remove_resist)
        self.layout.addRow('Resistances:', resist_pick)
        self.layout.addRow('', add_resist_btn)
        self.layout.addRow('Current Resistances:', resist_list)
        self.layout.addRow('', edit_resist_btn)
        self.layout.addRow('', remove_resist_btn)

        # --- Vulnerabilities with pick-list ---
        all_vulns = set()
        for a in parent_data.get('armor', []):
            for k in a.get('vulnerabilities', {}).keys():
                all_vulns.add(k)
        for w in parent_data.get('weapons', []):
            for eff in w.get('special_effects', []):
                if eff.get('damage_type'):
                    all_vulns.add(eff['damage_type'])
        for i in parent_data.get('items', []):
            for k in i.get('vulnerabilities', {}).keys():
                all_vulns.add(k)
        for b in parent_data.get('buffs', []):
            for k in b.get('vulnerabilities', {}).keys():
                all_vulns.add(k)
        all_vulns = sorted(s for s in all_vulns if s)
        self.vulnerabilities = {}
        vuln_pick = QComboBox()
        vuln_pick.addItem('(Add New Vulnerability)')
        for v in all_vulns:
            vuln_pick.addItem(v)
        vuln_list = QListWidget()
        def add_vuln():
            idx = vuln_pick.currentIndex()
            if idx == 0:
                text, ok = QInputDialog.getText(self, "Add Vulnerability Type", "Type:")
                if ok and text:
                    self.vulnerabilities[text] = 0
                    vuln_list.addItem(f"{text}: 0")
            else:
                t = vuln_pick.currentText()
                if t not in self.vulnerabilities:
                    self.vulnerabilities[t] = 0
                    vuln_list.addItem(f"{t}: 0")
        add_vuln_btn = QPushButton('Add Vulnerability')
        add_vuln_btn.clicked.connect(add_vuln)
        def edit_vuln():
            idx = vuln_list.currentRow()
            if idx >= 0:
                key = list(self.vulnerabilities.keys())[idx]
                val, ok = QInputDialog.getInt(self, "Edit Vulnerability Value", f"Value for {key}:", self.vulnerabilities[key], -99, 999)
                if ok:
                    self.vulnerabilities[key] = val
                    vuln_list.item(idx).setText(f"{key}: {val}")
        edit_vuln_btn = QPushButton('Edit Selected Vulnerability')
        edit_vuln_btn.clicked.connect(edit_vuln)
        def remove_vuln():
            idx = vuln_list.currentRow()
            if idx >= 0:
                key = list(self.vulnerabilities.keys())[idx]
                del self.vulnerabilities[key]
                vuln_list.takeItem(idx)
        remove_vuln_btn = QPushButton('Remove Selected Vulnerability')
        remove_vuln_btn.clicked.connect(remove_vuln)
        self.layout.addRow('Vulnerabilities:', vuln_pick)
        self.layout.addRow('', add_vuln_btn)
        self.layout.addRow('Current Vulnerabilities:', vuln_list)
        self.layout.addRow('', edit_vuln_btn)
        self.layout.addRow('', remove_vuln_btn)

        # --- Special Effects with pick-list (reuse from weapon dialog) ---
        special_btn = QPushButton('Edit Special Effects')
        self.special_effects = []
        all_specials = set()
        for w in parent_data.get('weapons', []):
            for eff in w.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for a in parent_data.get('armor', []):
            for eff in a.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for i in parent_data.get('items', []):
            for eff in i.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for b in parent_data.get('buffs', []):
            for eff in b.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        all_specials = sorted(s for s in all_specials if s)
        special_pick = QComboBox()
        special_pick.addItem('(Add New Special Effect)')
        for s in all_specials:
            special_pick.addItem(s)
        def edit_special():
            idx = special_pick.currentIndex()
            if idx == 0:
                dlg = SpecialEffectDialog(parent=self)
                if dlg.exec():
                    self.special_effects.append(dlg.get_data())
            else:
                name = special_pick.currentText()
                eff = None
                for w in parent_data.get('weapons', []):
                    for e in w.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for a in parent_data.get('armor', []):
                    for e in a.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for i in parent_data.get('items', []):
                    for e in i.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for b in parent_data.get('buffs', []):
                    for e in b.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                if eff:
                    dlg = SpecialEffectDialog(effect=eff, parent=self)
                    if dlg.exec():
                        self.special_effects.append(dlg.get_data())
        special_btn.clicked.connect(edit_special)
        special_list = QListWidget()
        def refresh_special_list():
            special_list.clear()
            for eff in self.special_effects:
                special_list.addItem(eff.get('name', ''))
        refresh_special_list()
        remove_special_btn = QPushButton('Remove Selected Special')
        def remove_special():
            idx = special_list.currentRow()
            if idx >= 0:
                self.special_effects.pop(idx)
                refresh_special_list()
        remove_special_btn.clicked.connect(remove_special)
        self.layout.addRow('Special Effects:', special_pick)
        self.layout.addRow('', special_btn)
        self.layout.addRow('Current Specials:', special_list)
        self.layout.addRow('', remove_special_btn)

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
            "duration": self.duration.currentText(),
            "resistances": self.resistances,
            "vulnerabilities": self.vulnerabilities,
            "special_effects": self.special_effects
        }

class SpecialEffectDialog(QDialog):
    def __init__(self, effect=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Special Effect")
        self.layout = QFormLayout()
        self.name_input = QLineEdit(effect.get('name', '') if effect else '')
        self.desc_input = QTextEdit(effect.get('description', '') if effect else '')
        self.probability_input = QLineEdit(effect.get('probability_dice', '') if effect else '')
        self.trigger_number_input = QSpinBox()
        self.trigger_number_input.setRange(1, 100)
        self.trigger_number_input.setValue(effect.get('trigger_number', 1) if effect else 1)
        self.dice_input = QLineEdit(effect.get('dice', '') if effect else '')
        self.flat_bonus_input = QSpinBox()
        self.flat_bonus_input.setRange(-99, 99)
        self.flat_bonus_input.setValue(effect.get('flat_bonus', 0) if effect else 0)
        self.damage_type_input = QLineEdit(effect.get('damage_type', '') if effect else '')
        self.media_button = QPushButton("Add Media")
        self.media_button.clicked.connect(self.add_media)
        self.media_list = list(effect.get('media', [])) if effect else []
        self.media_display = QTextEdit()
        self.media_display.setReadOnly(True)
        self.media_display.setText("\n".join(self.media_list))
        # Applies section
        self.applies = effect.get('applies', {}) if effect else {}
        self.applies_group = QGroupBox("Applies (Ongoing Effects)")
        self.applies_layout = QVBoxLayout()
        # Lost limbs
        self.lost_limbs_list = QListWidget()
        for limb in self.applies.get('lost_limbs', []):
            self.lost_limbs_list.addItem(limb)
        lost_limb_btns = QHBoxLayout()
        add_lost_limb = QPushButton("Add Lost Limb")
        remove_lost_limb = QPushButton("Remove")
        lost_limb_btns.addWidget(add_lost_limb)
        lost_limb_btns.addWidget(remove_lost_limb)
        def add_limb():
            text, ok = QInputDialog.getText(self, "Add Lost Limb", "Limb:")
            if ok and text:
                self.lost_limbs_list.addItem(text)
        def remove_limb():
            idx = self.lost_limbs_list.currentRow()
            if idx >= 0:
                self.lost_limbs_list.takeItem(idx)
        add_lost_limb.clicked.connect(add_limb)
        remove_lost_limb.clicked.connect(remove_limb)
        self.applies_layout.addWidget(QLabel("Lost Limbs:"))
        self.applies_layout.addWidget(self.lost_limbs_list)
        self.applies_layout.addLayout(lost_limb_btns)
        # Broken limbs
        self.broken_limbs_list = QListWidget()
        for limb in self.applies.get('broken_limbs', []):
            self.broken_limbs_list.addItem(limb)
        broken_limb_btns = QHBoxLayout()
        add_broken_limb = QPushButton("Add Broken Limb")
        remove_broken_limb = QPushButton("Remove")
        broken_limb_btns.addWidget(add_broken_limb)
        broken_limb_btns.addWidget(remove_broken_limb)
        def add_broken():
            text, ok = QInputDialog.getText(self, "Add Broken Limb", "Limb:")
            if ok and text:
                self.broken_limbs_list.addItem(text)
        def remove_broken():
            idx = self.broken_limbs_list.currentRow()
            if idx >= 0:
                self.broken_limbs_list.takeItem(idx)
        add_broken_limb.clicked.connect(add_broken)
        remove_broken_limb.clicked.connect(remove_broken)
        self.applies_layout.addWidget(QLabel("Broken Limbs:"))
        self.applies_layout.addWidget(self.broken_limbs_list)
        self.applies_layout.addLayout(broken_limb_btns)
        # Status effects
        self.status_effects_list = QListWidget()
        for se in self.applies.get('status_effects', []):
            if isinstance(se, dict):
                name = se.get('name', '')
                dur = se.get('duration', None)
                label = f"{name} ({dur}r)" if dur else name
            else:
                label = str(se)
            self.status_effects_list.addItem(label)
        status_btns = QHBoxLayout()
        add_status = QPushButton("Add Status Effect")
        remove_status = QPushButton("Remove")
        status_btns.addWidget(add_status)
        status_btns.addWidget(remove_status)
        def add_status_effect():
            name, ok = QInputDialog.getText(self, "Add Status Effect", "Name:")
            if not ok or not name:
                return
            dur, ok = QInputDialog.getInt(self, "Add Status Effect", "Duration (rounds, 0 for permanent):", 0, 0, 99)
            if ok:
                label = f"{name} ({dur}r)" if dur else name
                self.status_effects_list.addItem(label)
        def remove_status_effect():
            idx = self.status_effects_list.currentRow()
            if idx >= 0:
                self.status_effects_list.takeItem(idx)
        add_status.clicked.connect(add_status_effect)
        remove_status.clicked.connect(remove_status_effect)
        self.applies_layout.addWidget(QLabel("Status Effects:"))
        self.applies_layout.addWidget(self.status_effects_list)
        self.applies_layout.addLayout(status_btns)
        self.applies_group.setLayout(self.applies_layout)
        # Layout
        self.layout.addRow("Name:", self.name_input)
        self.layout.addRow("Description:", self.desc_input)
        self.layout.addRow("Probability Dice (e.g., 1d4):", self.probability_input)
        self.layout.addRow("Trigger Number (player's chosen number):", self.trigger_number_input)
        self.layout.addRow("Damage Dice (e.g., 1d20):", self.dice_input)
        self.layout.addRow("Flat Bonus (e.g., +1):", self.flat_bonus_input)
        self.layout.addRow("Damage Type:", self.damage_type_input)
        self.layout.addRow("Media:", self.media_button)
        self.layout.addRow("Current Media:", self.media_display)
        self.layout.addRow(self.applies_group)
        self.submit_button = QPushButton("Save Effect")
        self.submit_button.clicked.connect(self.accept)
        self.layout.addWidget(self.submit_button)
        self.setLayout(self.layout)
    def add_media(self):
        dialog = MediaDialog(self.media_list, self)
        if dialog.exec():
            self.media_list = dialog.get_data()
            self.media_display.setText("\n".join(self.media_list))
    def get_data(self):
        applies = {}
        lost_limbs = [self.lost_limbs_list.item(i).text() for i in range(self.lost_limbs_list.count())]
        if lost_limbs:
            applies['lost_limbs'] = lost_limbs
        broken_limbs = [self.broken_limbs_list.item(i).text() for i in range(self.broken_limbs_list.count())]
        if broken_limbs:
            applies['broken_limbs'] = broken_limbs
        status_effects = []
        for i in range(self.status_effects_list.count()):
            label = self.status_effects_list.item(i).text()
            import re
            m = re.match(r"(.+?) \((\d+)r\)", label)
            if m:
                name, dur = m.groups()
                status_effects.append({'name': name, 'duration': int(dur)})
            else:
                status_effects.append({'name': label, 'duration': None})
        if status_effects:
            applies['status_effects'] = status_effects
        return {
            "name": self.name_input.text(),
            "description": self.desc_input.toPlainText(),
            "probability_dice": self.probability_input.text(),
            "trigger_number": self.trigger_number_input.value(),
            "dice": self.dice_input.text(),
            "flat_bonus": self.flat_bonus_input.value(),
            "damage_type": self.damage_type_input.text(),
            "media": self.media_list,
            "applies": applies
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
        self.form_layout.addRow("Manual Roll:", self.manual_roll_checkbox)
        layout.addLayout(self.form_layout)
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
            self.loot_group.setVisible(True)
        else:
            event = next((e for e in self.parent().data["events"] if e["name"] == event_name), None)
            if event:
                self.dice_input.setText(event["dice"])
                self.dice_input.setEnabled(False)
                self.threshold_input.setValue(event["success_threshold"])
                self.threshold_input.setEnabled(False)
                self.loot_items = [{"name": i} for i in event.get("loot", [])]
                self.loot_display.setText("\n".join([i["name"] for i in self.loot_items]))
                self.loot_group.setVisible(False)
    
    def get_data(self):
        return {
            "entity_name": self.entity_select.currentText(),
            "event_name": self.event_select.currentText(),
            "guardian": self.guardian_select.get_data() if self.guardian_check.isChecked() else None,
            "guardian_type": self.guardian_type.currentText() if self.guardian_check.isChecked() else None,
            "dice": self.dice_input.text(),
            "success_threshold": self.threshold_input.value(),
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

class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                text-align: left;
                font-weight: bold;
                background: #ddd;
                border: none;
                padding: 4px 8px;
            }
            QPushButton:checked {
                background: #ccc;
            }
        """)
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_area.setVisible(True)
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)
        self.toggle_button.toggled.connect(self.content_area.setVisible)
    def layout(self):
        return self.content_layout

class PlayerWindow(QWidget):
    battle_log_update_signal = Signal(list)  # log_entries
    def __init__(self, data, parent=None):
        print('[DEBUG] PlayerWindow.__init__ called')
        super().__init__(parent)
        self.data = data
        self.setWindowTitle('Wasteland Odyssey Player View')  # Unique title for OBS
        self.setWindowFlags(Qt.Window)  # Make window independent without staying on top
        self.setAttribute(Qt.WA_TranslucentBackground)  # Allow transparency
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #FFFFFF;
                margin-top: 1em;
                color: #FFFFFF;
            }
            QGroupBox::title {
                color: #FFFFFF;
            }
        """)
        # self.setFixedSize(600, 800)  # Remove this line to allow resizing
        self.layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        scroll.setWidget(self.content_widget)
        self.layout.addWidget(scroll)
        self.setLayout(self.layout)
        # Remove QGroupBox code and use CollapsibleSection for each section
        self.player_section_widget = CollapsibleSection("Players")
        self.player_section = self.player_section_widget.layout()
        self.enemy_section_widget = CollapsibleSection("Enemies")
        self.enemy_section = self.enemy_section_widget.layout()
        self.event_section_widget = CollapsibleSection("Event")
        self.event_section = self.event_section_widget.layout()
        self.location_section_widget = CollapsibleSection("Location")
        self.location_section = self.location_section_widget.layout()

        self.content_layout.addWidget(self.player_section_widget)
        self.content_layout.addWidget(self.enemy_section_widget)
        self.content_layout.addWidget(self.event_section_widget)
        self.content_layout.addWidget(self.location_section_widget)
        print('[DEBUG] PlayerWindow widgets created')

        # ... in PlayerWindow.__init__ ...
        self.battle_log_section_widget = CollapsibleSection("Battle Log")
        self.battle_log_section = self.battle_log_section_widget.layout()
        self.content_layout.addWidget(self.battle_log_section_widget)

        self.event_section_widget.setVisible(True)
        self.battle_log_section_widget.setVisible(False)

        # In PlayerWindow.__init__:
        self.battle_log_view_start_time = None

        # Add this line at the class level:
        self.battle_log_update_signal.connect(self.show_battle_log)

        # In PlayerWindow.__init__:
        self.battle_log_list = QListWidget()
        self.battle_log_section_widget.layout().addWidget(self.battle_log_list)
        self.battle_log_view_start_index = 0

    def update_display(self, player_ids=None, enemy_ids=None, event_id=None):
        print(f'[DEBUG] PlayerWindow.update_display called with player_ids={player_ids}, enemy_ids={enemy_ids}, event_id={event_id}')
        players = self.data.get('players', [])
        enemies = self.data.get('enemies', [])
        events = self.data.get('events', [])
        items = self.data.get('items', [])
        weapons = self.data.get('weapons', [])
        armor_list = self.data.get('armor', [])
        selected_players = [p for p in players if p.get('id') in (player_ids or [])]
        selected_enemies = [e for e in enemies if e.get('id') in (enemy_ids or [])]
        event = next((ev for ev in events if ev.get('id') == event_id), {'name': 'Generic Battle', 'description': 'Standard combat encounter.', 'media': []})
        # Clear all sections
        for section in [self.player_section, self.enemy_section, self.event_section, self.location_section]:
            while section.count():
                item = section.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()
        # Players
        if not selected_players:
            placeholder = QLabel('No players selected')
            placeholder.setStyleSheet('font-weight: bold; color: #888;')
            placeholder.setWordWrap(True)
            self.player_section.addWidget(placeholder)
        for player in selected_players:
            header = QLabel(f'Player: {player.get("name", "")}')
            header.setStyleSheet('font-weight: bold; font-size: 14pt;')
            header.setWordWrap(True)
            self.player_section.addWidget(header)
            desc_label = QLabel(f"Description: {player.get('description', '')}")
            desc_label.setWordWrap(True)
            self.player_section.addWidget(desc_label)
            # Media
            mlist = player.get('media', [])
            if mlist:
                img = next((m for m in mlist if m.lower().endswith(('.png', '.jpg', '.jpeg'))), None)
                if img and os.path.exists(img):
                    media = QLabel()
                    pixmap = QPixmap(img).scaled(100, 100, Qt.KeepAspectRatio)
                    media.setPixmap(pixmap)
                    self.player_section.addWidget(media)
            # Stats
            stats = player.get('stats', {})
            stat_str = f"HP: {stats.get('hp', 0)}  AC: {player.get('ac', 0)}\nSTR: {stats.get('strength', 0)}  AGI: {stats.get('agility', 0)}  ENG: {stats.get('engineering', 0)}  INT: {stats.get('intelligence', 0)}  LUCK: {stats.get('luck', 0)}"
            stat_label = QLabel(stat_str)
            stat_label.setWordWrap(True)
            self.player_section.addWidget(stat_label)
            # Equipment
            eq = player.get('equipment', {})
            # Weapon
            weapon_id = eq.get('weapon', '')
            weapon = next((w for w in weapons if w['id'] == weapon_id), None) if weapon_id else None
            if weapon:
                wlabel = f"Weapon: {weapon.get('name', weapon_id)} (Damage: {weapon.get('damage_dice', '')}, Hit Mod: {weapon.get('hit_modifier', 0)})"
            else:
                wlabel = f"Weapon: {weapon_id or 'None'}"
            weapon_label = QLabel(wlabel)
            weapon_label.setWordWrap(True)
            self.player_section.addWidget(weapon_label)
            # Armor
            armor_id = eq.get('armor', '')
            armor = next((a for a in armor_list if a['id'] == armor_id), None) if armor_id else None
            if armor:
                dr = armor.get('damage_resistance', {})
                dr_str = ', '.join(f"{k}: {v}" for k, v in dr.items()) if dr else ''
                alabel = f"Armor: {armor.get('name', armor_id)} (Hit Mod: {armor.get('hit_modifier', 0)}, DR: {dr_str})"
            else:
                alabel = f"Armor: {armor_id or 'None'}"
            armor_label = QLabel(alabel)
            armor_label.setWordWrap(True)
            self.player_section.addWidget(armor_label)
            # Items
            item_ids = eq.get('items', [])
            if item_ids:
                items_label = QLabel("Items:")
                items_label.setWordWrap(True)
                self.player_section.addWidget(items_label)
                for iid in item_ids:
                    item = next((i for i in items if i['id'] == iid), None)
                    if item:
                        ilabel = f"- {item.get('name', iid)} (Type: {item.get('type', '')}, Hit Mod: {item.get('hit_modifier', '')}, Desc: {item.get('description', '')})"
                    else:
                        ilabel = f"- {iid}"
                    item_label = QLabel(ilabel)
                    item_label.setWordWrap(True)
                    self.player_section.addWidget(item_label)
            else:
                items_none_label = QLabel("Items: None")
                items_none_label.setWordWrap(True)
                self.player_section.addWidget(items_none_label)
            # Buffs
            buffs = player.get('buffs', [])
            buffs_label = QLabel(f"Buffs: {', '.join([b['name'] for b in buffs if isinstance(b, dict)])}")
            buffs_label.setWordWrap(True)
            self.player_section.addWidget(buffs_label)
            # Location
            location_label = QLabel(f"Location: {player.get('location', '')} / {player.get('sub_location', '')}")
            location_label.setWordWrap(True)
            self.player_section.addWidget(location_label)
            # Custom fields
            cf = player.get('custom_fields', {})
            if cf:
                custom_label = QLabel(f"Custom: {cf}")
                custom_label.setWordWrap(True)
                self.player_section.addWidget(custom_label)
        # Enemies
        if not selected_enemies:
            placeholder = QLabel('No enemies selected')
            placeholder.setStyleSheet('font-weight: bold; color: #888;')
            placeholder.setWordWrap(True)
            self.enemy_section.addWidget(placeholder)
        for enemy in selected_enemies:
            header = QLabel(f'Enemy: {enemy.get("name", "")}')
            header.setStyleSheet('font-weight: bold; font-size: 14pt;')
            header.setWordWrap(True)
            self.enemy_section.addWidget(header)
            desc_label = QLabel(f"Description: {enemy.get('description', '')}")
            desc_label.setWordWrap(True)
            self.enemy_section.addWidget(desc_label)
            mlist = enemy.get('media', [])
            if mlist:
                img = next((m for m in mlist if m.lower().endswith(('.png', '.jpg', '.jpeg'))), None)
                if img and os.path.exists(img):
                    media = QLabel()
                    pixmap = QPixmap(img).scaled(100, 100, Qt.KeepAspectRatio)
                    media.setPixmap(pixmap)
                    self.enemy_section.addWidget(media)
            stats = enemy.get('stats', {})
            stat_str = f"HP: {stats.get('hp', 0)}  AC: {enemy.get('ac', 0)}\nSTR: {stats.get('strength', 0)}  AGI: {stats.get('agility', 0)}  ENG: {stats.get('engineering', 0)}  INT: {stats.get('intelligence', 0)}  LUCK: {stats.get('luck', 0)}"
            stat_label = QLabel(stat_str)
            stat_label.setWordWrap(True)
            self.enemy_section.addWidget(stat_label)
            eq = enemy.get('equipment', {})
            # Weapon
            weapon_id = eq.get('weapon', '')
            weapon = next((w for w in weapons if w['id'] == weapon_id), None) if weapon_id else None
            if weapon:
                wlabel = f"Weapon: {weapon.get('name', weapon_id)} (Damage: {weapon.get('damage_dice', '')}, Hit Mod: {weapon.get('hit_modifier', 0)})"
            else:
                wlabel = f"Weapon: {weapon_id or 'None'}"
            weapon_label = QLabel(wlabel)
            weapon_label.setWordWrap(True)
            self.enemy_section.addWidget(weapon_label)
            # Armor
            armor_id = eq.get('armor', '')
            armor = next((a for a in armor_list if a['id'] == armor_id), None) if armor_id else None
            if armor:
                dr = armor.get('damage_resistance', {})
                dr_str = ', '.join(f"{k}: {v}" for k, v in dr.items()) if dr else ''
                alabel = f"Armor: {armor.get('name', armor_id)} (Hit Mod: {armor.get('hit_modifier', 0)}, DR: {dr_str})"
            else:
                alabel = f"Armor: {armor_id or 'None'}"
            armor_label = QLabel(alabel)
            armor_label.setWordWrap(True)
            self.enemy_section.addWidget(armor_label)
            # Items
            item_ids = eq.get('items', [])
            if item_ids:
                items_label = QLabel("Items:")
                items_label.setWordWrap(True)
                self.enemy_section.addWidget(items_label)
                for iid in item_ids:
                    item = next((i for i in items if i['id'] == iid), None)
                    if item:
                        ilabel = f"- {item.get('name', iid)} (Type: {item.get('type', '')}, Hit Mod: {item.get('hit_modifier', '')}, Desc: {item.get('description', '')})"
                    else:
                        ilabel = f"- {iid}"
                    item_label = QLabel(ilabel)
                    item_label.setWordWrap(True)
                    self.enemy_section.addWidget(item_label)
            else:
                items_none_label = QLabel("Items: None")
                items_none_label.setWordWrap(True)
                self.enemy_section.addWidget(items_none_label)
            buffs = enemy.get('buffs', [])
            buffs_label = QLabel(f"Buffs: {', '.join([b['name'] for b in buffs if isinstance(b, dict)])}")
            buffs_label.setWordWrap(True)
            self.enemy_section.addWidget(buffs_label)
            location_label = QLabel(f"Location: {enemy.get('location', '')} / {enemy.get('sub_location', '')}")
            location_label.setWordWrap(True)
            self.enemy_section.addWidget(location_label)
            cf = enemy.get('custom_fields', {})
            if cf:
                custom_label = QLabel(f"Custom: {cf}")
                custom_label.setWordWrap(True)
                self.enemy_section.addWidget(custom_label)
        # Event section
        if event.get('name', '') == 'Generic Battle':
            event_header = QLabel('Generic Battle: Standard combat encounter.')
            event_header.setStyleSheet('font-weight: bold; font-size: 14pt;')
            event_header.setWordWrap(True)
            self.event_section.addWidget(event_header)
        else:
            event_header = QLabel(f"Event: {event.get('name', '')}")
            event_header.setStyleSheet('font-weight: bold; font-size: 14pt;')
            event_header.setWordWrap(True)
            self.event_section.addWidget(event_header)
            desc_label = QLabel(f"Description: {event.get('description', '')}")
            desc_label.setWordWrap(True)
            self.event_section.addWidget(desc_label)
            event_media_list = event.get('media', [])
            if event_media_list:
                img = next((m for m in event_media_list if m.lower().endswith(('.png', '.jpg', '.jpeg'))), None)
                if img and os.path.exists(img):
                    media = QLabel()
                    pixmap = QPixmap(img).scaled(100, 100, Qt.KeepAspectRatio)
                    media.setPixmap(pixmap)
                    self.event_section.addWidget(media)
            else:
                media_list_label = QLabel(str(event_media_list))
                media_list_label.setWordWrap(True)
                self.event_section.addWidget(media_list_label)
        print(f'[DEBUG] PlayerWindow updated: players={[p.get("name") for p in selected_players]}, enemies={[e.get("name") for e in selected_enemies]}, event={event.get("name")}')

        if event_id is not None:
            self.event_section_widget.setVisible(True)
            self.battle_log_section_widget.setVisible(False)

    def show_battle_log(self, log_entries):
        self.battle_log_list.clear()
        for i, entry in enumerate(log_entries):
            if i >= self.battle_log_view_start_index:
                text = entry.get('details', '')
                item = QListWidgetItem()
                label = QLabel(text)
                label.setWordWrap(True)
                label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                # Force the label to use the list's width
                width = self.battle_log_list.viewport().width() - 30  # Add some padding
                label.setFixedWidth(width)
                # Adjust item height based on wrapped text
                height = label.heightForWidth(width)
                item.setSizeHint(QSize(width, height))
                self.battle_log_list.addItem(item)
                self.battle_log_list.setItemWidget(item, label)
        self.event_section_widget.setVisible(False)
        self.battle_log_section_widget.setVisible(True)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Update all label widths when window is resized
        width = self.battle_log_list.viewport().width() - 30
        for i in range(self.battle_log_list.count()):
            item = self.battle_log_list.item(i)
            label = self.battle_log_list.itemWidget(item)
            if label:
                label.setFixedWidth(width)
                height = label.heightForWidth(width)
                item.setSizeHint(QSize(width, height))

    def clear_battle_log_display(self):
        self.battle_log_view_start_index = len(self.data.get('log', []))
        self.battle_log_list.clear()
        self.battle_log_section_widget.setVisible(True)

    def show_blank(self):
        print('[DEBUG] DiceWindow.show_blank called.')
        self.dice_view.setHtml('<body style="background:#00FF00;"></body>')

# Restore DiceWindow class before WastelandOdysseyGUI
class DiceWindow(QWidget):
    def __init__(self, parent=None):
        print('[DEBUG] DiceWindow.__init__ called')
        super().__init__(parent)
        self.setWindowTitle('Dice Window (OBS Green Screen)')
        self.resize(800, 1200)  # Default size, but allow resizing
        layout = QVBoxLayout(self)
        self.dice_view = QWebEngineView()
        self.dice_view.setStyleSheet('background: #00FF00;')
        layout.addWidget(self.dice_view)
        self.setLayout(layout)
        self.show_blank()
        print('[DEBUG] DiceWindow widgets created')

    def show_dice_url(self, url):
        print(f'[DEBUG] DiceWindow.show_dice_url called with url: {url}')
        try:
            self.dice_view.setUrl(QUrl(url))
            print('[DEBUG] QWebEngineView setUrl called.')
        except Exception as e:
            print(f'[ERROR] Failed to load dice URL: {e}')

    def show_blank(self):
        print('[DEBUG] DiceWindow.show_blank called.')
        self.dice_view.setHtml('<body style="background:#00FF00;"></body>')

class WastelandOdysseyGUI(QMainWindow):
    def __init__(self):
        print('[DEBUG] WastelandOdysseyGUI.__init__ called')
        super().__init__()
        self.setWindowTitle("Wasteland Odyssey GM Tool")
        self.resize(1400, 900)  # Start with a large, resizable window
        try:
            with open("wasteland_odyssey.json", "r") as f:
                self.data = json.load(f)
            print(f'[DEBUG] Loaded data: {self.data.get("players", [])}')
        except FileNotFoundError:
            self.data = {"players": []}
            print('[ERROR] wasteland_odyssey.json not found, starting with empty data')
        # MIGRATION: Move flat stat fields into stats and remove them
        for entity_list in [self.data.get('players', []), self.data.get('enemies', [])]:
            for ent in entity_list:
                if 'stats' not in ent:
                    ent['stats'] = {}
                for stat in ['hp', 'strength', 'agility', 'engineering', 'intelligence', 'luck']:
                    if stat in ent:
                        ent['stats'][stat] = ent[stat]
                        del ent[stat]
        self.current_battle = {"rolls_left": {}}
        self.current_stage = ""  # Track the current combat stage
        self.init_ui()
        self.player_window = PlayerWindow(self.data)
        self.player_window.show()
        self.player_window.update_display()
        print('[DEBUG] PlayerWindow shown and updated')
        self.dice_window = DiceWindow()
        self.dice_window.show()
        print('[DEBUG] DiceWindow shown')
        self.attacker_id = None
        self.selected_weapon = None
        self.selected_target = None
        self.dice_scale = 1.0  # Default dice scale
    
    def init_ui(self):
        print('[DEBUG] WastelandOdysseyGUI.init_ui called')
        # Use a scroll area for the central widget
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)
        self.setCentralWidget(scroll_area)
        layout = QVBoxLayout(central_widget)
        # --- Save/Update All Buttons ---
        top_btn_layout = QHBoxLayout()
        self.save_all_btn = QPushButton('Save All')
        self.refresh_all_btn = QPushButton('Refresh All')
        self.load_json_btn = QPushButton('Load JSON')
        top_btn_layout.addWidget(self.save_all_btn)
        top_btn_layout.addWidget(self.refresh_all_btn)
        top_btn_layout.addWidget(self.load_json_btn)
        layout.addLayout(top_btn_layout)
        def do_save_all():
            self.save_json()
            QMessageBox.information(self, 'Save Complete', 'All changes saved to wasteland_odyssey.json!')
        self.save_all_btn.clicked.connect(do_save_all)
        def do_refresh_all():
            self.update_tables()
            self.sync_selection_widgets()
            if hasattr(self, 'update_playerwindow_selection_from_control'):
                self.update_playerwindow_selection_from_control()
        self.refresh_all_btn.clicked.connect(do_refresh_all)
        def do_load_json():
            file_path, _ = QFileDialog.getOpenFileName(self, "Load JSON File", "", "JSON Files (*.json)")
            if file_path:
                try:
                    with open(file_path, "r") as f:
                        self.data = json.load(f)
                    QMessageBox.information(self, 'Load Complete', f'Loaded data from {file_path}')
                    self.update_tables()
                    self.sync_selection_widgets()
                    if hasattr(self, 'update_playerwindow_selection_from_control'):
                        self.update_playerwindow_selection_from_control()
                except Exception as e:
                    QMessageBox.critical(self, 'Load Failed', f'Failed to load JSON: {e}')
        self.load_json_btn.clicked.connect(do_load_json)
        # Create tab widget
        tabs = QTabWidget()
        # --- Combat tab ---
        combat_tab = QWidget()
        combat_layout = QVBoxLayout()
        # --- COMBAT CONTROLS LAYOUT REWORK (move all into combat tab) ---
        combat_controls_layout = QHBoxLayout()
        # Multi-select lists for players and enemies
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QListWidget.MultiSelection)
        for p in self.data.get('players', []):
            item = QListWidgetItem(p.get('name', p.get('id', '')))
            item.setData(Qt.UserRole, p.get('id'))
            self.player_list.addItem(item)
        self.enemy_list = QListWidget()
        self.enemy_list.setSelectionMode(QListWidget.MultiSelection)
        for e in self.data.get('enemies', []):
            item = QListWidgetItem(e.get('name', e.get('id', '')))
            item.setData(Qt.UserRole, e.get('id'))
            self.enemy_list.addItem(item)
        self.event_select = QComboBox()
        self.event_select.addItem('Generic Battle')
        self.event_select.addItems([ev.get('name', ev.get('id', '')) for ev in self.data.get('events', [])])
        # --- Attacker/Weapon/Target Selection ---
        attacker_group = QGroupBox("Attackers")
        attacker_layout = QVBoxLayout()
        self.attacker_list = QListWidget()
        self.attacker_list.setSelectionMode(QListWidget.MultiSelection)
        for p in self.data.get('players', []):
            item = QListWidgetItem(f"Player: {p.get('name', p.get('id', ''))}")
            item.setData(Qt.UserRole, ('player', p.get('id')))
            self.attacker_list.addItem(item)
        for e in self.data.get('enemies', []):
            item = QListWidgetItem(f"Enemy: {e.get('name', e.get('id', ''))}")
            item.setData(Qt.UserRole, ('enemy', e.get('id')))
            self.attacker_list.addItem(item)
        attacker_layout.addWidget(QLabel("Select one or more attackers:"))
        attacker_layout.addWidget(self.attacker_list)
        attacker_group.setLayout(attacker_layout)
        # --- ADD THIS LINE ---
        self.attacker_list.itemSelectionChanged.connect(self.update_weapon_select)
        # ---------------------
        # Weapon selection for selected attacker
        weapon_group = QGroupBox("Weapon")
        weapon_layout = QVBoxLayout()
        self.weapon_select = QComboBox()
        weapon_layout.addWidget(QLabel("Weapon for selected attacker:"))
        weapon_layout.addWidget(self.weapon_select)
        weapon_group.setLayout(weapon_layout)
        # Target selection
        target_group = QGroupBox("Target")
        target_layout = QVBoxLayout()
        self.target_select = QComboBox()
        for p in self.data.get('players', []):
            self.target_select.addItem(f"Player: {p.get('name', p.get('id', ''))}", ('player', p.get('id')))
        for e in self.data.get('enemies', []):
            self.target_select.addItem(f"Enemy: {e.get('name', e.get('id', ''))}", ('enemy', e.get('id')))
        target_layout.addWidget(QLabel("Select target:"))
        target_layout.addWidget(self.target_select)
        target_group.setLayout(target_layout)
        # --- Combat Stages Group (move to right) ---
        self.combat_stage_group = QGroupBox("Combat Stages")
        self.combat_stage_layout = QVBoxLayout()
        from PySide6.QtWidgets import QRadioButton
        self.stage_attack = QRadioButton("Attack Roll")
        self.stage_crit = QRadioButton("Crit Check")
        self.stage_special = QRadioButton("Special Effects")
        self.stage_damage = QRadioButton("Damage Roll")
        self.combat_stage_layout.addWidget(self.stage_attack)
        self.combat_stage_layout.addWidget(self.stage_crit)
        self.combat_stage_layout.addWidget(self.stage_special)
        self.combat_stage_layout.addWidget(self.stage_damage)
        self.combat_stage_group.setLayout(self.combat_stage_layout)
        # Add Manual Mode checkbox above dice controls
        self.manual_mode_checkbox = QCheckBox("Manual Mode (Freeform Dice)")
        self.manual_mode_checkbox.setChecked(False)
        manual_mode_layout = QHBoxLayout()
        manual_mode_layout.addWidget(QLabel("Manual Mode:"))
        manual_mode_layout.addWidget(self.manual_mode_checkbox)
        combat_layout.addLayout(manual_mode_layout)
        # Add all to the horizontal combat_controls_layout
        combat_controls_layout.addWidget(attacker_group, 2)
        combat_controls_layout.addWidget(weapon_group, 1)
        combat_controls_layout.addWidget(target_group, 2)
        combat_controls_layout.addWidget(self.combat_stage_group, 1)
        # Add the combat_controls_layout to the combat tab layout
        combat_layout.addLayout(combat_controls_layout)
        # --- DICE CONTROLS ---
        dice_controls = QHBoxLayout()
        self.dice_input = QLineEdit()
        self.dice_input.setPlaceholderText('Enter dice (e.g. 1d20, 2d6+3, 1d20 5d6 3d8+2)')
        self.dice_input.setEnabled(True)
        self.dice_scale_label = QLabel("Scale: 1.0")
        self.dice_scale_minus = QPushButton("−")
        self.dice_scale_plus = QPushButton("+")
        self.dice_scale_minus.setFixedWidth(30)
        self.dice_scale_plus.setFixedWidth(30)
        self.dice_scale_minus.clicked.connect(self.decrease_dice_scale)
        self.dice_scale_plus.clicked.connect(self.increase_dice_scale)
        dice_controls.addWidget(QLabel('Dice:'))
        dice_controls.addWidget(self.dice_input)
        dice_controls.addWidget(self.dice_scale_minus)
        dice_controls.addWidget(self.dice_scale_label)
        dice_controls.addWidget(self.dice_scale_plus)
        self.dice_notes = QLineEdit()
        self.dice_notes.setPlaceholderText("Notes, modifiers, influences (e.g. +2 Buff, -1 Cover, Special Ammo, etc.)")
        dice_controls.addWidget(self.dice_notes)
        self.throw_dice_btn = QPushButton('Throw Dice')
        self.throw_dice_btn.clicked.connect(self.throw_dice)
        dice_controls.addWidget(self.throw_dice_btn)
        self.clear_dice_btn = QPushButton('Clear Dice')
        self.clear_dice_btn.clicked.connect(self.clear_dice_result)
        dice_controls.addWidget(self.clear_dice_btn)
        combat_layout.addLayout(dice_controls)
        # --- Dice Results Table (editable, below dice input) ---
        self.dice_results_table = QTableWidget(0, 4)
        self.dice_results_table.setHorizontalHeaderLabels(["Dice Notation", "Roll Total (Editable)", "Submit/Update", "Reroll"])
        self.dice_results_table.setEditTriggers(QTableWidget.AllEditTriggers)
        combat_layout.addWidget(self.dice_results_table)
        # --- Battle log ---
        battle_log_group = QGroupBox("Battle Log")
        battle_log_layout = QVBoxLayout()
        self.battle_log = QTextEdit()
        self.battle_log.setReadOnly(True)
        battle_log_layout.addWidget(self.battle_log)
        battle_log_group.setLayout(battle_log_layout)
        combat_layout.addWidget(battle_log_group)
        combat_tab.setLayout(combat_layout)
        tabs.addTab(combat_tab, "Combat")
        # --- Players tab ---
        players_tab = QWidget()
        players_layout = QVBoxLayout()
        players_controls = QHBoxLayout()
        self.add_player_btn = QPushButton('Add Player')
        self.edit_player_btn = QPushButton('Edit Player')
        self.delete_player_btn = QPushButton('Delete Player')
        players_controls.addWidget(self.add_player_btn)
        players_controls.addWidget(self.edit_player_btn)
        players_controls.addWidget(self.delete_player_btn)
        players_layout.addLayout(players_controls)
        self.players_table = QTableWidget()
        self.players_table.setColumnCount(8)
        self.players_table.setHorizontalHeaderLabels(["Name", "HP", "AC", "Strength", "Agility", "Engineering", "Intelligence", "Luck"])
        players_layout.addWidget(self.players_table)
        self.inventory_group = QGroupBox("Selected Player Inventory & Equipment")
        inventory_layout = QVBoxLayout()
        self.inventory_info = QLabel("Select a player to view inventory.")
        inventory_layout.addWidget(self.inventory_info)
        self.inventory_list = QListWidget()
        inventory_layout.addWidget(self.inventory_list)
        self.equip_weapon_btn = QPushButton("Equip Selected as Weapon")
        self.equip_armor_btn = QPushButton("Equip Selected as Armor")
        self.use_consumable_btn = QPushButton("Use Consumable")
        self.remove_item_btn = QPushButton("Remove from Inventory")
        self.add_item_btn = QPushButton("Add Item")
        self.add_weapon_btn = QPushButton("Add Weapon")
        self.add_armor_btn = QPushButton("Add Armor")
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.equip_weapon_btn)
        btn_layout.addWidget(self.equip_armor_btn)
        btn_layout.addWidget(self.use_consumable_btn)
        btn_layout.addWidget(self.remove_item_btn)
        inventory_layout.addLayout(btn_layout)
        add_btn_layout = QHBoxLayout()
        add_btn_layout.addWidget(self.add_item_btn)
        add_btn_layout.addWidget(self.add_weapon_btn)
        add_btn_layout.addWidget(self.add_armor_btn)
        inventory_layout.addLayout(add_btn_layout)
        self.inventory_group.setLayout(inventory_layout)
        players_layout.addWidget(self.inventory_group)
        self.inventory_group.setVisible(False)
        players_tab.setLayout(players_layout)
        tabs.addTab(players_tab, "Players")
        # --- Enemies tab ---
        enemies_tab = QWidget()
        enemies_layout = QVBoxLayout()
        enemies_controls = QHBoxLayout()
        self.add_enemy_btn = QPushButton('Add Enemy')
        self.edit_enemy_btn = QPushButton('Edit Enemy')
        self.delete_enemy_btn = QPushButton('Delete Enemy')
        enemies_controls.addWidget(self.add_enemy_btn)
        enemies_controls.addWidget(self.edit_enemy_btn)
        enemies_controls.addWidget(self.delete_enemy_btn)
        enemies_layout.addLayout(enemies_controls)
        self.enemies_table = QTableWidget()
        self.enemies_table.setColumnCount(8)
        self.enemies_table.setHorizontalHeaderLabels(["Name", "HP", "AC", "Strength", "Agility", "Engineering", "Intelligence", "Luck"])
        enemies_layout.addWidget(self.enemies_table)
        
        # Add inventory management for enemies
        self.enemy_inventory_group = QGroupBox("Selected Enemy Inventory & Equipment")
        enemy_inventory_layout = QVBoxLayout()
        self.enemy_inventory_info = QLabel("Select an enemy to view inventory.")
        enemy_inventory_layout.addWidget(self.enemy_inventory_info)
        self.enemy_inventory_list = QListWidget()
        enemy_inventory_layout.addWidget(self.enemy_inventory_list)
        self.enemy_equip_weapon_btn = QPushButton("Equip Selected as Weapon")
        self.enemy_equip_armor_btn = QPushButton("Equip Selected as Armor")
        self.enemy_use_consumable_btn = QPushButton("Use Consumable")
        self.enemy_remove_item_btn = QPushButton("Remove from Inventory")
        self.enemy_add_item_btn = QPushButton("Add Item")
        self.enemy_add_weapon_btn = QPushButton("Add Weapon")
        self.enemy_add_armor_btn = QPushButton("Add Armor")
        enemy_btn_layout = QHBoxLayout()
        enemy_btn_layout.addWidget(self.enemy_equip_weapon_btn)
        enemy_btn_layout.addWidget(self.enemy_equip_armor_btn)
        enemy_btn_layout.addWidget(self.enemy_use_consumable_btn)
        enemy_btn_layout.addWidget(self.enemy_remove_item_btn)
        enemy_inventory_layout.addLayout(enemy_btn_layout)
        enemy_add_btn_layout = QHBoxLayout()
        enemy_add_btn_layout.addWidget(self.enemy_add_item_btn)
        enemy_add_btn_layout.addWidget(self.enemy_add_weapon_btn)
        enemy_add_btn_layout.addWidget(self.enemy_add_armor_btn)
        enemy_inventory_layout.addLayout(enemy_add_btn_layout)
        self.enemy_inventory_group.setLayout(enemy_inventory_layout)
        enemies_layout.addWidget(self.enemy_inventory_group)
        self.enemy_inventory_group.setVisible(False)
        
        enemies_tab.setLayout(enemies_layout)
        tabs.addTab(enemies_tab, "Enemies")
        # --- Events tab ---
        events_tab = QWidget()
        events_layout = QVBoxLayout()
        events_controls = QHBoxLayout()
        self.add_event_btn = QPushButton('Add Event')
        self.edit_event_btn = QPushButton('Edit Event')
        self.delete_event_btn = QPushButton('Delete Event')
        events_controls.addWidget(self.add_event_btn)
        events_controls.addWidget(self.edit_event_btn)
        events_controls.addWidget(self.delete_event_btn)
        events_layout.addLayout(events_controls)
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(4)
        self.events_table.setHorizontalHeaderLabels(["Name", "Dice", "Success Threshold", "Description"])
        events_layout.addWidget(self.events_table)
        events_tab.setLayout(events_layout)
        tabs.addTab(events_tab, "Events")
        # --- Items tab ---
        items_tab = QWidget()
        items_layout = QVBoxLayout()
        items_controls = QHBoxLayout()
        self.add_item_btn2 = QPushButton('Add Item')
        self.edit_item_btn = QPushButton('Edit Item')
        self.delete_item_btn = QPushButton('Delete Item')
        items_controls.addWidget(self.add_item_btn2)
        items_controls.addWidget(self.edit_item_btn)
        items_controls.addWidget(self.delete_item_btn)
        items_layout.addLayout(items_controls)
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Name", "Type", "Hit Modifier", "Description"])
        items_layout.addWidget(self.items_table)
        items_tab.setLayout(items_layout)
        tabs.addTab(items_tab, "Items")
        # --- Weapons tab ---
        weapons_tab = QWidget()
        weapons_layout = QVBoxLayout()
        weapons_controls = QHBoxLayout()
        self.add_weapon_btn2 = QPushButton('Add Weapon')
        self.edit_weapon_btn2 = QPushButton('Edit Weapon')
        self.delete_weapon_btn2 = QPushButton('Delete Weapon')
        weapons_controls.addWidget(self.add_weapon_btn2)
        weapons_controls.addWidget(self.edit_weapon_btn2)
        weapons_controls.addWidget(self.delete_weapon_btn2)
        weapons_layout.addLayout(weapons_controls)
        self.weapons_table = QTableWidget()
        self.weapons_table.setColumnCount(5)
        self.weapons_table.setHorizontalHeaderLabels(["Name", "Damage Dice", "Hit Modifier", "Description", "Special Effects"])
        weapons_layout.addWidget(self.weapons_table)
        weapons_tab.setLayout(weapons_layout)
        tabs.addTab(weapons_tab, "Weapons")
        # --- Armor tab ---
        armor_tab = QWidget()
        armor_layout = QVBoxLayout()
        armor_controls = QHBoxLayout()
        self.add_armor_btn = QPushButton('Add Armor')
        self.edit_armor_btn = QPushButton('Edit Armor')
        self.delete_armor_btn = QPushButton('Delete Armor')
        armor_controls.addWidget(self.add_armor_btn)
        armor_controls.addWidget(self.edit_armor_btn)
        armor_controls.addWidget(self.delete_armor_btn)
        armor_layout.addLayout(armor_controls)
        self.armor_table = QTableWidget()
        self.armor_table.setColumnCount(4)
        self.armor_table.setHorizontalHeaderLabels(["Name", "Hit Modifier", "Damage Resistance", "Description"])
        armor_layout.addWidget(self.armor_table)
        armor_tab.setLayout(armor_layout)
        tabs.addTab(armor_tab, "Armor")
        # --- Locations tab ---
        locations_tab = QWidget()
        locations_layout = QVBoxLayout()
        locations_controls = QHBoxLayout()
        self.add_location_btn = QPushButton('Add Location')
        self.edit_location_btn = QPushButton('Edit Location')
        self.delete_location_btn = QPushButton('Delete Location')
        locations_controls.addWidget(self.add_location_btn)
        locations_controls.addWidget(self.edit_location_btn)
        locations_controls.addWidget(self.delete_location_btn)
        locations_layout.addLayout(locations_controls)
        self.locations_table = QTableWidget()
        self.locations_table.setColumnCount(2)
        self.locations_table.setHorizontalHeaderLabels(["Name", "Description"])
        locations_layout.addWidget(self.locations_table)
        locations_tab.setLayout(locations_layout)
        tabs.addTab(locations_tab, "Locations")
        # --- NPCs tab ---
        npcs_tab = QWidget()
        npcs_layout = QVBoxLayout()
        npcs_controls = QHBoxLayout()
        self.add_npc_btn = QPushButton('Add NPC')
        self.edit_npc_btn = QPushButton('Edit NPC')
        self.delete_npc_btn = QPushButton('Delete NPC')
        npcs_controls.addWidget(self.add_npc_btn)
        npcs_controls.addWidget(self.edit_npc_btn)
        npcs_controls.addWidget(self.delete_npc_btn)
        npcs_layout.addLayout(npcs_controls)
        self.npcs_table = QTableWidget()
        self.npcs_table.setColumnCount(2)
        self.npcs_table.setHorizontalHeaderLabels(["Name", "Description"])
        npcs_layout.addWidget(self.npcs_table)
        npcs_tab.setLayout(npcs_layout)
        tabs.addTab(npcs_tab, "NPCs")
        # --- Vendors tab ---
        vendors_tab = QWidget()
        vendors_layout = QVBoxLayout()
        vendors_controls = QHBoxLayout()
        self.add_vendor_btn = QPushButton('Add Vendor')
        self.edit_vendor_btn = QPushButton('Edit Vendor')
        self.delete_vendor_btn = QPushButton('Delete Vendor')
        vendors_controls.addWidget(self.add_vendor_btn)
        vendors_controls.addWidget(self.edit_vendor_btn)
        vendors_controls.addWidget(self.delete_vendor_btn)
        vendors_layout.addLayout(vendors_controls)
        self.vendors_table = QTableWidget()
        self.vendors_table.setColumnCount(2)
        self.vendors_table.setHorizontalHeaderLabels(["Name", "Description"])
        vendors_layout.addWidget(self.vendors_table)
        vendors_tab.setLayout(vendors_layout)
        tabs.addTab(vendors_tab, "Vendors")
        # --- Miscellaneous tab ---
        misc_tab = QWidget()
        misc_layout = QVBoxLayout()
        misc_controls = QHBoxLayout()
        self.add_misc_btn = QPushButton('Add Misc')
        self.edit_misc_btn = QPushButton('Edit Misc')
        self.delete_misc_btn = QPushButton('Delete Misc')
        misc_controls.addWidget(self.add_misc_btn)
        misc_controls.addWidget(self.edit_misc_btn)
        misc_controls.addWidget(self.delete_misc_btn)
        misc_layout.addLayout(misc_controls)
        self.misc_table = QTableWidget()
        self.misc_table.setColumnCount(2)
        self.misc_table.setHorizontalHeaderLabels(["Name", "Description"])
        misc_layout.addWidget(self.misc_table)
        misc_tab.setLayout(misc_layout)
        tabs.addTab(misc_tab, "Miscellaneous")
        # --- Log tab ---
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Timestamp", "Category", "Details"])
        log_layout.addWidget(self.log_table)
        log_tab.setLayout(log_layout)
        tabs.addTab(log_tab, "Log")
        # --- Display Control tab ---
        display_tab = QWidget()
        display_layout = QVBoxLayout()
        # Players
        display_layout.addWidget(QLabel('Players:'))
        self.display_players_list = QListWidget()
        self.display_players_list.setSelectionMode(QListWidget.MultiSelection)
        for player in self.data.get('players', []):
            item = QListWidgetItem(player.get('name', player.get('id', 'Unknown')))
            item.setData(Qt.UserRole, player['id'])
            self.display_players_list.addItem(item)
        display_layout.addWidget(self.display_players_list)
        # Enemies
        display_layout.addWidget(QLabel('Enemies:'))
        self.display_enemies_list = QListWidget()
        self.display_enemies_list.setSelectionMode(QListWidget.MultiSelection)
        for enemy in self.data.get('enemies', []):
            item = QListWidgetItem(enemy.get('name', enemy.get('id', 'Unknown')))
            item.setData(Qt.UserRole, enemy['id'])
            self.display_enemies_list.addItem(item)
        display_layout.addWidget(self.display_enemies_list)
        # Items
        display_layout.addWidget(QLabel('Items:'))
        self.display_items_list = QListWidget()
        self.display_items_list.setSelectionMode(QListWidget.MultiSelection)
        for item_data in self.data.get('items', []):
            item = QListWidgetItem(item_data.get('name', item_data.get('id', 'Unknown')))
            item.setData(Qt.UserRole, item_data['id'])
            self.display_items_list.addItem(item)
        display_layout.addWidget(self.display_items_list)
        # Events
        display_layout.addWidget(QLabel('Events:'))
        self.display_events_list = QListWidget()
        self.display_events_list.setSelectionMode(QListWidget.MultiSelection)
        for event in self.data.get('events', []):
            item = QListWidgetItem(event.get('name', event.get('id', 'Unknown')))
            item.setData(Qt.UserRole, event['id'])
            self.display_events_list.addItem(item)
        display_layout.addWidget(self.display_events_list)
        # Show button
        self.display_show_btn = QPushButton('Show Selection in Player Window')
        self.display_show_btn.clicked.connect(self.update_playerwindow_selection_from_control)
        display_layout.addWidget(self.display_show_btn)
        # Add a button to show the battle log in the Player Window
        self.display_show_battle_log_btn = QPushButton('Show Battle Log in Player Window')
        self.display_show_battle_log_btn.clicked.connect(self.show_battle_log_in_player_window)
        display_layout.addWidget(self.display_show_battle_log_btn)
        # Add a button to clear the battle log display in the Player Window
        self.display_clear_battle_log_btn = QPushButton('Clear Battle Log View')
        self.display_clear_battle_log_btn.setToolTip('This only clears the current view. The full log is always saved.')
        self.display_clear_battle_log_btn.clicked.connect(self.clear_battle_log_in_player_window)
        display_layout.addWidget(self.display_clear_battle_log_btn)
        display_tab.setLayout(display_layout)
        tabs.addTab(display_tab, 'Display Control')
        layout.addWidget(tabs)
        # Restore all signal/slot connections for tab controls
        self.players_table.cellClicked.connect(self.show_player_inventory)
        self.add_player_btn.clicked.connect(self.add_player_dialog)
        self.edit_player_btn.clicked.connect(self.edit_player_dialog)
        self.delete_player_btn.clicked.connect(self.delete_player)
        self.players_table.cellDoubleClicked.connect(self.edit_player_dialog)
        self.add_item_btn.clicked.connect(self.add_item_to_player)
        self.add_weapon_btn.clicked.connect(self.add_weapon_to_player)
        self.add_armor_btn.clicked.connect(self.add_armor_to_player)
        self.remove_item_btn.clicked.connect(self.remove_item_from_player)
        self.equip_weapon_btn.clicked.connect(self.equip_weapon_for_player)
        self.equip_armor_btn.clicked.connect(self.equip_armor_for_player)
        self.use_consumable_btn.clicked.connect(self.use_consumable_for_player)

        # Add enemy inventory button connections
        self.enemies_table.cellClicked.connect(self.show_enemy_inventory)
        self.enemy_add_item_btn.clicked.connect(self.add_item_to_enemy)
        self.enemy_add_weapon_btn.clicked.connect(self.add_weapon_to_enemy)
        self.enemy_add_armor_btn.clicked.connect(self.add_armor_to_enemy)
        self.enemy_remove_item_btn.clicked.connect(self.remove_item_from_enemy)
        self.enemy_equip_weapon_btn.clicked.connect(self.equip_weapon_for_enemy)
        self.enemy_equip_armor_btn.clicked.connect(self.equip_armor_for_enemy)
        self.enemy_use_consumable_btn.clicked.connect(self.use_consumable_for_enemy)

        self.add_enemy_btn.clicked.connect(self.add_enemy_dialog)
        self.edit_enemy_btn.clicked.connect(self.edit_enemy_dialog)
        self.delete_enemy_btn.clicked.connect(self.delete_enemy)
        self.enemies_table.cellDoubleClicked.connect(self.edit_enemy_dialog)
        self.add_event_btn.clicked.connect(self.add_event_dialog)
        self.edit_event_btn.clicked.connect(self.edit_event_dialog)
        self.delete_event_btn.clicked.connect(self.delete_event)
        self.events_table.cellDoubleClicked.connect(self.edit_event_dialog)
        self.add_item_btn2.clicked.connect(self.add_item_dialog)
        self.edit_item_btn.clicked.connect(self.edit_item_dialog)
        self.delete_item_btn.clicked.connect(self.delete_item)
        self.items_table.cellDoubleClicked.connect(self.edit_item_dialog)
        self.add_armor_btn.clicked.connect(self.add_armor_dialog)
        self.edit_armor_btn.clicked.connect(self.edit_armor_dialog)
        self.delete_armor_btn.clicked.connect(self.delete_armor)
        self.armor_table.cellDoubleClicked.connect(self.edit_armor_dialog)
        self.add_location_btn.clicked.connect(self.add_location_dialog)
        self.edit_location_btn.clicked.connect(self.edit_location_dialog)
        self.delete_location_btn.clicked.connect(self.delete_location)
        self.locations_table.cellDoubleClicked.connect(self.edit_location_dialog)
        self.add_npc_btn.clicked.connect(self.add_npc_dialog)
        self.edit_npc_btn.clicked.connect(self.edit_npc_dialog)
        self.delete_npc_btn.clicked.connect(self.delete_npc)
        self.npcs_table.cellDoubleClicked.connect(self.edit_npc_dialog)
        self.add_vendor_btn.clicked.connect(self.add_vendor_dialog)
        self.edit_vendor_btn.clicked.connect(self.edit_vendor_dialog)
        self.delete_vendor_btn.clicked.connect(self.delete_vendor)
        self.vendors_table.cellDoubleClicked.connect(self.edit_vendor_dialog)
        self.add_misc_btn.clicked.connect(self.add_misc_dialog)
        self.edit_misc_btn.clicked.connect(self.edit_misc_dialog)
        self.delete_misc_btn.clicked.connect(self.delete_misc)
        self.misc_table.cellDoubleClicked.connect(self.edit_misc_dialog)
        # Initialize tables
        self.update_tables()
        self.stage_attack.toggled.connect(self.handle_stage_attack)
        self.stage_crit.toggled.connect(self.handle_stage_crit)
        self.stage_special.toggled.connect(self.handle_stage_special)
        self.stage_damage.toggled.connect(self.handle_stage_damage)
        self.manual_mode_checkbox.stateChanged.connect(self.handle_manual_mode)
        self.add_weapon_btn2.clicked.connect(self.add_weapon_dialog)
        self.edit_weapon_btn2.clicked.connect(self.edit_weapon_dialog)
        self.delete_weapon_btn2.clicked.connect(self.delete_weapon)
        self.weapons_table.cellDoubleClicked.connect(self.edit_weapon_dialog)
        # ... after each QTableWidget is created in init_ui() ...
        self.players_table.cellChanged.connect(self.handle_player_table_edit)
        self.enemies_table.cellChanged.connect(self.handle_enemy_table_edit)
        self.events_table.cellChanged.connect(self.handle_event_table_edit)
        self.items_table.cellChanged.connect(self.handle_item_table_edit)
        self.weapons_table.cellChanged.connect(self.handle_weapon_table_edit)
        self.armor_table.cellChanged.connect(self.handle_armor_table_edit)
        self.npcs_table.cellChanged.connect(self.handle_npc_table_edit)
        self.vendors_table.cellChanged.connect(self.handle_vendor_table_edit)
        self.misc_table.cellChanged.connect(self.handle_misc_table_edit)
        self.locations_table.cellChanged.connect(self.handle_location_table_edit)
    
    def update_tables(self):
        # Update players table
        self.players_table.setRowCount(len(self.data.get("players", [])))
        for i, player in enumerate(self.data.get("players", [])):
            self.players_table.setItem(i, 0, QTableWidgetItem(player.get("name", "")))
            self.players_table.setItem(i, 1, QTableWidgetItem(str(player.get("stats", {}).get("hp", 0))))
            self.players_table.setItem(i, 2, QTableWidgetItem(str(player.get("ac", 0))))
            self.players_table.setItem(i, 3, QTableWidgetItem(str(player.get("stats", {}).get("strength", 0))))
            self.players_table.setItem(i, 4, QTableWidgetItem(str(player.get("stats", {}).get("agility", 0))))
            self.players_table.setItem(i, 5, QTableWidgetItem(str(player.get("stats", {}).get("engineering", 0))))
            self.players_table.setItem(i, 6, QTableWidgetItem(str(player.get("stats", {}).get("intelligence", 0))))
            self.players_table.setItem(i, 7, QTableWidgetItem(str(player.get("stats", {}).get("luck", 0))))
        
        # Update enemies table
        self.enemies_table.setRowCount(len(self.data.get("enemies", [])))
        for i, enemy in enumerate(self.data.get("enemies", [])):
            self.enemies_table.setItem(i, 0, QTableWidgetItem(enemy.get("name", "")))
            self.enemies_table.setItem(i, 1, QTableWidgetItem(str(enemy.get("stats", {}).get("hp", 0))))
            self.enemies_table.setItem(i, 2, QTableWidgetItem(str(enemy.get("ac", 0))))
            self.enemies_table.setItem(i, 3, QTableWidgetItem(str(enemy.get("stats", {}).get("strength", 0))))
            self.enemies_table.setItem(i, 4, QTableWidgetItem(str(enemy.get("stats", {}).get("agility", 0))))
            self.enemies_table.setItem(i, 5, QTableWidgetItem(str(enemy.get("stats", {}).get("engineering", 0))))
            self.enemies_table.setItem(i, 6, QTableWidgetItem(str(enemy.get("stats", {}).get("intelligence", 0))))
            self.enemies_table.setItem(i, 7, QTableWidgetItem(str(enemy.get("stats", {}).get("luck", 0))))
        
        # Update events table
        self.events_table.setRowCount(len(self.data.get("events", [])))
        for i, event in enumerate(self.data.get("events", [])):
            self.events_table.setItem(i, 0, QTableWidgetItem(event.get("name", "")))
            self.events_table.setItem(i, 1, QTableWidgetItem(event.get("dice", "")))
            self.events_table.setItem(i, 2, QTableWidgetItem(str(event.get("success_threshold", 0))))
            self.events_table.setItem(i, 3, QTableWidgetItem(event.get("description", "")))
        
        # Update items table
        self.items_table.setRowCount(0)
        for item in self.data.get("items", []):
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            self.items_table.setItem(row, 1, QTableWidgetItem(item.get("type", "")))
            self.items_table.setItem(row, 2, QTableWidgetItem(str(item.get("hit_modifier", 0))))
            self.items_table.setItem(row, 3, QTableWidgetItem(item.get("description", "")))
        
        # Update log table
        self.log_table.setRowCount(len(self.data.get("log", [])))
        for i, entry in enumerate(self.data.get("log", [])):
            self.log_table.setItem(i, 0, QTableWidgetItem(entry.get("timestamp", "")))
            self.log_table.setItem(i, 1, QTableWidgetItem(entry.get("category", "")))
            self.log_table.setItem(i, 2, QTableWidgetItem(entry.get("details", "")))
        
        # Update weapons table
        self.weapons_table.setRowCount(0)
        for weapon in self.data.get("weapons", []):
            row = self.weapons_table.rowCount()
            self.weapons_table.insertRow(row)
            self.weapons_table.setItem(row, 0, QTableWidgetItem(weapon.get("name", "")))
            self.weapons_table.setItem(row, 1, QTableWidgetItem(weapon.get("damage_dice", "")))
            self.weapons_table.setItem(row, 2, QTableWidgetItem(str(weapon.get("hit_modifier", 0))))
            self.weapons_table.setItem(row, 3, QTableWidgetItem(weapon.get("description", "")))
            # Special Effects as string
            special = weapon.get("special_effects", [])
            if special:
                special_str = ", ".join([f"{e.get('name', '')} ({e.get('dice', '')})" for e in special])
            else:
                special_str = ""
            self.weapons_table.setItem(row, 4, QTableWidgetItem(special_str))
    
        # Update armor table
        self.armor_table.setRowCount(0)
        for armor in self.data.get("armor", []):
            row = self.armor_table.rowCount()
            self.armor_table.insertRow(row)
            self.armor_table.setItem(row, 0, QTableWidgetItem(armor.get("name", "")))
            self.armor_table.setItem(row, 1, QTableWidgetItem(str(armor.get("hit_modifier", 0))))
            # Damage Resistance as string
            dr = armor.get("damage_resistance", {})
            if dr:
                dr_str = ", ".join(f"{k}: {v}" for k, v in dr.items())
            else:
                dr_str = ""
            self.armor_table.setItem(row, 2, QTableWidgetItem(dr_str))
            self.armor_table.setItem(row, 3, QTableWidgetItem(armor.get("description", "")))
    
    def save_json(self):
        with open("wasteland_odyssey.json", "w") as f:
            json.dump(self.data, f, indent=2)
    
    def roll_for_attack(self):
        if not self.selected_weapon or not self.attacker_id:
            QMessageBox.warning(self, "Error", "Select an attacker and weapon.")
            return
        
        target_dialog = EnemySelectionDialog(self.data.get("enemies", []), self)
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
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
            prob = effect.get('probability', 1.0)
            triggered = True
            if prob < 1.0:
                prob_dialog = ManualRollDialog("1d4", f"Enter {effect['name']} Probability Roll (1d4, 1 triggers)", self)
                if prob_dialog.exec():
                    prob_result = prob_dialog.get_data()["total"]
                    triggered = (prob_result == 1)
                else:
                    triggered = False
            if triggered:
                total_damage = 0
                # If dice is present, roll for it
                if effect.get("dice"):
                    damage_dialog = ManualRollDialog(effect["dice"], f"Enter {effect['name']} Damage Roll ({effect['dice']})", self)
                    if damage_dialog.exec():
                        damage_result = damage_dialog.get_data()["total"]
                        total_damage += damage_result
                        effect_roll_entry = {
                            "id": f"roll_{len(self.data.get('dice_rolls', [])) + 1:03d}",
                            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
                # Add flat_bonus if present
                flat_bonus = effect.get("flat_bonus", 0)
                if flat_bonus:
                    total_damage += flat_bonus
                # Only add if there is any damage
                if total_damage:
                    special_damages.append({"type": effect.get("damage_type", "special"), "amount": total_damage})
        
        # Calculate hit modifier
        attacker = next((p for p in self.data["players"] if p["id"] == self.attacker_id), 
                       next((e for e in self.data["enemies"] if e["id"] == self.attacker_id), {}))
        target = next((p for p in self.data["players"] if p["id"] == self.selected_target), 
                     next((e for e in self.data["enemies"] if e["id"] == self.selected_target), {}))
        hit_modifier = self.calculate_hit_modifier(attacker, weapon, None)
        
        # Body part targeting
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
        
        # Damage calculation
        damage_dice = weapon.get("damage_dice", "1d4")
        damage_dialog = ManualRollDialog(damage_dice, f"Enter Damage Roll ({damage_dice})", self)
        if damage_dialog.exec():
            damage_result = damage_dialog.get_data()["total"]
            damage_roll_entry = {
                "id": f"roll_{len(self.data.get('dice_rolls', [])) + 1:03d}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
        
        # Environmental effects (keep this part)
        location = next((loc for loc in self.data["locations"] if loc["id"] == attacker["location"]), {})
        sub_location = next((subloc for subloc in location.get("sub_locations", []) if subloc["id"] == attacker["sub_location"]), {})
        env_effects = sub_location.get("environmental_effects", location.get("environmental_effects", {}))
        env_damage = 0
        if "radiation" in env_effects:
            rad = env_effects["radiation"]
            env_damage = max(0, rad["damage"] - int(rad["scale_factor"] * target["stats"].get(rad["scale_stat"], 0)))

        # --- Gather all resistances and vulnerabilities from armor, items, buffs ---
        def gather_resists_vulns(target, dtype, bypass_armor=False):
            total_resist = 0
            total_vuln = 0
            details = []
            # Armor
            armor = next((a for a in self.data["armor"] if a["id"] == target.get("equipment", {}).get("armor")), {})
            if not bypass_armor and armor:
                for k, v in armor.get("damage_resistance", {}).items():
                    if k == dtype:
                        total_resist += v
                        details.append(f"Armor({armor.get('name','')} {dtype} RES:{v})")
                for k, v in armor.get("resistances", {}).items():
                    if k == dtype:
                        total_resist += v
                        details.append(f"Armor({armor.get('name','')} {dtype} RES:{v})")
                for k, v in armor.get("vulnerabilities", {}).items():
                    if k == dtype:
                        total_vuln += v
                        details.append(f"Armor({armor.get('name','')} {dtype} VULN:{v})")
            # Items
            for item_id in target.get("equipment", {}).get("items", []):
                item = next((i for i in self.data.get("items", []) if i["id"] == item_id), None)
                if item:
                    for k, v in item.get("resistances", {}).items():
                        if k == dtype:
                            total_resist += v
                            details.append(f"Item({item.get('name','')} {dtype} RES:{v})")
                    for k, v in item.get("vulnerabilities", {}).items():
                        if k == dtype:
                            total_vuln += v
                            details.append(f"Item({item.get('name','')} {dtype} VULN:{v})")
            # Buffs
            for buff in target.get("buffs", []):
                if not isinstance(buff, dict):
                    continue
                for k, v in buff.get("resistances", {}).items():
                    if k == dtype:
                        total_resist += v
                        details.append(f"Buff({buff.get('name','')} {dtype} RES:{v})")
                for k, v in buff.get("vulnerabilities", {}).items():
                    if k == dtype:
                        total_vuln += v
                        details.append(f"Buff({buff.get('name','')} {dtype} VULN:{v})")
            return total_resist, total_vuln, details

        # --- Apply resistances/vulnerabilities to each damage type ---
        damage_breakdown = []
        total_final_damage = 0
        # Base physical damage
        base_type = "physical"
        base_bypass = False
        base_resist, base_vuln, base_details = gather_resists_vulns(target, base_type, base_bypass)
        final_base_damage = max(0, damage - base_resist + base_vuln)
        if damage > 0:
            damage_breakdown.append(f"{final_base_damage} {base_type} (raw:{damage}, -{base_resist} RES, +{base_vuln} VULN; {'; '.join(base_details)})")
        total_final_damage += final_base_damage
        # Radiation damage
        rad_type = "radiation"
        rad_bypass = False
        rad_resist, rad_vuln, rad_details = gather_resists_vulns(target, rad_type, rad_bypass)
        final_rad_damage = max(0, radiation_damage - rad_resist + rad_vuln)
        if radiation_damage > 0:
            damage_breakdown.append(f"{final_rad_damage} {rad_type} (raw:{radiation_damage}, -{rad_resist} RES, +{rad_vuln} VULN; {'; '.join(rad_details)})")
        total_final_damage += final_rad_damage
        # Special damages
        for s in special_damages:
            dtype = s.get("type", "special")
            amount = s.get("amount", 0)
            bypass = s.get("bypass_armor", False)
            resist, vuln, details = gather_resists_vulns(target, dtype, bypass)
            final_special = max(0, amount - resist + vuln)
            damage_breakdown.append(f"{final_special} {dtype} (raw:{amount}, -{resist} RES, +{vuln} VULN; {'; '.join(details)}){' (bypassed armor)' if bypass else ''}")
            total_final_damage += final_special
        # Environmental damage (leave as-is for now)
        if env_damage > 0:
            damage_breakdown.append(f"{env_damage} environmental")
            total_final_damage += env_damage

        # --- DEBUG: Print special damages and breakdowns ---
        print(f"[DEBUG] special_damages: {special_damages}")

        # --- Apply resistances/vulnerabilities to each damage type ---
        damage_breakdown = []
        total_final_damage = 0
        # Base physical damage
        base_type = "physical"
        base_bypass = False
        base_resist, base_vuln, base_details = gather_resists_vulns(target, base_type, base_bypass)
        final_base_damage = max(0, damage - base_resist + base_vuln)
        if damage > 0:
            damage_breakdown.append(f"{final_base_damage} {base_type} (raw:{damage}, -{base_resist} RES, +{base_vuln} VULN; {'; '.join(base_details)})")
        total_final_damage += final_base_damage
        # Radiation damage
        rad_type = "radiation"
        rad_bypass = False
        rad_resist, rad_vuln, rad_details = gather_resists_vulns(target, rad_type, rad_bypass)
        final_rad_damage = max(0, radiation_damage - rad_resist + rad_vuln)
        if radiation_damage > 0:
            damage_breakdown.append(f"{final_rad_damage} {rad_type} (raw:{radiation_damage}, -{rad_resist} RES, +{rad_vuln} VULN; {'; '.join(rad_details)})")
        total_final_damage += final_rad_damage
        # Special damages
        for s in special_damages:
            dtype = s.get("type", "special")
            amount = s.get("amount", 0)
            bypass = s.get("bypass_armor", False)
            resist, vuln, details = gather_resists_vulns(target, dtype, bypass)
            final_special = max(0, amount - resist + vuln)
            damage_breakdown.append(f"{final_special} {dtype} (raw:{amount}, -{resist} RES, +{vuln} VULN; {'; '.join(details)}){' (bypassed armor)' if bypass else ''}")
            total_final_damage += final_special
        # Environmental damage (leave as-is for now)
        if env_damage > 0:
            damage_breakdown.append(f"{env_damage} environmental")
            total_final_damage += env_damage

        # --- DEBUG: Print breakdown and total ---
        print(f"[DEBUG] damage_breakdown: {damage_breakdown}")
        print(f"[DEBUG] total_final_damage: {total_final_damage}")

        # Dodge check
        dodge_chance = target_armor.get("dodge_modifier", 0) + sum(b["effect"].get("dodge_chance", 0) for b in target.get("buffs", []))
        dodge_roll = random.randint(1, 20)
        hit_success = (int(attack_result) + hit_modifier >= target["ac"]) and (dodge_roll / 20 > dodge_chance)
        
        # Update target HP
        if hit_success:
            target["stats"]["hp"] = max(0, target["stats"]["hp"] - total_final_damage)
        
        # Log battle (show breakdown)
        weapon_name = weapon.get('name', 'Unknown Weapon')
        log_details = (
            f"{attacker['name']} attacks {target['name']} with {weapon_name}: "
            f"{attack_result} + {hit_modifier} vs AC {target['ac']} => {'HIT' if hit_success else 'MISS'} {hit_body_part} "
            f"for {total_final_damage} total damage. Breakdown: {' | '.join(damage_breakdown)}"
        )
        print(f"[DEBUG] log_details: {log_details}")
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "category": "battle",
            "details": log_details
        }
        self.data["log"].append(log_entry)
        # Update PlayerWindow battle log view if visible
        if hasattr(self, 'player_window') and self.player_window is not None:
            if self.player_window.battle_log_section_widget.isVisible():
                self.player_window.battle_log_update_signal.emit(self.data['log'])
        
        # Update buff durations
        self.update_buff_durations(attacker, "rolls")
        
        self.save_json()
        self.update_log()
        self.battle_log.setText(log_details)
        self.update_display(roll_url=roll_url)
        self.update_playerwindow_battle_log_view()
        print(f'[DEBUG] Appending log entry: {log_entry}')
        self.data["log"].append(log_entry)
        if hasattr(self, 'player_window') and self.player_window is not None:
            print('[DEBUG] Emitting battle_log_update_signal')
            self.player_window.battle_log_update_signal.emit(self.data['log'])
        entry_index = len(self.data['log']) - 1
        if hasattr(self, 'player_window') and self.player_window is not None:
            self.player_window.battle_log_update_signal.emit(self.data['log'][entry_index], entry_index)
    
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
                    "puzzle_type": event_data.get("puzzle_type", "stat-based"),
                    "puzzle_content": event_data.get("puzzle_content", {"type": "text", "value": ""})
                }
                self.data["events"].append(event)
            
            # Handle guardian
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
                    # Simulate battle (simplified; reuse roll_for_attack logic)
                    self.attacker_id = entity["id"]
                    self.selected_weapon = entity["equipment"].get("weapon")
                    self.selected_target = guardian_id
                    self.body_part_select.setCurrentText("torso")
                    self.roll_for_attack()
                    guardian_entity = next((e for e in self.data["enemies"] if e["id"] == guardian_id), {})
                    guardian_success = guardian_entity["stats"]["hp"] <= 0
                elif event_data["guardian_type"] == "puzzle":
                    # Handle puzzle event
                    puzzle_event = {
                        "id": f"event_{len(self.data['events']) + 1:03d}",
                        "name": f"Puzzle for {event['name']}",
                        "description": "Solve the puzzle to proceed",
                        "dice": "1d20",
                        "success_threshold": 15,
                        "stat_bonuses": ["intelligence", "engineering"],
                        "loot": [],
                        "media": [],
                        "puzzle_type": event.get("puzzle_type", "stat-based"),
                        "puzzle_content": event.get("puzzle_content", {"type": "text", "value": "Solve this puzzle"})
                    }
                    self.data["events"].append(puzzle_event)
                    guardian_success = self.process_event_roll(entity, puzzle_event, event_data["buffs"], event_data["manual_roll"])
            
            if not guardian_success:
                log_entry = {
                    "id": f"log_{len(self.data['log']) + 1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "category": "event",
                    "details": f"{entity['name']} failed guardian challenge for {event['name']}"
                }
                self.data["log"].append(log_entry)
                self.save_json()
                self.update_log()
                self.event_log.setText(log_entry["details"])
                self.update_display()
                return
            
            # Process main event
            success = self.process_event_roll(entity, event, event_data["buffs"], event_data["manual_roll"])
            
            # Handle loot
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
            
            log_details = (f"{entity['name']} rolled {event['dice']} for {event['name']}, "
                          f"{'Succeeded' if success else 'Failed'}.")
            log_entry = {
                "id": f"log_{len(self.data['log']) + 1:03d}",
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "category": "event",
                "details": log_details
            }
            self.data["log"].append(log_entry)
            # Update PlayerWindow battle log view if visible
            if hasattr(self, 'player_window') and self.player_window is not None:
                if self.player_window.battle_log_section_widget.isVisible():
                    self.player_window.battle_log_update_signal.emit(self.data['log'])
            # Update buff durations
            self.update_buff_durations(entity, "rolls")
            self.save_json()
            self.update_log()
            self.event_log.setText(log_details)
            roll_url = f"http://dice.bee.ac/?dicehex=4E1E78&labelhex=CC9EEC&chromahex=00FF00&d={event['dice']}&roll&resultsize=24"
            self.update_display(roll_url=roll_url)
            self.update_playerwindow_battle_log_view()
            print(f'[DEBUG] Appending log entry: {log_entry}')
            self.data["log"].append(log_entry)
            if hasattr(self, 'player_window') and self.player_window is not None:
                print('[DEBUG] Emitting battle_log_update_signal')
                self.player_window.battle_log_update_signal.emit(self.data['log'])
            entry_index = len(self.data['log']) - 1
            if hasattr(self, 'player_window') and self.player_window is not None:
                self.player_window.battle_log_update_signal.emit(self.data['log'][entry_index], entry_index)
    
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
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
        
        # Environmental effects
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
        
        for buff in buffs:
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

    def add_player_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Player')
        layout = QFormLayout(dialog)
        name = QLineEdit()
        hp = QSpinBox(); hp.setRange(0, 999)
        ac = QSpinBox(); ac.setRange(0, 99)
        strength = QSpinBox(); strength.setRange(0, 99)
        agility = QSpinBox(); agility.setRange(0, 99)
        engineering = QSpinBox(); engineering.setRange(0, 99)
        intelligence = QSpinBox(); intelligence.setRange(0, 99)
        luck = QSpinBox(); luck.setRange(0, 99)
        layout.addRow('Name:', name)
        layout.addRow('HP:', hp)
        layout.addRow('AC:', ac)
        layout.addRow('Strength:', strength)
        layout.addRow('Agility:', agility)
        layout.addRow('Engineering:', engineering)
        layout.addRow('Intelligence:', intelligence)
        layout.addRow('Luck:', luck)
        btn = QPushButton('Add')
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        if dialog.exec():
            player = {
                'id': f"player_{len(self.data.get('players', [])) + 1:03d}",
                'name': name.text(),
                'stats': {
                    'hp': hp.value(),
                    'strength': strength.value(),
                    'agility': agility.value(),
                    'engineering': engineering.value(),
                    'intelligence': intelligence.value(),
                    'luck': luck.value()
                },
                'ac': ac.value(),
                'equipment': {'weapon': '', 'armor': '', 'items': []},
                'buffs': [],
                'location': '',
                'sub_location': ''
            }
            self.data.setdefault('players', []).append(player)
            self.save_json()
            self.player_window.update_display()  # Update PlayerWindow after adding

    def edit_player_dialog(self, row=None, col=None):
        if row is None:
            row = self.players_table.currentRow()
        if row < 0:
            return
        player = self.data['players'][row]
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Player')
        layout = QFormLayout(dialog)
        name = QLineEdit(player.get('name', ''))
        hp = QSpinBox(); hp.setRange(0, 999); hp.setValue(player.get('hp', 0))
        ac = QSpinBox(); ac.setRange(0, 99); ac.setValue(player.get('ac', 0))
        strength = QSpinBox(); strength.setRange(0, 99); strength.setValue(player.get('strength', 0))
        agility = QSpinBox(); agility.setRange(0, 99); agility.setValue(player.get('agility', 0))
        engineering = QSpinBox(); engineering.setRange(0, 99); engineering.setValue(player.get('engineering', 0))
        intelligence = QSpinBox(); intelligence.setRange(0, 99); intelligence.setValue(player.get('intelligence', 0))
        luck = QSpinBox(); luck.setRange(0, 99); luck.setValue(player.get('luck', 0))
        layout.addRow('Name:', name)
        layout.addRow('HP:', hp)
        layout.addRow('AC:', ac)
        layout.addRow('Strength:', strength)
        layout.addRow('Agility:', agility)
        layout.addRow('Engineering:', engineering)
        layout.addRow('Intelligence:', intelligence)
        layout.addRow('Luck:', luck)
        btn = QPushButton('Save')
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        if dialog.exec():
            player['name'] = name.text()
            player['stats'] = {
                'hp': hp.value(),
                'strength': strength.value(),
                'agility': agility.value(),
                'engineering': engineering.value(),
                'intelligence': intelligence.value(),
                'luck': luck.value()
            }
            player['ac'] = ac.value()
            self.save_json()
            self.player_window.update_display()  # Update PlayerWindow after editing

    def delete_player(self):
        row = self.players_table.currentRow()
        if row < 0:
            return
        del self.data['players'][row]
        self.save_json()
        self.player_window.update_display()  # Update PlayerWindow after deleting

    def add_enemy_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Enemy')
        layout = QFormLayout(dialog)
        name = QLineEdit()
        hp = QSpinBox(); hp.setRange(0, 999)
        ac = QSpinBox(); ac.setRange(0, 99)
        strength = QSpinBox(); strength.setRange(0, 99)
        agility = QSpinBox(); agility.setRange(0, 99)
        engineering = QSpinBox(); engineering.setRange(0, 99)
        intelligence = QSpinBox(); intelligence.setRange(0, 99)
        luck = QSpinBox(); luck.setRange(0, 99)
        layout.addRow('Name:', name)
        layout.addRow('HP:', hp)
        layout.addRow('AC:', ac)
        layout.addRow('Strength:', strength)
        layout.addRow('Agility:', agility)
        layout.addRow('Engineering:', engineering)
        layout.addRow('Intelligence:', intelligence)
        layout.addRow('Luck:', luck)
        btn = QPushButton('Add')
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        if dialog.exec():
            enemy = {
                'id': f"enemy_{len(self.data.get('enemies', [])) + 1:03d}",
                'name': name.text(),
                'stats': {
                    'hp': hp.value(),
                    'strength': strength.value(),
                    'agility': agility.value(),
                    'engineering': engineering.value(),
                    'intelligence': intelligence.value(),
                    'luck': luck.value()
                },
                'ac': ac.value(),
                'equipment': {'weapon': '', 'armor': '', 'items': []},
                'buffs': [],
                'location': '',
                'sub_location': ''
            }
            self.data.setdefault('enemies', []).append(enemy)
            self.save_json()

    def edit_enemy_dialog(self, row=None, col=None):
        if row is None:
            row = self.enemies_table.currentRow()
        if row < 0:
            return
        enemy = self.data['enemies'][row]
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Enemy')
        layout = QFormLayout(dialog)
        name = QLineEdit(enemy.get('name', ''))
        hp = QSpinBox(); hp.setRange(0, 999); hp.setValue(enemy.get('hp', 0))
        ac = QSpinBox(); ac.setRange(0, 99); ac.setValue(enemy.get('ac', 0))
        strength = QSpinBox(); strength.setRange(0, 99); strength.setValue(enemy.get('strength', enemy.get('stats', {}).get('strength', 0)))
        agility = QSpinBox(); agility.setRange(0, 99); agility.setValue(enemy.get('agility', enemy.get('stats', {}).get('agility', 0)))
        engineering = QSpinBox(); engineering.setRange(0, 99); engineering.setValue(enemy.get('engineering', enemy.get('stats', {}).get('engineering', 0)))
        intelligence = QSpinBox(); intelligence.setRange(0, 99); intelligence.setValue(enemy.get('intelligence', enemy.get('stats', {}).get('intelligence', 0)))
        luck = QSpinBox(); luck.setRange(0, 99); luck.setValue(enemy.get('luck', enemy.get('stats', {}).get('luck', 0)))
        desc = QTextEdit(enemy.get('description', ''))
        layout.addRow('Name:', name)
        layout.addRow('HP:', hp)
        layout.addRow('AC:', ac)
        layout.addRow('Strength:', strength)
        layout.addRow('Agility:', agility)
        layout.addRow('Engineering:', engineering)
        layout.addRow('Intelligence:', intelligence)
        layout.addRow('Luck:', luck)
        layout.addRow('Description:', desc)
        btn = QPushButton('Save')
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        if dialog.exec():
            enemy['name'] = name.text()
            enemy['stats'] = {
                'hp': hp.value(),
                'strength': strength.value(),
                'agility': agility.value(),
                'engineering': engineering.value(),
                'intelligence': intelligence.value(),
                'luck': luck.value()
            }
            enemy['ac'] = ac.value()
            enemy['description'] = desc.toPlainText()
            self.save_json()
            self.update_tables()

    def delete_enemy(self):
        row = self.enemies_table.currentRow()
        if row < 0:
            return
        del self.data['enemies'][row]
        self.save_json()

    def add_event_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Event')
        layout = QFormLayout(dialog)
        name = QLineEdit()
        dice = QLineEdit()
        threshold = QSpinBox(); threshold.setRange(0, 999)
        desc = QTextEdit()
        layout.addRow('Name:', name)
        layout.addRow('Dice:', dice)
        layout.addRow('Success Threshold:', threshold)
        layout.addRow('Description:', desc)
        btn = QPushButton('Add')
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        if dialog.exec():
            event = {
                'id': f"event_{len(self.data.get('events', [])) + 1:03d}",
                'name': name.text(),
                'dice': dice.text(),
                'success_threshold': threshold.value(),
                'description': desc.toPlainText(),
                'stat_bonuses': [],
                'loot': [],
                'media': []
            }
            self.data.setdefault('events', []).append(event)
            self.save_json()

    def edit_event_dialog(self, row=None, col=None):
        if row is None:
            row = self.events_table.currentRow()
        if row < 0:
            return
        event = self.data['events'][row]
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Event')
        layout = QFormLayout(dialog)
        name = QLineEdit(event.get('name', ''))
        dice = QLineEdit(event.get('dice', ''))
        threshold = QSpinBox(); threshold.setRange(0, 999); threshold.setValue(event.get('success_threshold', 0))
        desc = QTextEdit(event.get('description', ''))
        layout.addRow('Name:', name)
        layout.addRow('Dice:', dice)
        layout.addRow('Success Threshold:', threshold)
        layout.addRow('Description:', desc)
        btn = QPushButton('Save')
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        if dialog.exec():
            event['name'] = name.text()
            event['dice'] = dice.text()
            event['success_threshold'] = threshold.value()
            event['description'] = desc.toPlainText()
            self.save_json()

    def delete_event(self):
        row = self.events_table.currentRow()
        if row < 0:
            return
        del self.data['events'][row]
        self.save_json()

    def add_item_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Add Item')
        layout = QFormLayout(dialog)
        name = QLineEdit()
        type_ = QLineEdit()
        hit_mod = QSpinBox(); hit_mod.setRange(-99, 99)
        desc = QTextEdit()
        # --- Resistances with pick-list ---
        all_resistances = set()
        for a in self.data.get('armor', []):
            for k in a.get('resistances', {}).keys():
                all_resistances.add(k)
        for w in self.data.get('weapons', []):
            for eff in w.get('special_effects', []):
                if eff.get('damage_type'):
                    all_resistances.add(eff['damage_type'])
        for i in self.data.get('items', []):
            for k in i.get('resistances', {}).keys():
                all_resistances.add(k)
        for b in self.data.get('buffs', []):
            for k in b.get('resistances', {}).keys():
                all_resistances.add(k)
        all_resistances = sorted(s for s in all_resistances if s)
        resistances = {}
        resist_pick = QComboBox()
        resist_pick.addItem('(Add New Resistance)')
        for r in all_resistances:
            resist_pick.addItem(r)
        resist_list = QListWidget()
        def add_resist():
            idx = resist_pick.currentIndex()
            if idx == 0:
                text, ok = QInputDialog.getText(self, "Add Resistance Type", "Type:")
                if ok and text:
                    resistances[text] = 0
                    resist_list.addItem(f"{text}: 0")
            else:
                t = resist_pick.currentText()
                if t not in resistances:
                    resistances[t] = 0
                    resist_list.addItem(f"{t}: 0")
        add_resist_btn = QPushButton('Add Resistance')
        add_resist_btn.clicked.connect(add_resist)
        def edit_resist():
            idx = resist_list.currentRow()
            if idx >= 0:
                key = list(resistances.keys())[idx]
                val, ok = QInputDialog.getInt(self, "Edit Resistance Value", f"Value for {key}:", resistances[key], -99, 999)
                if ok:
                    resistances[key] = val
                    resist_list.item(idx).setText(f"{key}: {val}")
        edit_resist_btn = QPushButton('Edit Selected Resistance')
        edit_resist_btn.clicked.connect(edit_resist)
        def remove_resist():
            idx = resist_list.currentRow()
            if idx >= 0:
                key = list(resistances.keys())[idx]
                del resistances[key]
                resist_list.takeItem(idx)
        remove_resist_btn = QPushButton('Remove Selected Resistance')
        remove_resist_btn.clicked.connect(remove_resist)
        # --- Vulnerabilities with pick-list ---
        all_vulns = set()
        for a in self.data.get('armor', []):
            for k in a.get('vulnerabilities', {}).keys():
                all_vulns.add(k)
        for w in self.data.get('weapons', []):
            for eff in w.get('special_effects', []):
                if eff.get('damage_type'):
                    all_vulns.add(eff['damage_type'])
        for i in self.data.get('items', []):
            for k in i.get('vulnerabilities', {}).keys():
                all_vulns.add(k)
        for b in self.data.get('buffs', []):
            for k in b.get('vulnerabilities', {}).keys():
                all_vulns.add(k)
        all_vulns = sorted(s for s in all_vulns if s)
        vulnerabilities = {}
        vuln_pick = QComboBox()
        vuln_pick.addItem('(Add New Vulnerability)')
        for v in all_vulns:
            vuln_pick.addItem(v)
        vuln_list = QListWidget()
        def add_vuln():
            idx = vuln_pick.currentIndex()
            if idx == 0:
                text, ok = QInputDialog.getText(self, "Add Vulnerability Type", "Type:")
                if ok and text:
                    vulnerabilities[text] = 0
                    vuln_list.addItem(f"{text}: 0")
            else:
                t = vuln_pick.currentText()
                if t not in vulnerabilities:
                    vulnerabilities[t] = 0
                    vuln_list.addItem(f"{t}: 0")
        add_vuln_btn = QPushButton('Add Vulnerability')
        add_vuln_btn.clicked.connect(add_vuln)
        def edit_vuln():
            idx = vuln_list.currentRow()
            if idx >= 0:
                key = list(vulnerabilities.keys())[idx]
                val, ok = QInputDialog.getInt(self, "Edit Vulnerability Value", f"Value for {key}:", vulnerabilities[key], -99, 999)
                if ok:
                    vulnerabilities[key] = val
                    vuln_list.item(idx).setText(f"{key}: {val}")
        edit_vuln_btn = QPushButton('Edit Selected Vulnerability')
        edit_vuln_btn.clicked.connect(edit_vuln)
        def remove_vuln():
            idx = vuln_list.currentRow()
            if idx >= 0:
                key = list(vulnerabilities.keys())[idx]
                del vulnerabilities[key]
                vuln_list.takeItem(idx)
        remove_vuln_btn = QPushButton('Remove Selected Vulnerability')
        remove_vuln_btn.clicked.connect(remove_vuln)
        # --- Special Effects with pick-list (reuse from weapon dialog) ---
        special_btn = QPushButton('Edit Special Effects')
        special_effects = []
        all_specials = set()
        for w in self.data.get('weapons', []):
            for eff in w.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for a in self.data.get('armor', []):
            for eff in a.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for i in self.data.get('items', []):
            for eff in i.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for b in self.data.get('buffs', []):
            for eff in b.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        all_specials = sorted(s for s in all_specials if s)
        special_pick = QComboBox()
        special_pick.addItem('(Add New Special Effect)')
        for s in all_specials:
            special_pick.addItem(s)
        def edit_special():
            idx = special_pick.currentIndex()
            if idx == 0:
                dlg = SpecialEffectDialog(parent=self)
                if dlg.exec():
                    special_effects.append(dlg.get_data())
            else:
                name = special_pick.currentText()
                eff = None
                for w in self.data.get('weapons', []):
                    for e in w.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for a in self.data.get('armor', []):
                    for e in a.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for i in self.data.get('items', []):
                    for e in i.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for b in self.data.get('buffs', []):
                    for e in b.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                if eff:
                    dlg = SpecialEffectDialog(effect=eff, parent=self)
                    if dlg.exec():
                        special_effects.append(dlg.get_data())
        special_btn.clicked.connect(edit_special)
        special_list = QListWidget()
        def refresh_special_list():
            special_list.clear()
            for eff in special_effects:
                special_list.addItem(eff.get('name', ''))
        refresh_special_list()
        remove_special_btn = QPushButton('Remove Selected Special')
        def remove_special():
            idx = special_list.currentRow()
            if idx >= 0:
                special_effects.pop(idx)
                refresh_special_list()
        remove_special_btn.clicked.connect(remove_special)
        # Media
        media_btn = QPushButton('Add Media')
        media_list = []
        def add_media():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Media", "", "Images (*.png *.jpg);;Videos (*.mp4)")
            if file_path:
                media_list.append(file_path)
        media_btn.clicked.connect(add_media)
        layout.addRow('Name:', name)
        layout.addRow('Type:', type_)
        layout.addRow('Hit Modifier:', hit_mod)
        layout.addRow('Description:', desc)
        layout.addRow('Resistances:', resist_pick)
        layout.addRow('', add_resist_btn)
        layout.addRow('Current Resistances:', resist_list)
        layout.addRow('', edit_resist_btn)
        layout.addRow('', remove_resist_btn)
        layout.addRow('Vulnerabilities:', vuln_pick)
        layout.addRow('', add_vuln_btn)
        layout.addRow('Current Vulnerabilities:', vuln_list)
        layout.addRow('', edit_vuln_btn)
        layout.addRow('', remove_vuln_btn)
        layout.addRow('Special Effects:', special_pick)
        layout.addRow('', special_btn)
        layout.addRow('Current Specials:', special_list)
        layout.addRow('', remove_special_btn)
        layout.addRow('Media:', media_btn)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        dialog.setLayout(layout)
        if dialog.exec():
            item = {
                'id': f"item_{len(self.data.get('items', [])) + 1:03d}",
                'name': name.text(),
                'type': type_.text(),
                'hit_modifier': hit_mod.value(),
                'description': desc.toPlainText(),
                'media': media_list,
                'resistances': resistances,
                'vulnerabilities': vulnerabilities,
                'special_effects': special_effects
            }
            self.data.setdefault('items', []).append(item)
            self.save_json()
            self.update_tables()

    def edit_armor_dialog(self, row=None, col=None):
        if row is None:
            row = self.armor_table.currentRow()
        if row < 0:
            return
        armor = self.data['armor'][row]
        dialog = QDialog(self)
        dialog.setWindowTitle('Edit Armor')
        layout = QFormLayout(dialog)
        name = QLineEdit(armor.get('name', ''))
        hit_mod = QSpinBox(); hit_mod.setRange(-99, 99); hit_mod.setValue(armor.get('hit_modifier', 0))
        desc = QTextEdit(armor.get('description', ''))
        name = QLineEdit(weapon.get('name', ''))
        damage_dice = QLineEdit(weapon.get('damage_dice', ''))
        hit_mod = QSpinBox(); hit_mod.setRange(-99, 99); hit_mod.setValue(weapon.get('hit_modifier', 0))
        desc = QTextEdit(weapon.get('description', ''))
        # --- Special Effects with pick-list ---
        special_btn = QPushButton('Edit Special Effects')
        special_effects = list(weapon.get('special_effects', []))
        # Gather all existing special effects for pick-list
        all_specials = set()
        for w in self.data.get('weapons', []):
            for eff in w.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        for a in self.data.get('armor', []):
            for eff in a.get('special_effects', []):
                all_specials.add(eff.get('name', ''))
        all_specials = sorted(s for s in all_specials if s)
        special_pick = QComboBox()
        special_pick.addItem('(Add New Special Effect)')
        for s in all_specials:
            special_pick.addItem(s)
        def edit_special():
            idx = special_pick.currentIndex()
            if idx == 0:
                dlg = SpecialEffectDialog(parent=self)
                if dlg.exec():
                    special_effects.append(dlg.get_data())
            else:
                # Find the effect by name and allow editing
                name = special_pick.currentText()
                eff = None
                for w in self.data.get('weapons', []):
                    for e in w.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                for a in self.data.get('armor', []):
                    for e in a.get('special_effects', []):
                        if e.get('name', '') == name:
                            eff = e
                            break
                if eff:
                    dlg = SpecialEffectDialog(effect=eff, parent=self)
                    if dlg.exec():
                        special_effects.append(dlg.get_data())
        special_btn.clicked.connect(edit_special)
        # Show current selected specials
        special_list = QListWidget()
        def refresh_special_list():
            special_list.clear()
            for eff in special_effects:
                special_list.addItem(eff.get('name', ''))
        refresh_special_list()
        # Remove selected special
        remove_special_btn = QPushButton('Remove Selected Special')
        def remove_special():
            idx = special_list.currentRow()
            if idx >= 0:
                special_effects.pop(idx)
                refresh_special_list()
        remove_special_btn.clicked.connect(remove_special)
        # Media
        media_btn = QPushButton('Add Media')
        media_list = list(weapon.get('media', []))
        def add_media():
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Media", "", "Images (*.png *.jpg);;Videos (*.mp4)")
            if file_path:
                media_list.append(file_path)
        media_btn.clicked.connect(add_media)
        layout.addRow('Name:', name)
        layout.addRow('Damage Dice:', damage_dice)
        layout.addRow('Hit Modifier:', hit_mod)
        layout.addRow('Description:', desc)
        layout.addRow('Special Effects:', special_pick)
        layout.addRow('', special_btn)
        layout.addRow('Current Specials:', special_list)
        layout.addRow('', remove_special_btn)
        layout.addRow('Media:', media_btn)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        dialog.setLayout(layout)
        if dialog.exec():
            weapon['name'] = name.text()
            weapon['damage_dice'] = damage_dice.text()
            weapon['hit_modifier'] = hit_mod.value()
            weapon['description'] = desc.toPlainText()
            weapon['special_effects'] = special_effects
            weapon['media'] = media_list
            self.save_json()
            self.update_tables()

    def delete_weapon(self):
        row = self.weapons_table.currentRow()
        if row < 0 or row >= len(self.data.get('weapons', [])):
            return
        del self.data['weapons'][row]
        self.save_json()
        self.update_tables()

    def update_playerwindow_selection_from_control(self):
        player_ids = [item.data(Qt.UserRole) for item in self.display_players_list.selectedItems()]
        enemy_ids = [item.data(Qt.UserRole) for item in self.display_enemies_list.selectedItems()]
        event_ids = [item.data(Qt.UserRole) for item in self.display_events_list.selectedItems()]
        event_id = event_ids[0] if event_ids else None
        # Only pass arguments PlayerWindow.update_display accepts
        if hasattr(self, 'player_window') and self.player_window is not None:
            self.player_window.update_display(
                player_ids=player_ids,
                enemy_ids=enemy_ids,
                event_id=event_id
            )

    def handle_player_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("players", [])):
            return
        player = self.data["players"][row]
        value = self.players_table.item(row, col).text()
        fields = ["name", "hp", "ac", "strength", "agility", "engineering", "intelligence", "luck"]
        if col >= len(fields):
            return
        field = fields[col]
        if field == "hp":
            player['stats']['hp'] = int(value)
        elif field == "ac":
            player['ac'] = int(value)
        elif field in ["strength", "agility", "engineering", "intelligence", "luck"]:
            player['stats'][field] = int(value)
        elif field == "name":
            player['name'] = value

    def handle_enemy_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("enemies", [])):
            return
        enemy = self.data["enemies"][row]
        value = self.enemies_table.item(row, col).text()
        fields = ["name", "hp", "ac", "strength", "agility", "engineering", "intelligence", "luck"]
        if col >= len(fields):
            return
        field = fields[col]
        if field == "hp":
            enemy['stats']['hp'] = int(value)
        elif field == "ac":
            enemy['ac'] = int(value)
        elif field in ["strength", "agility", "engineering", "intelligence", "luck"]:
            enemy['stats'][field] = int(value)
        elif field == "name":
            enemy['name'] = value

    def handle_event_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("events", [])):
            return
        event = self.data["events"][row]
        value = self.events_table.item(row, col).text()
        fields = ["name", "dice", "success_threshold", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        if field == "success_threshold":
            try:
                value = int(value)
            except ValueError:
                value = 0
        event[field] = value

    def handle_item_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("items", [])):
            return
        item = self.data["items"][row]
        value = self.items_table.item(row, col).text()
        fields = ["name", "type", "hit_modifier", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        if field == "hit_modifier":
            try:
                value = int(value)
            except ValueError:
                value = 0
        item[field] = value

    def handle_weapon_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("weapons", [])):
            return
        weapon = self.data["weapons"][row]
        value = self.weapons_table.item(row, col).text()
        fields = ["name", "damage_dice", "hit_modifier", "description", "special_effects"]
        if col >= len(fields):
            return
        field = fields[col]
        if field == "hit_modifier":
            try:
                value = int(value)
            except ValueError:
                value = 0
        if field == "special_effects":
            # This is a string representation, skip direct editing
            return
        weapon[field] = value

    def handle_armor_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("armor", [])):
            return
        armor = self.data["armor"][row]
        value = self.armor_table.item(row, col).text()
        fields = ["name", "hit_modifier", "damage_resistance", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        if field == "hit_modifier":
            try:
                value = int(value)
            except ValueError:
                value = 0
        if field == "damage_resistance":
            # This is a string representation, skip direct editing
            return
        armor[field] = value

    def handle_npc_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("npcs", [])):
            return
        npc = self.data["npcs"][row]
        value = self.npcs_table.item(row, col).text()
        fields = ["name", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        npc[field] = value

    def handle_vendor_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("vendors", [])):
            return
        vendor = self.data["vendors"][row]
        value = self.vendors_table.item(row, col).text()
        fields = ["name", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        vendor[field] = value

    def handle_misc_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("misc", [])):
            return
        misc = self.data["misc"][row]
        value = self.misc_table.item(row, col).text()
        fields = ["name", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        misc[field] = value

    def handle_location_table_edit(self, row, col):
        if row < 0 or row >= len(self.data.get("locations", [])):
            return
        location = self.data["locations"][row]
        value = self.locations_table.item(row, col).text()
        fields = ["name", "description"]
        if col >= len(fields):
            return
        field = fields[col]
        location[field] = value

    def clear_battle_log_in_player_window(self):
        if hasattr(self, 'player_window') and self.player_window is not None:
            self.player_window.clear_battle_log_display()

    # In WastelandOdysseyGUI, add this method:
    def show_battle_log_in_player_window(self):
        if hasattr(self, 'player_window') and self.player_window is not None:
            self.player_window.battle_log_view_start_index = 0  # Reset to show all logs
            log_entries = self.data.get('log', [])
            self.player_window.battle_log_update_signal.emit(log_entries)

    # ... in WastelandOdysseyGUI, add this method:
    def update_playerwindow_battle_log_view(self):
        if hasattr(self, 'player_window') and self.player_window is not None:
            if self.player_window.battle_log_section_widget.isVisible():
                self.player_window.battle_log_update_signal.emit(self.data['log'])

    # ... after every self.data['log'].append(log_entry) in the file, add:
        self.update_playerwindow_battle_log_view()

    def append_battle_log_entry(self, entry, index):
        if index >= self.battle_log_view_start_index:
            text = f"{entry.get('timestamp', 'Unknown time')}: {entry.get('details', '')}"
            self.battle_log_list.addItem(text)
        self.event_section_widget.setVisible(False)
        self.battle_log_section_widget.setVisible(True)

    def show_enemy_inventory(self, row, col):
        if row < 0 or row >= len(self.data.get('enemies', [])):
            return
        enemy = self.data['enemies'][row]
        self.selected_enemy_idx = row
        self.enemy_inventory_group.setVisible(True)
        # Get equipment info
        eq = enemy.get('equipment', {})
        items = eq.get('items', [])
        weapon_id = eq.get('weapon', '')
        armor_id = eq.get('armor', '')
        # Only count items in 'items' for inventory usage
        inventory_count = len(items)
        limit = enemy.get('inventory_limit', 7)
        # Update info display
        weapon_name = "None"
        if weapon_id:
            weapon = next((w for w in self.data.get('weapons', []) if w['id'] == weapon_id), None)
            if weapon:
                weapon_name = weapon['name']
        armor_name = "None"
        if armor_id:
            armor = next((a for a in self.data.get('armor', []) if a['id'] == armor_id), None)
            if armor:
                armor_name = armor['name']
        self.enemy_inventory_info.setText(f"Inventory ({inventory_count}/{limit}) | Weapon: {weapon_name} | Armor: {armor_name}")
        # Clear and repopulate inventory list
        self.enemy_inventory_list.clear()
        # Add equipped weapon if any
        if weapon_id:
            weapon = next((w for w in self.data.get('weapons', []) if w['id'] == weapon_id), None)
            if weapon:
                self.enemy_inventory_list.addItem(f"[Equipped Weapon] {weapon['name']}")
        # Add equipped armor if any
        if armor_id:
            armor = next((a for a in self.data.get('armor', []) if a['id'] == armor_id), None)
            if armor:
                self.enemy_inventory_list.addItem(f"[Equipped Armor] {armor['name']}")
        # Add items in inventory
        for iid in items:
            item = next((i for i in self.data.get('items', []) if i['id'] == iid), None)
            if item:
                label = f"Item: {item['name']} (Consumable: {'Yes' if item.get('type', '').lower() == 'consumable' else 'No'})"
                self.enemy_inventory_list.addItem(label)
            else:
                weapon = next((w for w in self.data.get('weapons', []) if w['id'] == iid), None)
                if weapon:
                    self.enemy_inventory_list.addItem(f"[Weapon] {weapon['name']}")
                    continue
                armor = next((a for a in self.data.get('armor', []) if a['id'] == iid), None)
                if armor:
                    self.enemy_inventory_list.addItem(f"[Armor] {armor['name']}")
                    continue

    def add_item_to_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        items = self.data.get('items', [])
        if not items:
            QMessageBox.warning(self, "No Items", "No items available to add.")
            return
        item_names = [i['name'] for i in items]
        selected, ok = QInputDialog.getItem(self, "Add Item", "Select Item:", item_names, 0, False)
        if ok:
            item = next((i for i in items if i['name'] == selected), None)
            if not item:
                return
            eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
            limit = enemy.get('inventory_limit', 7)
            inv_count = len(eq.get('items', [])) + (1 if eq.get('weapon') else 0) + (1 if eq.get('armor') else 0)
            if inv_count >= limit:
                QMessageBox.warning(self, "Inventory Full", f"Enemy inventory is full ({inv_count}/{limit}). Remove something first.")
                return
            eq['items'].append(item['id'])
            self.save_json()
            self.show_enemy_inventory(row, 0)

    def add_weapon_to_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        weapons = self.data.get('weapons', [])
        if not weapons:
            QMessageBox.warning(self, "No Weapons", "No weapons available to add.")
            return
        weapon_names = [w['name'] for w in weapons]
        selected, ok = QInputDialog.getItem(self, "Add Weapon", "Select Weapon:", weapon_names, 0, False)
        if ok:
            weapon = next((w for w in weapons if w['name'] == selected), None)
            if not weapon:
                return
            eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
            limit = enemy.get('inventory_limit', 7)
            inv_count = len(eq.get('items', [])) + (1 if eq.get('weapon') else 0) + (1 if eq.get('armor') else 0)
            if inv_count >= limit:
                QMessageBox.warning(self, "Inventory Full", f"Enemy inventory is full ({inv_count}/{limit}). Remove something first.")
                return
            eq['items'].append(weapon['id'])
            self.save_json()
            self.show_enemy_inventory(row, 0)

    def add_armor_to_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        armor_list = self.data.get('armor', [])
        if not armor_list:
            QMessageBox.warning(self, "No Armor", "No armor available to add.")
            return
        armor_names = [a['name'] for a in armor_list]
        selected, ok = QInputDialog.getItem(self, "Add Armor", "Select Armor:", armor_names, 0, False)
        if ok:
            armor = next((a for a in armor_list if a['name'] == selected), None)
            if not armor:
                return
            eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
            limit = enemy.get('inventory_limit', 7)
            inv_count = len(eq.get('items', [])) + (1 if eq.get('weapon') else 0) + (1 if eq.get('armor') else 0)
            if inv_count >= limit:
                QMessageBox.warning(self, "Inventory Full", f"Enemy inventory is full ({inv_count}/{limit}). Remove something first.")
                return
            eq['items'].append(armor['id'])
            self.save_json()
            self.show_enemy_inventory(row, 0)

    def remove_item_from_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        items = eq.get('items', [])
        weapons = self.data.get('weapons', [])
        armor_list = self.data.get('armor', [])
        all_items = items[:]
        if eq.get('weapon'):
            all_items.append(eq['weapon'])
        if eq.get('armor'):
            all_items.append(eq['armor'])
        if not all_items:
            QMessageBox.warning(self, "No Items", "No items, weapons, or armor to remove.")
            return
        name_map = {}
        for iid in all_items:
            item = next((i for i in self.data.get('items', []) if i['id'] == iid), None)
            if item:
                name_map[iid] = f"Item: {item['name']}"
            weapon = next((w for w in weapons if w['id'] == iid), None)
            if weapon:
                name_map[iid] = f"Weapon: {weapon['name']}"
            armor = next((a for a in armor_list if a['id'] == iid), None)
            if armor:
                name_map[iid] = f"Armor: {armor['name']}"
        name_list = [name_map[iid] for iid in all_items]
        selected, ok = QInputDialog.getItem(self, "Remove Item", "Select Item/Weapon/Armor to remove:", name_list, 0, False)
        if ok:
            for iid, label in name_map.items():
                if label == selected:
                    if iid == eq.get('weapon'):
                        eq['weapon'] = ''
                    elif iid == eq.get('armor'):
                        eq['armor'] = ''
                    elif iid in eq['items']:
                        eq['items'].remove(iid)
                    break
            self.save_json()
            self.show_enemy_inventory(row, 0)

    def equip_weapon_for_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        weapons = [iid for iid in eq.get('items', []) if any(w['id'] == iid for w in self.data.get('weapons', []))]
        if not weapons:
            QMessageBox.warning(self, "No Weapons", "No weapons in inventory to equip.")
            return
        weapon_objs = [next(w for w in self.data.get('weapons', []) if w['id'] == iid) for iid in weapons]
        weapon_names = [w['name'] for w in weapon_objs]
        selected, ok = QInputDialog.getItem(self, "Equip Weapon", "Select Weapon to Equip:", weapon_names, 0, False)
        if ok:
            weapon = next((w for w in weapon_objs if w['name'] == selected), None)
            if weapon:
                # If a weapon is already equipped, move it back to items
                if eq.get('weapon'):
                    eq['items'].append(eq['weapon'])
                # Remove the new weapon from items and equip it
                if weapon['id'] in eq['items']:
                    eq['items'].remove(weapon['id'])
                eq['weapon'] = weapon['id']
                self.save_json()
                self.show_enemy_inventory(row, 0)

    def equip_armor_for_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        armor_ids = [iid for iid in eq.get('items', []) if any(a['id'] == iid for a in self.data.get('armor', []))]
        if not armor_ids:
            QMessageBox.warning(self, "No Armor", "No armor in inventory to equip.")
            return
        armor_objs = [next(a for a in self.data.get('armor', []) if a['id'] == iid) for iid in armor_ids]
        armor_names = [a['name'] for a in armor_objs]
        selected, ok = QInputDialog.getItem(self, "Equip Armor", "Select Armor to Equip:", armor_names, 0, False)
        if ok:
            armor = next((a for a in armor_objs if a['name'] == selected), None)
            if armor:
                # If armor is already equipped, move it back to items
                if eq.get('armor'):
                    eq['items'].append(eq['armor'])
                # Remove the new armor from items and equip it
                if armor['id'] in eq['items']:
                    eq['items'].remove(armor['id'])
                eq['armor'] = armor['id']
                self.save_json()
                self.show_enemy_inventory(row, 0)

    def use_consumable_for_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        items = [iid for iid in eq.get('items', []) if next((i for i in self.data.get('items', []) if i['id'] == iid and i.get('type', '').lower() == 'consumable'), None)]
        if not items:
            QMessageBox.warning(self, "No Consumables", "No consumable items in inventory.")
            return
        item_objs = [next(i for i in self.data.get('items', []) if i['id'] == iid) for iid in items]
        item_names = [i['name'] for i in item_objs]
        selected, ok = QInputDialog.getItem(self, "Use Consumable", "Select Consumable to Use:", item_names, 0, False)
        if ok:
            item = next((i for i in item_objs if i['name'] == selected), None)
            if item:
                eq['items'].remove(item['id'])
                log_entry = {
                    "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "category": "consumable",
                    "details": f"{enemy['name']} used consumable: {item['name']}"
                }
                self.data.setdefault('log', []).append(log_entry)
                self.save_json()
                self.show_enemy_inventory(row, 0)
                if hasattr(self, 'player_window') and self.player_window is not None:
                    self.player_window.battle_log_update_signal.emit(self.data['log'])

    def unequip_weapon_for_player(self):
        row = getattr(self, 'selected_player_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Player Selected", "Select a player in the table first.")
            return
        player = self.data['players'][row]
        eq = player.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        if eq.get('weapon'):
            eq['items'].append(eq['weapon'])
            eq['weapon'] = ''
            self.save_json()
            self.show_player_inventory(row, 0)
        else:
            QMessageBox.information(self, "No Weapon Equipped", "No weapon is currently equipped.")

    def unequip_armor_for_player(self):
        row = getattr(self, 'selected_player_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Player Selected", "Select a player in the table first.")
            return
        player = self.data['players'][row]
        eq = player.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        if eq.get('armor'):
            eq['items'].append(eq['armor'])
            eq['armor'] = ''
            self.save_json()
            self.show_player_inventory(row, 0)
        else:
            QMessageBox.information(self, "No Armor Equipped", "No armor is currently equipped.")

    def unequip_weapon_for_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        if eq.get('weapon'):
            eq['items'].append(eq['weapon'])
            eq['weapon'] = ''
            self.save_json()
            self.show_enemy_inventory(row, 0)
        else:
            QMessageBox.information(self, "No Weapon Equipped", "No weapon is currently equipped.")

    def unequip_armor_for_enemy(self):
        row = getattr(self, 'selected_enemy_idx', None)
        if row is None:
            QMessageBox.warning(self, "No Enemy Selected", "Select an enemy in the table first.")
            return
        enemy = self.data['enemies'][row]
        eq = enemy.setdefault('equipment', {'items': [], 'weapon': '', 'armor': ''})
        if eq.get('armor'):
            eq['items'].append(eq['armor'])
            eq['armor'] = ''
            self.save_json()
            self.show_enemy_inventory(row, 0)
        else:
            QMessageBox.information(self, "No Armor Equipped", "No armor is currently equipped.")

    def submit_result(self, row):
        global Qt
        notation_item = self.dice_results_table.item(row, 0)
        total_item = self.dice_results_table.item(row, 1)
        if not notation_item or not total_item:
            QMessageBox.warning(self, "Missing Data", "Dice notation or total is missing.")
            return
        notation = notation_item.text().strip()
        total = total_item.text().strip()
        if not total:
            QMessageBox.warning(self, "No Total Entered", "Enter the roll total before submitting.")
            return
        # --- Gather context for detailed log ---
        attacker_name = attacker_type = weapon_name = weapon_mod = ""
        target_name = target_type = armor_name = armor_dr = ""
        buffs_applied = []
        location = sub_location = ""
        hit_mod = dmg_mod = dr_mod = 0
        # --- NEW: Gather attacker, target, weapon, armor objects ---
        attacker = target = weapon = armor = None
        if hasattr(self, 'attacker_list'):
            selected = self.attacker_list.selectedItems()
            if selected and len(selected) == 1:
                attacker_type_val, attacker_id = selected[0].data(Qt.UserRole)
                if attacker_type_val == 'player':
                    attacker = next((p for p in self.data.get('players', []) if p['id'] == attacker_id), None)
                else:
                    attacker = next((e for e in self.data.get('enemies', []) if e['id'] == attacker_id), None)
                if attacker:
                    attacker_name = attacker.get('name', '')
                    eq = attacker.get('equipment', {})
                    weapon_id = eq.get('weapon', '')
                    weapon = next((w for w in self.data.get('weapons', []) if w['id'] == weapon_id), None) if weapon_id else None
                    weapon_name = weapon.get('name', '') if weapon else ''
                    weapon_mod = weapon.get('hit_modifier', 0) if weapon else 0
                    location = attacker.get('location', '')
                    sub_location = attacker.get('sub_location', '')
        if hasattr(self, 'target_select'):
            idx = self.target_select.currentIndex()
            if idx >= 0:
                data = self.target_select.itemData(idx)
                if data:
                    target_type_val, target_id = data
                    if target_type_val == 'player':
                        target = next((p for p in self.data.get('players', []) if p['id'] == target_id), None)
                    else:
                        target = next((e for e in self.data.get('enemies', []) if e['id'] == target_id), None)
                    if target:
                        target_name = target.get('name', '')
                        eq = target.get('equipment', {})
                        armor_id = eq.get('armor', '')
                        armor = next((a for a in self.data.get('armor', []) if a['id'] == armor_id), None) if armor_id else None
                        armor_name = armor.get('name', '') if armor else ''
                        armor_dr = armor.get('damage_resistance', {}) if armor else {}
                        dr_mod = armor_dr.get('physical', 0) if isinstance(armor_dr, dict) else 0
        # --- Enhanced Damage Logic ---
        try:
            base_damage = int(total)
        except Exception:
            base_damage = 0
        # 1. Detect weapon type
        weapon_type = weapon.get('type', '').lower() if weapon and 'type' in weapon else ''
        if not weapon_type:
            if weapon and 'sword' in weapon.get('name', '').lower():
                weapon_type = 'melee'
            elif weapon and 'gun' in weapon.get('name', '').lower():
                weapon_type = 'ranged'
            else:
                weapon_type = 'melee'
        # 2. Detect targeted body part
        body_part = ''
        if hasattr(self, 'body_part_select') and self.body_part_select.currentText():
            body_part = self.body_part_select.currentText().lower()
        # 3. Gather resistances for base damage
        total_resistance = 0
        resist_details = []
        if armor and 'damage_resistance' in armor:
            dr = armor['damage_resistance']
            if weapon_type in dr:
                total_resistance += dr[weapon_type]
                resist_details.append(f"{armor_name} ({weapon_type}: {dr[weapon_type]})")
            if body_part and body_part in dr:
                total_resistance += dr[body_part]
                resist_details.append(f"{armor_name} ({body_part}: {dr[body_part]})")
        # 4. Add item/buff resistances
        if target and 'equipment' in target:
            eq = target['equipment']
            for item_id in eq.get('items', []):
                item = next((i for i in self.data.get('items', []) if i['id'] == item_id), None)
                if item and 'damage_resistance' in item:
                    dr = item['damage_resistance']
                    if weapon_type in dr:
                        total_resistance += dr[weapon_type]
                        resist_details.append(f"{item.get('name', '')} ({weapon_type}: {dr[weapon_type]})")
                    if body_part and body_part in dr:
                        total_resistance += dr[body_part]
                        resist_details.append(f"{item.get('name', '')} ({body_part}: {dr[body_part]})")
        for b in target.get('buffs', []):
            if not isinstance(b, dict):
                continue
            effect = b.get('effect', {})
            if 'damage_resistance' in effect:
                dr = effect['damage_resistance']
                if isinstance(dr, dict):
                    if weapon_type in dr:
                        total_resistance += dr[weapon_type]
                        resist_details.append(f"{b['name']} ({weapon_type}: {dr[weapon_type]})")
                    if body_part and body_part in dr:
                        total_resistance += dr[body_part]
                        resist_details.append(f"{b['name']} ({body_part}: {dr[body_part]})")
        # 5. Apply resistance to base damage
        final_damage = max(0, base_damage - total_resistance)
        resist_str = f" Applied resistance: {' + '.join(resist_details)} = {total_resistance}." if resist_details else ""
        # --- NEW: Special Effects (fire, electric, etc.) ---
        special_breakdown = []
        special_total = 0
        if weapon and weapon.get('special_effects'):
            for effect in weapon['special_effects']:
                effect_name = effect.get('name', effect.get('damage_type', 'special'))
                dtype = effect.get('damage_type', 'special')
                flat_bonus = effect.get('flat_bonus', 0)
                dice = effect.get('dice', '')
                # Prompt for dice roll if needed
                effect_damage = 0
                if dice:
                    dialog = ManualRollDialog(dice, f"Enter {effect_name} Damage Roll ({dice})", self)
                    if dialog.exec():
                        effect_damage += dialog.get_data()['total']
                effect_damage += flat_bonus
                # Apply resistances/vulnerabilities for this type
                # Use the same gather_resists_vulns logic as in roll_for_attack
                def gather_resists_vulns(target, dtype):
                    total_resist = 0
                    total_vuln = 0
                    details = []
                    # Armor
                    armor = next((a for a in self.data["armor"] if a["id"] == target.get("equipment", {}).get("armor")), {})
                    if armor:
                        for k, v in armor.get("damage_resistance", {}).items():
                            if k == dtype:
                                total_resist += v
                                details.append(f"Armor({armor.get('name','')} {dtype} RES:{v})")
                        for k, v in armor.get("resistances", {}).items():
                            if k == dtype:
                                total_resist += v
                                details.append(f"Armor({armor.get('name','')} {dtype} RES:{v})")
                        for k, v in armor.get("vulnerabilities", {}).items():
                            if k == dtype:
                                total_vuln += v
                                details.append(f"Armor({armor.get('name','')} {dtype} VULN:{v})")
                    # Items
                    for item_id in target.get("equipment", {}).get("items", []):
                        item = next((i for i in self.data.get("items", []) if i["id"] == item_id), None)
                        if item:
                            for k, v in item.get("resistances", {}).items():
                                if k == dtype:
                                    total_resist += v
                                    details.append(f"Item({item.get('name','')} {dtype} RES:{v})")
                            for k, v in item.get("vulnerabilities", {}).items():
                                if k == dtype:
                                    total_vuln += v
                                    details.append(f"Item({item.get('name','')} {dtype} VULN:{v})")
                    # Buffs
                    for buff in target.get("buffs", []):
                        if not isinstance(buff, dict):
                            continue
                        for k, v in buff.get("resistances", {}).items():
                            if k == dtype:
                                total_resist += v
                                details.append(f"Buff({buff.get('name','')} {dtype} RES:{v})")
                        for k, v in buff.get("vulnerabilities", {}).items():
                            if k == dtype:
                                total_vuln += v
                                details.append(f"Buff({buff.get('name','')} {dtype} VULN:{v})")
                    return total_resist, total_vuln, details
                resist, vuln, details = gather_resists_vulns(target, dtype)
                final_special = max(0, effect_damage - resist + vuln)
                special_breakdown.append(f"{final_special} {dtype} (raw:{effect_damage}, -{resist} RES, +{vuln} VULN; {'; '.join(details)})")
                special_total += final_special
        # --- Update HP and log ---
        total_final = final_damage + special_total
        hp_change_str = ""
        if target and 'stats' in target and 'hp' in target['stats']:
            max_hp = target['stats'].get('max_hp', None)
            hp_before = target['stats']['hp']
            target['stats']['hp'] = max(0, target['stats']['hp'] - total_final)
            hp_after = target['stats']['hp']
            hp_change_str = f" Target HP: {hp_before} -> {hp_after}{'/' + str(max_hp) if max_hp else ''}"
            self.save_json()
        # --- Compose improved log message ---
        log_lines = []
        log_lines.append(f"{attacker_name} attacks {target_name}!")
        # Base damage
        base_line = f"  • Base Damage: {base_damage} (roll)"
        if armor_name and resist_details:
            base_line += f" → {final_damage} after resistance [{', '.join(resist_details)}]"
        elif resist_details:
            base_line += f" → {final_damage} after resistance [{', '.join(resist_details)}]"
        else:
            base_line += f" → {final_damage}"
        log_lines.append(base_line)
        # Specials
        if special_breakdown:
            log_lines.append(f"  • Special Damage:")
            for s in special_breakdown:
                # Parse s: "{final_special} {dtype} (raw:{effect_damage}, -{resist} RES, +{vuln} VULN; ... )"
                import re
                m = re.match(r"(\d+) ([^ ]+) \(raw:(\d+), -?(\d+) RES, \+?(\d+) VULN; (.*)\)", s)
                if m:
                    val, dtype, raw, res, vul, src = m.groups()
                    src = src.strip()
                    src_str = f" [{src}]" if src else ""
                    log_lines.append(f"      - {dtype.title()}: {val} (raw: {raw}, resisted: {res}, vulnerable: {vul}){src_str}")
                else:
                    log_lines.append(f"      - {s}")
        # Total
        log_lines.append(f"  • Total Damage Dealt: {total_final}")
        # HP change
        if target_name and hp_change_str:
            # Parse hp_change_str: " Target HP: {hp_before} -> {hp_after}" (strip leading space)
            hp_change = hp_change_str.strip().replace("Target HP:", f"{target_name} HP:")
            log_lines.append(f"  • {hp_change}")
        log_msg = "\n".join(log_lines)
        # --- Save log ---
        from datetime import datetime
        log_entry = {
            "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
            "timestamp": datetime.now().isoformat(),
            "category": "manual",
            "details": log_msg
        }
        self.data.setdefault('log', []).append(log_entry)
        if hasattr(self, 'battle_log') and self.battle_log:
            self.battle_log.append(log_msg)
        self.save_json()
        if hasattr(self, 'player_window') and self.player_window is not None:
            self.player_window.battle_log_update_signal.emit(self.data.get('log', []))
        from PySide6.QtCore import Qt
        new_total_item = QTableWidgetItem(total)
        new_total_item.setFlags(new_total_item.flags() | Qt.ItemIsEditable)
        self.dice_results_table.setItem(row, 1, new_total_item)

        # --- Special Effects Stage: Conditional Specials ---
        if hasattr(self, 'stage_special') and self.stage_special.isChecked() and weapon and weapon.get('special_effects'):
            conditional_logged = False
            for effect in weapon['special_effects']:
                trigger_number = effect.get('trigger_number')
                probability_dice = effect.get('probability_dice')
                description = effect.get('description', '')
                applies = effect.get('applies', {})
                if trigger_number is not None and probability_dice:
                    try:
                        roll_result = int(total)
                    except Exception:
                        roll_result = None
                    log_lines = []
                    log_lines.append(f"{attacker_name} attempts a special effect!")
                    log_lines.append(f"  • Special Roll: {roll_result} (player's chosen number: {trigger_number})")
                    if roll_result == int(trigger_number):
                        log_lines.append(f"    → SPECIAL EFFECT TRIGGERED!")
                        if description:
                            log_lines.append(f"      > {description}")
                        # --- Apply ongoing effects to target ---
                        if target:
                            # Lost limbs
                            if 'lost_limbs' in applies:
                                target.setdefault('lost_limbs', [])
                                for limb in applies['lost_limbs']:
                                    if limb not in target['lost_limbs']:
                                        target['lost_limbs'].append(limb)
                                        log_lines.append(f"      > {target_name} lost limb: {limb}")
                            # Broken limbs
                            if 'broken_limbs' in applies:
                                target.setdefault('broken_limbs', [])
                                for limb in applies['broken_limbs']:
                                    if limb not in target['broken_limbs']:
                                        target['broken_limbs'].append(limb)
                                        log_lines.append(f"      > {target_name} broke limb: {limb}")
                            # Status effects (with duration)
                            if 'status_effects' in applies:
                                target.setdefault('status_effects', [])
                                for se in applies['status_effects']:
                                    # se can be a string or dict
                                    if isinstance(se, str):
                                        if not any(s.get('name', s) == se for s in target['status_effects']):
                                            target['status_effects'].append({'name': se, 'duration': None})
                                            log_lines.append(f"      > {target_name} gains status: {se}")
                                    elif isinstance(se, dict):
                                        if not any(s.get('name') == se.get('name') for s in target['status_effects']):
                                            target['status_effects'].append(se)
                                            dur_str = f" for {se['duration']} rounds" if se.get('duration') else ''
                                            log_lines.append(f"      > {target_name} gains status: {se['name']}{dur_str}")
                            self.save_json()
                    else:
                        log_lines.append(f"    → No special effect triggered.")
                    log_msg = "\n".join(log_lines)
                    from datetime import datetime
                    log_entry = {
                        "id": f"log_{len(self.data.get('log', [])) + 1:03d}",
                        "timestamp": datetime.now().isoformat(),
                        "category": "manual",
                        "details": log_msg
                    }
                    self.data.setdefault('log', []).append(log_entry)
                    if hasattr(self, 'battle_log') and self.battle_log:
                        self.battle_log.append(log_msg)
                    self.save_json()
                    if hasattr(self, 'player_window') and self.player_window is not None:
                        self.player_window.battle_log_update_signal.emit(self.data.get('log', []))
                    from PySide6.QtCore import Qt
                    new_total_item = QTableWidgetItem(total)
                    new_total_item.setFlags(new_total_item.flags() | Qt.ItemIsEditable)
                    self.dice_results_table.setItem(row, 1, new_total_item)
                    conditional_logged = True
                    break
            if conditional_logged:
                return
        # --- Otherwise, use the normal always-on special logic ---

    # --- Decrement status effect durations after each round ---
    def decrement_status_effects(self, entity):
        changed = False
        if 'status_effects' in entity:
            for se in list(entity['status_effects']):
                if isinstance(se, dict) and se.get('duration') is not None:
                    se['duration'] -= 1
                    if se['duration'] <= 0:
                        entity['status_effects'].remove(se)
                        changed = True
        if changed:
            self.save_json()

    # --- Show ongoing effects in player/enemy info panel ---
    # (Add to PlayerWindow.update_display, after stats)
    # Example:
    #   if player.get('lost_limbs'):
    #       self.player_section.addWidget(QLabel(f"Lost Limbs: {', '.join(player['lost_limbs'])}"))
    #   if player.get('broken_limbs'):
    #       self.player_section.addWidget(QLabel(f"Broken Limbs: {', '.join(player['broken_limbs'])}"))
    #   if player.get('status_effects'):
    #       se_str = ', '.join(f"{s['name']} ({s['duration']}r)" if isinstance(s, dict) and s.get('duration') else s['name'] if isinstance(s, dict) else s for s in player['status_effects'])
    #       self.player_section.addWidget(QLabel(f"Status Effects: {se_str}"))

    # --- Auto-decrement status effect durations for all entities after each round ---
    def decrement_all_status_effects(self):
        changed = False
        for entity_list in [self.data.get('players', []), self.data.get('enemies', [])]:
            for ent in entity_list:
                if 'status_effects' in ent:
                    for se in list(ent['status_effects']):
                        if isinstance(se, dict) and se.get('duration') is not None:
                            se['duration'] -= 1
                            if se['duration'] <= 0:
                                ent['status_effects'].remove(se)
                                changed = True
        if changed:
            self.save_json()
            self.update_tables()
            if hasattr(self, 'player_window') and self.player_window is not None:
                self.player_window.update_display()

    # --- Manual status effect editor dialog ---
    def edit_status_effects_dialog(self, entity):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Status Effects for {entity.get('name', '')}")
        layout = QVBoxLayout(dialog)
        se_list = QListWidget()
        for se in entity.get('status_effects', []):
            if isinstance(se, dict):
                dur = f" ({se['duration']}r)" if se.get('duration') else ''
                se_list.addItem(f"{se['name']}{dur}")
            else:
                se_list.addItem(str(se))
        layout.addWidget(se_list)
        btns = QHBoxLayout()
        inc_btn = QPushButton("Increase Duration")
        dec_btn = QPushButton("Decrease Duration")
        remove_btn = QPushButton("Remove Effect")
        btns.addWidget(inc_btn)
        btns.addWidget(dec_btn)
        btns.addWidget(remove_btn)
        layout.addLayout(btns)
        def inc():
            idx = se_list.currentRow()
            if idx < 0: return
            se = entity['status_effects'][idx]
            if isinstance(se, dict) and se.get('duration') is not None:
                se['duration'] += 1
                se_list.item(idx).setText(f"{se['name']} ({se['duration']}r)")
        def dec():
            idx = se_list.currentRow()
            if idx < 0: return
            se = entity['status_effects'][idx]
            if isinstance(se, dict) and se.get('duration') is not None:
                se['duration'] -= 1
                if se['duration'] <= 0:
                    entity['status_effects'].pop(idx)
                    se_list.takeItem(idx)
                else:
                    se_list.item(idx).setText(f"{se['name']} ({se['duration']}r)")
        def remove():
            idx = se_list.currentRow()
            if idx < 0: return
            entity['status_effects'].pop(idx)
            se_list.takeItem(idx)
        inc_btn.clicked.connect(inc)
        dec_btn.clicked.connect(dec)
        remove_btn.clicked.connect(remove)
        ok_btn = QPushButton("Done")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)
        dialog.setLayout(layout)
        if dialog.exec():
            self.save_json()
            self.update_tables()
            if hasattr(self, 'player_window') and self.player_window is not None:
                self.player_window.update_display()

    # --- Add button to player/enemy info panel to open status effect editor ---
    # In PlayerWindow.update_display, after showing status effects:
    #   edit_btn = QPushButton('Edit Status Effects')
    #   edit_btn.clicked.connect(lambda _, ent=player: self.parent().edit_status_effects_dialog(ent))
    #   self.player_section.addWidget(edit_btn)
    # (Repeat for enemies)

    # --- Display lost limbs, broken limbs, and status effects in info panel ---
    # Already shown in previous patch, but now with edit button for status effects.

    # --- Call decrement_all_status_effects after each round or attack as needed ---
    # For example, at the end of roll_for_attack or after all attacks in a round:
    #   self.decrement_all_status_effects()

# --- Add this new dialog for resistances/vulnerabilities ---
class ResistanceEditorDialog(QDialog):
    def __init__(self, title, data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout(self)
        self.resistances = dict(data) if data else {}
        self.list_widget = QListWidget()
        self.refresh_list()
        self.layout.addWidget(self.list_widget)
        btns = QHBoxLayout()
        add_btn = QPushButton("Add")
        edit_btn = QPushButton("Edit")
        remove_btn = QPushButton("Remove")
        btns.addWidget(add_btn)
        btns.addWidget(edit_btn)
        btns.addWidget(remove_btn)
        self.layout.addLayout(btns)
        add_btn.clicked.connect(self.add_resistance)
        edit_btn.clicked.connect(self.edit_resistance)
        remove_btn.clicked.connect(self.remove_resistance)
        ok_btn = QPushButton("Done")
        ok_btn.clicked.connect(self.accept)
        self.layout.addWidget(ok_btn)

    def refresh_list(self):
        self.list_widget.clear()
        for k, v in self.resistances.items():
            self.list_widget.addItem(f"{k}: {v}")

    def add_resistance(self):
        dialog = QDialog(self)
        layout = QFormLayout(dialog)
        dtype = QLineEdit()
        value = QSpinBox(); value.setRange(-99, 999)
        layout.addRow("Type:", dtype)
        layout.addRow("Value:", value)
        ok_btn = QPushButton("Add")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)
        dialog.setLayout(layout)
        if dialog.exec():
            self.resistances[dtype.text()] = value.value()
            self.refresh_list()

    def edit_resistance(self):
        idx = self.list_widget.currentRow()
        if idx < 0: return
        key = list(self.resistances.keys())[idx]
        dialog = QDialog(self)
        layout = QFormLayout(dialog)
        dtype = QLineEdit(key)
        value = QSpinBox(); value.setRange(-99, 999); value.setValue(self.resistances[key])
        layout.addRow("Type:", dtype)
        layout.addRow("Value:", value)
        ok_btn = QPushButton("Save")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)
        dialog.setLayout(layout)
        if dialog.exec():
            del self.resistances[key]
            self.resistances[dtype.text()] = value.value()
            self.refresh_list()

    def remove_resistance(self):
        idx = self.list_widget.currentRow()
        if idx < 0: return
        key = list(self.resistances.keys())[idx]
        del self.resistances[key]
        self.refresh_list()

    def get_data(self):
        return self.resistances

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WastelandOdysseyGUI()
    window.show()
    sys.exit(app.exec())