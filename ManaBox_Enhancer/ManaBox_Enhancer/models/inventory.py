class CardInventory:
    def __init__(self):
        self.cards = []

    def load_cards(self, cards):
        self.cards = cards.copy()

    def get_all_cards(self):
        return self.cards

    def filter_cards(self, filters):
        # filters: dict of {column: value}
        def matches(card):
            for key, value in filters.items():
                if value and value.lower() not in str(card.get(key, "")).lower():
                    return False
            return True
        return [card for card in self.cards if matches(card)]

    def remove_cards(self, cards_to_remove):
        """Remove all cards in cards_to_remove from the inventory."""
        # Remove by identity or dict equality
        new_cards = [c for c in self.cards if c not in cards_to_remove]
        self.cards = new_cards
