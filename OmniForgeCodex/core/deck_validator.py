from typing import Dict, Any, List, Tuple
import numpy as np
from collections import Counter

class DeckValidator:
    def __init__(self, format_rules: Dict[str, Any]):
        self.format_rules = format_rules
        
    def validate_deck(self, deck: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a deck against format rules"""
        errors = []
        
        # Check deck size
        if not self._validate_deck_size(deck):
            errors.append("Invalid deck size")
            
        # Check card limits
        if not self._validate_card_limits(deck):
            errors.append("Invalid card quantities")
            
        # Check mana curve
        if not self._validate_mana_curve(deck):
            errors.append("Invalid mana curve")
            
        # Check color balance
        if not self._validate_color_balance(deck):
            errors.append("Invalid color balance")
            
        # Check format legality
        if not self._validate_format_legality(deck):
            errors.append("Contains illegal cards")
            
        # Check budget
        if not self._validate_budget(deck):
            errors.append("Exceeds budget")
            
        return len(errors) == 0, errors
        
    def _validate_deck_size(self, deck: Dict[str, Any]) -> bool:
        """Validate deck size against format rules"""
        min_size = self.format_rules.get('min_deck_size', 60)
        max_size = self.format_rules.get('max_deck_size', 60)
        actual_size = sum(count for _, count in deck['mainboard'])
        return min_size <= actual_size <= max_size
        
    def _validate_card_limits(self, deck: Dict[str, Any]) -> bool:
        """Validate card quantity limits"""
        max_copies = self.format_rules.get('max_copies', 4)
        card_counts = Counter(card['name'] for card, _ in deck['mainboard'])
        return all(count <= max_copies for count in card_counts.values())
        
    def _validate_mana_curve(self, deck: Dict[str, Any]) -> bool:
        """Validate mana curve distribution"""
        curve = self._calculate_mana_curve(deck)
        ideal_curve = self.format_rules.get('ideal_mana_curve', {})
        
        if not ideal_curve:
            return True
            
        # Check if curve follows ideal distribution
        for cmc, count in curve.items():
            if cmc in ideal_curve:
                if not (ideal_curve[cmc] * 0.7 <= count <= ideal_curve[cmc] * 1.3):
                    return False
        return True
        
    def _validate_color_balance(self, deck: Dict[str, Any]) -> bool:
        """Validate color balance"""
        color_counts = self._calculate_color_counts(deck)
        total_colors = sum(color_counts.values())
        
        if total_colors == 0:
            return True
            
        # Check if any color is too dominant
        for count in color_counts.values():
            if count / total_colors > 0.4:  # No color should be more than 40%
                return False
        return True
        
    def _validate_format_legality(self, deck: Dict[str, Any]) -> bool:
        # Implementation of _validate_format_legality method
        pass
        
    def _validate_budget(self, deck: Dict[str, Any]) -> bool:
        # Implementation of _validate_budget method
        pass
        
    def _calculate_mana_curve(self, deck: Dict[str, Any]) -> Dict[str, int]:
        # Implementation of _calculate_mana_curve method
        pass
        
    def _calculate_color_counts(self, deck: Dict[str, Any]) -> Dict[str, int]:
        # Implementation of _calculate_color_counts method
        pass 