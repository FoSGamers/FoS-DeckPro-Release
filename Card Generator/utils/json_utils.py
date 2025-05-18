import json
from utils.card_helpers import get_card_name
from config.constants import WASTELAND_JSON_PATH

CARD_BACK_FIELDS_PATH = "config/card_back_fields.json"

def add_card_to_json(card, card_type):
    # Load JSON
    with open(WASTELAND_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Check for duplicates by name or id
    section = data.get(card_type, [])
    name = get_card_name(card)
    card_id = card.get('id', None)
    for entry in section:
        if (entry.get('name') == name) or (card_id and entry.get('id') == card_id):
            return  # Already exists
    # Add card
    section.append(card)
    data[card_type] = section
    # Save JSON
    with open(WASTELAND_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_card_back_fields(card_type):
    """
    Load the list of fields to show on the back of a card for the given card_type.
    Returns a list of field names.
    """
    try:
        with open(CARD_BACK_FIELDS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(card_type, [])
    except Exception as e:
        print(f"[DEBUG] Could not load card back fields config: {e}")
        return []

def set_card_back_fields(card_type, fields):
    """
    Save the list of fields to show on the back of a card for the given card_type.
    """
    try:
        with open(CARD_BACK_FIELDS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data[card_type] = fields
    with open(CARD_BACK_FIELDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False) 