"""
Inventory management for FoS_DeckPro
"""

from typing import List, Dict, Any, Optional

class CardInventory:
    """Manages a collection of Magic: The Gathering cards"""
    
    def __init__(self):
        self.cards: List[Dict[str, Any]] = []
        
    def load_cards(self, cards: List[Dict[str, Any]]) -> None:
        """
        Load cards into the inventory
        
        Args:
            cards: List of card dictionaries
        """
        self.cards = cards.copy()
        
    def add_card(self, card: Dict[str, Any]) -> None:
        """
        Add a single card to the inventory
        
        Args:
            card: Card dictionary
        """
        self.cards.append(card)
        
    def remove_card(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Remove a card from the inventory
        
        Args:
            index: Index of the card to remove
            
        Returns:
            Removed card or None if index invalid
        """
        if 0 <= index < len(self.cards):
            return self.cards.pop(index)
        return None
        
    def get_cards(self) -> List[Dict[str, Any]]:
        """
        Get all cards in the inventory
        
        Returns:
            List of all cards
        """
        return self.cards.copy()
        
    def get_card(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific card by index
        
        Args:
            index: Index of the card
            
        Returns:
            Card dictionary or None if index invalid
        """
        if 0 <= index < len(self.cards):
            return self.cards[index]
        return None
        
    def update_card(self, index: int, card: Dict[str, Any]) -> bool:
        """
        Update a card at a specific index
        
        Args:
            index: Index of the card to update
            card: New card data
            
        Returns:
            True if successful, False if index invalid
        """
        if 0 <= index < len(self.cards):
            self.cards[index] = card
            return True
        return False
        
    def get_unique_fields(self) -> List[str]:
        """
        Get all unique field names from the cards
        
        Returns:
            List of field names
        """
        fields = set()
        for card in self.cards:
            fields.update(card.keys())
        return sorted(list(fields))
        
    def filter_cards(self, filters: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Filter cards based on criteria
        
        Args:
            filters: Dictionary of field: value pairs to filter by
            
        Returns:
            List of cards matching the filters
        """
        filtered_cards = []
        for card in self.cards:
            matches = True
            for field, value in filters.items():
                if field in card:
                    card_value = str(card[field]).lower()
                    filter_value = value.lower()
                    if filter_value not in card_value:
                        matches = False
                        break
                else:
                    matches = False
                    break
            if matches:
                filtered_cards.append(card)
        return filtered_cards
        
    def get_all_cards(self) -> List[Dict[str, Any]]:
        """
        Get all cards in the inventory (alias for get_cards)
        
        Returns:
            List of all cards
        """
        return self.cards.copy()
        
    def merge_cards(self, new_cards: List[Dict[str, Any]]) -> None:
        """
        Merge new cards into the existing inventory
        
        Args:
            new_cards: List of new card dictionaries to merge
        """
        self.cards.extend(new_cards) 