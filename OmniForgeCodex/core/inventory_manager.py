from PySide6.QtCore import QObject, Signal
from utils import parse_csv_with_headers, save_json, load_json
from core.scryfall_client import ScryfallClient
import os
import csv

class InventoryManager(QObject):
    inventory_updated = Signal()
    progress = Signal(str)

    def __init__(self):
        super().__init__()
        self.inventory = []
        self.scryfall_client = ScryfallClient()

    def load_csv_inventory(self, file_path: str, column_mapping: dict = None):
        if not os.path.exists(file_path):
            self.progress.emit(f"File not found: {file_path}")
            return
        
        if os.path.getsize(file_path) > 10 * 1024 * 1024:  # 10MB limit
            self.progress.emit("File too large")
            return
        
        try:
            # Create backup
            backup_path = f"{file_path}.bak"
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, backup_path)

            rows = parse_csv_with_headers(file_path)
            self.inventory = []

            for i, row in enumerate(rows):
                self.progress.emit(f"Processing card {i+1}/{len(rows)}")
                card_name = row.get("Name", "").strip()
                if not card_name:
                    continue

                quantity = int(row.get("Quantity", 1))
                purchase_price = float(row.get("Purchase Price", 0.0))
                card_data = self.scryfall_client.enrich_card_data(card_name, ["all"])
                if not card_data:
                    self.progress.emit(f"Skipping invalid card: {card_name}")
                    continue

                card_data.update({
                    "quantity": quantity,
                    "purchase_price": purchase_price
                })
                self.inventory.append(card_data)

            self.inventory_updated.emit()
        except Exception as e:
            self.progress.emit(f"Error loading inventory: {e}")

    def get_card_pool_for_deckbuilding(self, criteria: dict, exclude_cards_dict: dict = None) -> list:
        pool = []
        format_ = criteria.get("format", "")
        commander_ci = criteria.get("commander_color_identity", [])

        for card in self.inventory:
            if exclude_cards_dict and card["scryfall_id"] in exclude_cards_dict:
                if card["quantity"] <= exclude_cards_dict[card["scryfall_id"]]:
                    continue
            if format_ and card["legalities"].get(format_, "legal") != "legal":
                continue
            if commander_ci and not all(c in commander_ci for c in card["color_identity"]):
                continue
            pool.append(card)

        return pool

    def update_inventory_after_deck_approval(self, deck_card_tuples_list: list):
        for scryfall_id, name, quantity_used in deck_card_tuples_list:
            for card in self.inventory:
                if card["scryfall_id"] == scryfall_id:
                    card["quantity"] -= quantity_used
                    if card["quantity"] <= 0:
                        self.inventory.remove(card)
                    break
        self.inventory_updated.emit()

    def save_inventory(self, file_path: str, format: str = "csv"):
        if format == "json":
            save_json(self.inventory, file_path)
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Quantity", "Purchase Price"])
                for card in self.inventory:
                    writer.writerow([card["name"], card["quantity"], card["purchase_price"]])
