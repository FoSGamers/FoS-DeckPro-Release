# deckforge_gui_autosim.py

import json
import random
import subprocess
from typing import List, Dict
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit,
    QFileDialog, QMessageBox, QLabel, QHBoxLayout, QLineEdit
)
import sys
import os

from deck_learning_engine import smart_analyze_synergy, update_win_stats
from forge_result_parser import wait_and_parse_forge_output

# === Deck Functions ===
def load_inventory(json_path: str) -> List[Dict]:
    with open(json_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def filter_legal_cards(cards: List[Dict], format_key: str = 'legal_pauper') -> List[Dict]:
    return [card for card in cards if card.get(format_key) == 'legal']

def generate_deck(cards: List[Dict]) -> List[Dict]:
    synergy_scores = smart_analyze_synergy(cards)
    sorted_cards = sorted(cards, key=lambda c: synergy_scores.get(c['Name'], 0), reverse=True)
    deck = []
    deck += [card for card in sorted_cards if 'Creature' in card['type_line']][:24]
    deck += [card for card in sorted_cards if 'Instant' in card['type_line'] or 'Sorcery' in card['type_line']][:12]
    deck += [card for card in sorted_cards if 'Land' in card['type_line']][:20]
    if len(deck) < 60:
        deck += sorted_cards[len(deck):60]
    return deck[:60]

def export_to_forge(deck: List[Dict], path: str):
    with open(path, 'w') as f:
        f.write("[metadata]\nName=DeckForge Auto Deck\n\n[main]\n")
        for card in deck:
            f.write(f"1 {card['Name']}\n")

def summarize_deck(deck: List[Dict]) -> str:
    return "\n".join([f"{card['Name']} | {card['type_line']} | CMC: {card['cmc']} | Cost: {card['mana_cost']}" for card in deck])

# === GUI App ===
class DeckForgeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeckForge AI – Auto Sim GUI")
        self.resize(800, 600)

        self.inventory = []
        self.deck = []
        self.forge_path = ""
        self.opponent_deck_path = ""

        layout = QVBoxLayout()
        hlayout = QHBoxLayout()

        self.load_btn = QPushButton("Load Inventory")
        self.load_btn.clicked.connect(self.load_inventory_file)
        hlayout.addWidget(self.load_btn)

        self.build_btn = QPushButton("Build Deck")
        self.build_btn.clicked.connect(self.build_deck)
        hlayout.addWidget(self.build_btn)

        self.sim_btn = QPushButton("Simulate in Forge")
        self.sim_btn.clicked.connect(self.simulate_deck)
        hlayout.addWidget(self.sim_btn)

        layout.addLayout(hlayout)

        # Opponent deck selection
        opponent_layout = QHBoxLayout()
        self.opp_deck_field = QLineEdit()
        self.opp_deck_field.setPlaceholderText("Opponent deck .dck file")
        self.opp_deck_browse = QPushButton("Choose Opponent Deck")
        self.opp_deck_browse.clicked.connect(self.select_opponent_deck)
        opponent_layout.addWidget(self.opp_deck_field)
        opponent_layout.addWidget(self.opp_deck_browse)
        layout.addLayout(opponent_layout)

        self.deck_display = QTextEdit()
        self.deck_display.setReadOnly(True)

        layout.addWidget(QLabel("Deck List:"))
        layout.addWidget(self.deck_display)
        self.setLayout(layout)

    def load_inventory_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Inventory JSON", "", "JSON Files (*.json)")
        if path:
            self.inventory = load_inventory(path)
            QMessageBox.information(self, "Inventory Loaded", f"Loaded {len(self.inventory)} cards.")

    def build_deck(self):
        legal = filter_legal_cards(self.inventory)
        self.deck = generate_deck(legal)
        self.deck_display.setText(summarize_deck(self.deck))

    def select_opponent_deck(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Opponent Deck", "", "Forge Deck (*.dck)")
        if path:
            self.opponent_deck_path = path
            self.opp_deck_field.setText(path)

    def simulate_deck(self):
        if not self.deck:
            QMessageBox.warning(self, "No Deck", "Build a deck first.")
            return

        self.forge_path, _ = QFileDialog.getOpenFileName(self, "Select Forge Executable", "", "*.jar")
        if not self.forge_path:
            return

        if not self.opponent_deck_path:
            QMessageBox.warning(self, "Missing Opponent Deck", "Please choose an opponent deck to simulate against.")
            return

        export_to_forge(self.deck, "autodeck.dck")

        cmd = ["java", "-jar", self.forge_path, "sim", "autodeck.dck", self.opponent_deck_path, "5"]
        with open("forge_simulation_result.txt", "w") as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)

        wait_and_parse_forge_output(self.deck)
        QMessageBox.information(self, "Simulation Complete", "Forge simulation run complete and stats updated.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = DeckForgeApp()
    gui.show()
    sys.exit(app.exec())
