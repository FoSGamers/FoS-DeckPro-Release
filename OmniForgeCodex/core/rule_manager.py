from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

class RuleManager:
    def __init__(self):
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.versions: Dict[str, List[str]] = {}
        self.load_rules()
        
    def load_rules(self):
        """Load rules with validation and inheritance"""
        try:
            with open(Path("resources/default_data/codex_rules.json"), 'r') as f:
                self.rules = json.load(f)
            self._validate_rules()
            self._load_metadata()
            self._setup_inheritance()
        except Exception as e:
            logging.error(f"Error loading rules: {e}")
            
    def _validate_rules(self):
        """Validate rule definitions"""
        required_fields = {'budget', 'singleton'}
        for format_name, rules in self.rules.items():
            if not all(field in rules for field in required_fields):
                raise ValueError(f"Missing required fields in format {format_name}")
            if not isinstance(rules['budget'], (int, float)):
                raise ValueError(f"Invalid budget in format {format_name}")
            if not isinstance(rules['singleton'], bool):
                raise ValueError(f"Invalid singleton flag in format {format_name}")
                
    def _setup_inheritance(self):
        """Setup rule inheritance"""
        for format_name, rules in self.rules.items():
            if 'inherits' in rules:
                parent_format = rules['inherits']
                if parent_format in self.rules:
                    parent_rules = self.rules[parent_format]
                    # Merge rules with inheritance
                    self.rules[format_name] = {
                        **parent_rules,
                        **rules,
                        'inherits': parent_format
                    }
                    
    def get_rule(self, format_name: str, rule_name: str) -> Any:
        """Get a specific rule with inheritance"""
        if format_name not in self.rules:
            raise ValueError(f"Unknown format: {format_name}")
            
        rules = self.rules[format_name]
        while 'inherits' in rules and rule_name not in rules:
            rules = self.rules[rules['inherits']]
            
        return rules.get(rule_name)
        
    def validate_deck_rules(self, deck: Dict[str, Any], format_name: str) -> List[str]:
        """Validate a deck against format rules"""
        errors = []
        rules = self.rules[format_name]
        
        # Check budget
        total_cost = sum(card['purchase_price'] * count 
                        for card, count in deck['mainboard'])
        if total_cost > rules['budget']:
            errors.append(f"Deck exceeds budget of ${rules['budget']}")
            
        # Check singleton
        if rules['singleton']:
            card_counts = {}
            for card, count in deck['mainboard']:
                if card['name'] in card_counts:
                    errors.append(f"Multiple copies of {card['name']} in singleton format")
                card_counts[card['name']] = count
                
        return errors 