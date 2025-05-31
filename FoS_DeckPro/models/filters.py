def filter_cards(cards, filters):
    """
    Filter a list of card dicts by a dict of {column: value} filters.
    Returns a new list of cards matching all filters.
    """
    def matches(card):
        for key, value in filters.items():
            if value and value.lower() not in str(card.get(key, "")).lower():
                return False
        return True
    return [card for card in cards if matches(card)]
