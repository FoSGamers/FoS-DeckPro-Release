import json
FONT_SETTINGS_PATH = "config/font_settings.json"

def get_font_settings(card_type, part):
    """
    Load font settings for a given card_type and part (title, subtype, body, stats).
    Returns a dict with keys:
      size, color, x, y, bold, italic, all_caps, underline, letter_spacing, line_spacing, shadow
    """
    try:
        with open(FONT_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(card_type, {}).get(part, {})
    except Exception as e:
        print(f"[DEBUG] Could not load font settings: {e}")
        return {}

def set_font_settings(card_type, part, settings):
    """
    Save font settings for a given card_type and part.
    Settings dict can include:
      size, color, x, y, bold, italic, all_caps, underline, letter_spacing, line_spacing, shadow
    """
    try:
        with open(FONT_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    if card_type not in data:
        data[card_type] = {}
    data[card_type][part] = settings
    with open(FONT_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False) 