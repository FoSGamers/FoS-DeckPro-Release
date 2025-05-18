# Shared card helper functions for use across modules

def get_card_name(card):
    if isinstance(card, dict):
        return card.get('Title') or card.get('name') or card.get('id', 'Card')
    return str(card)

def get_card_subtext(card, card_type):
    if not isinstance(card, dict):
        return card_type.capitalize()
    if card_type == 'players':
        return 'Player'
    if card_type == 'enemies':
        subtype = card.get('Subtype') or card.get('subtype')
        return f"Creature{f' – {subtype}' if subtype else ''}"
    if card_type == 'weapons':
        return 'Weapon'
    if card_type == 'armor':
        return 'Armor'
    if card_type == 'items':
        return 'Item'
    if card_type == 'locations':
        return 'Location'
    if card_type == 'vendors':
        return 'Vendor'
    if card_type == 'buffs':
        return 'Buff'
    if card_type == 'events':
        return 'Event'
    return card_type.capitalize()

def get_card_story(card, card_type):
    if not isinstance(card, dict):
        return ''
    return card.get('Lore') or card.get('description') or card.get('story') or card.get('details', '')

def resolve_name(val, data_list=None):
    # Handle lists of values (e.g., inventory, equipment)
    if isinstance(val, list):
        return ', '.join([resolve_name(v, data_list) for v in val])
    # Handle dicts with name/title
    if isinstance(val, dict) and ('name' in val or 'Title' in val):
        return val.get('name') or val.get('Title')
    # Try to resolve string IDs to names using data_list
    if isinstance(val, str):
        if data_list:
            for entry in data_list:
                if entry.get('id') == val or entry.get('name') == val or entry.get('Title') == val:
                    return entry.get('name') or entry.get('Title') or val
        return val
    return str(val) 