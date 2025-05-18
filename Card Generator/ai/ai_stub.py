def generate_card_json(prompt, count=1, card_type=None, data_list=None, schema=None, db_entries=None):
    if db_entries:
        return db_entries
    # Try to match prompt to an entry in data_list
    if data_list:
        matches = [entry for entry in data_list if prompt.lower() in str(entry.get('name', '')).lower()]
        if matches:
            # Return up to count matches
            return matches[:count]
    # Otherwise, return dummy cards for the type
    return [{
        "Title": f"Generated-{card_type or 'Card'}-{i+1}",
        "CardType": card_type or "Unknown",
        "Subtype": "Generated",
        "Stats": {"HP": 80, "STR": 5, "AGI": 4, "INT": 3, "ENG": 2, "LUCK": 1},
        "Ability": {"Name": "Lash", "Effect": "Roll 2d6. On 10+, deal 8 damage.", "Trigger": "On hit"},
        "Loot": ["+10 POGs", "Vault Tooth"],
        "Lore": f"Auto-generated {card_type or 'card'}.",
        "FrontImagePrompt": f"A {card_type or 'card'} in the wasteland",
        "BackImagePrompt": f"A {card_type or 'card'} back scene"
    } for i in range(count)] 