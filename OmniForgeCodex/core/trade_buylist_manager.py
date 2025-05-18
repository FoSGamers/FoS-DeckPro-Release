from datetime import datetime
from typing import Dict, List, Optional
import requests
import json
import os

class TradeBuylistManager:
    def __init__(self, scryfall_client):
        self.scryfall_client = scryfall_client
        self.price_cache = {}
        self.price_cache_file = "price_cache.json"
        self.cache_expiry = 3600  # 1 hour
        self._load_price_cache()
        
    def _load_price_cache(self):
        try:
            if os.path.exists(self.price_cache_file):
                with open(self.price_cache_file, 'r') as f:
                    data = json.load(f)
                    if datetime.now().timestamp() - data['timestamp'] < self.cache_expiry:
                        self.price_cache = data['prices']
        except Exception as e:
            print(f"Error loading price cache: {e}")
            self.price_cache = {}
            
    def _save_price_cache(self):
        try:
            with open(self.price_cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().timestamp(),
                    'prices': self.price_cache
                }, f)
        except Exception as e:
            print(f"Error saving price cache: {e}")
            
    def generate_buylist(self, deck_obj: dict) -> List[Dict]:
        buylist = []
        for card, count in deck_obj["mainboard"]:
            price_data = self._get_card_prices(card["name"])
            if price_data:
                buylist.append({
                    "name": card["name"],
                    "quantity": count,
                    "cash_price": price_data.get("cash", 0),
                    "credit_price": price_data.get("credit", 0),
                    "condition": "NM",  # Default condition
                    "last_updated": datetime.now().isoformat()
                })
        return buylist
        
    def _get_card_prices(self, card_name: str) -> Optional[Dict]:
        if card_name in self.price_cache:
            return self.price_cache[card_name]
            
        try:
            # Implement price fetching from multiple sources
            prices = self._fetch_prices_from_sources(card_name)
            self.price_cache[card_name] = prices
            self._save_price_cache()
            return prices
        except Exception as e:
            print(f"Error fetching prices for {card_name}: {e}")
            return None

    def generate_trade_list(self, inventory: list, criteria: dict) -> list:
        return [card["name"] for card in inventory if card["purchase_price"] > criteria.get("min_value", 0)]
