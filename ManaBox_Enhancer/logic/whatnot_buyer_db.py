import json
import os
from typing import Dict, Any, List

BUYERS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'buyers.json')

class WhatnotBuyerDB:
    """
    Manages buyers and their purchase history for Whatnot sales, stored in a JSON file.
    Supports analytics and future CRM features.
    """
    def __init__(self, db_path: str = BUYERS_DB_PATH):
        self.db_path = db_path
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        self.buyers = {}
                    else:
                        self.buyers = json.loads(content)
            except Exception:
                self.buyers = {}
        else:
            self.buyers = {}

    def _save(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.buyers, f, indent=2)

    def add_purchase(self, buyer: Dict[str, Any], sale: Dict[str, Any], show: Dict[str, Any]):
        """
        Add or update a buyer with a new purchase.
        buyer: dict with keys 'name', 'username', 'address'
        sale: dict with card sale info (Name, Quantity, etc)
        show: dict with 'title', 'date'
        """
        key = buyer['username'] or buyer['name']
        if key not in self.buyers:
            self.buyers[key] = {
                'name': buyer['name'],
                'username': buyer['username'],
                'address': buyer['address'],
                'purchases': [],
                'first_purchase': show['date'],
                'last_purchase': show['date'],
                'total_spent': 0.0,
                'total_cards': 0
            }
        entry = self.buyers[key]
        entry['last_purchase'] = show['date']
        entry['purchases'].append({
            'show': show,
            'sale': sale
        })
        # Analytics: update totals
        qty = sale.get('Quantity', 1)
        price = float(sale.get('Price', 0.0))
        entry['total_cards'] += qty
        entry['total_spent'] += price * qty
        self._save()

    def get_buyer(self, username_or_name: str) -> Dict[str, Any]:
        return self.buyers.get(username_or_name, {})

    def get_all_buyers(self) -> List[Dict[str, Any]]:
        return list(self.buyers.values())

    def get_top_buyers(self, n=10) -> List[Dict[str, Any]]:
        return sorted(self.get_all_buyers(), key=lambda b: b['total_spent'], reverse=True)[:n] 