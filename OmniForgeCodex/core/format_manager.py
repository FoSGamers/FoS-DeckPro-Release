from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

class FormatManager:
    def __init__(self):
        self.formats: Dict[str, Dict[str, Any]] = {}
        self.banlists: Dict[str, List[str]] = {}
        self.rotations: Dict[str, List[str]] = {}
        self.load_formats()
        
    def load_formats(self):
        """Load format definitions with validation"""
        try:
            with open(Path("resources/default_data/formats.json"), 'r') as f:
                self.formats = json.load(f)
            self._validate_formats()
            self._load_banlists()
            self._load_rotations()
        except Exception as e:
            logging.error(f"Error loading formats: {e}")
            
    def _validate_formats(self):
        """Validate format definitions"""
        required_fields = {'min_deck_size', 'max_deck_size', 'allowed_sets'}
        for format_name, format_def in self.formats.items():
            if not all(field in format_def for field in required_fields):
                raise ValueError(f"Missing required fields in format {format_name}")
                
    def is_card_legal(self, card: Dict[str, Any], format_name: str) -> bool:
        """Check if a card is legal in a format"""
        if format_name not in self.formats:
            return False
            
        format_def = self.formats[format_name]
        
        # Check if card is in allowed sets
        if card['set'] not in format_def['allowed_sets']:
            return False
            
        # Check if card is banned
        if card['name'] in self.banlists.get(format_name, []):
            return False
            
        return True
        
    def get_legal_cards(self, format_name: str) -> List[Dict[str, Any]]:
        """Get all legal cards for a format"""
        if format_name not in self.formats:
            return []
            
        format_def = self.formats[format_name]
        legal_cards = []
        
        for card in self.card_manager.get_all_cards():
            if self.is_card_legal(card, format_name):
                legal_cards.append(card)
                
        return legal_cards 