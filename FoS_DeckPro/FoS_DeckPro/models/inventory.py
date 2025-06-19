class CardInventory:
    def __init__(self):
        self.cards = []

    def load_cards(self, cards):
        self.cards = cards.copy()

    def get_all_cards(self):
        return self.cards

    def filter_cards(self, filters):
        # filters: dict of {column: value}
        import re
        NUMERIC_COLUMNS = {
            "Purchase price", "Whatnot price", "Quantity", "cmc", "ManaBox ID", "Collector number",
            # Scryfall price fields
            "usd", "usd_foil", "usd_etched", "eur", "eur_foil", "eur_etched", "tix"
        }
        def is_float(val):
            try:
                float(val)
                return True
            except Exception:
                return False
        def parse_range(val):
            # Supports '>0.10', '<1.00', '0.10-0.20', '>=0.10', '<=1.00'
            val = val.strip()
            if re.match(r'^>=?\s*\d*\.?\d+$', val):
                op = '>=' if val.startswith('>=') else '>'
                num = float(val.lstrip('>=').strip())
                return ('gt', op, num)
            elif re.match(r'^<=?\s*\d*\.?\d+$', val):
                op = '<=' if val.startswith('<=') else '<'
                num = float(val.lstrip('<=') .strip())
                return ('lt', op, num)
            elif '-' in val:
                parts = val.split('-')
                try:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    return ('range', low, high)
                except Exception:
                    return None
            elif is_float(val):
                return ('eq', float(val))
            else:
                return None
        def matches(card):
            for key, value in filters.items():
                if not value:
                    continue
                card_val = card.get(key, "")
                # Numeric/range filtering for numeric columns
                if key in NUMERIC_COLUMNS:
                    # Remove $ if present, handle both string and float
                    try:
                        card_num = float(str(card_val).replace("$", "").strip())
                    except Exception:
                        return False
                    rng = parse_range(value)
                    if rng:
                        if rng[0] == 'eq':
                            if card_num != rng[1]:
                                return False
                        elif rng[0] == 'gt':
                            if rng[1] == '>=':
                                if not (card_num >= rng[2]):
                                    return False
                            else:
                                if not (card_num > rng[2]):
                                    return False
                        elif rng[0] == 'lt':
                            if rng[1] == '<=':
                                if not (card_num <= rng[2]):
                                    return False
                            else:
                                if not (card_num < rng[2]):
                                    return False
                        elif rng[0] == 'range':
                            if not (rng[1] <= card_num <= rng[2]):
                                return False
                        else:
                            return False
                    else:
                        # Fallback to substring if not a valid numeric filter
                        if value.lower() not in str(card_val).lower():
                            return False
                else:
                    if value.lower() not in str(card_val).lower():
                        return False
            return True
        return [card for card in self.cards if matches(card)]

    def remove_cards(self, cards_to_remove):
        """Remove all cards in cards_to_remove from the inventory."""
        # Remove by identity or dict equality
        new_cards = [c for c in self.cards if c not in cards_to_remove]
        self.cards = new_cards

    def add_card(self, card):
        """Add a single card to the inventory."""
        self.cards.append(card.copy() if isinstance(card, dict) else card)
