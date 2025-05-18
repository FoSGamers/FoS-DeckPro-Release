from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

class CardManager:
    def __init__(self):
        self.cards: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[str]] = {}
        self.prices: Dict[str, List[Dict[str, Any]]] = {}
        self.availability: Dict[str, Dict[str, Any]] = {}
        
    def update_card_data(self, card_id: str, data: Dict[str, Any]):
        """Update card data with version tracking"""
        if card_id not in self.cards:
            self.cards[card_id] = data
            self.versions[card_id] = [data['version']]
        else:
            if data['version'] != self.cards[card_id]['version']:
                self.versions[card_id].append(data['version'])
            self.cards[card_id] = data
            
    def update_card_price(self, card_id: str, price: float, source: str):
        """Update card price with history"""
        if card_id not in self.prices:
            self.prices[card_id] = []
            
        self.prices[card_id].append({
            'price': price,
            'source': source,
            'timestamp': datetime.now().isoformat()
        })
        
    def update_card_availability(self, card_id: str, 
                               condition: str, 
                               quantity: int, 
                               location: str):
        """Update card availability"""
        if card_id not in self.availability:
            self.availability[card_id] = {}
            
        self.availability[card_id][condition] = {
            'quantity': quantity,
            'location': location,
            'last_updated': datetime.now().isoformat()
        }
        
    def get_card_history(self, card_id: str) -> Dict[str, Any]:
        """Get complete card history"""
        return {
            'data': self.cards.get(card_id, {}),
            'versions': self.versions.get(card_id, []),
            'prices': self.prices.get(card_id, []),
            'availability': self.availability.get(card_id, {})
        } 