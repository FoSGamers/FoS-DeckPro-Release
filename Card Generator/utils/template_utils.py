import os
import json

TEMPLATE_DIR = os.path.join('config', 'templates')

def save_template(template_name, card_type, font_settings, checked_fields, layout_settings=None, style_settings=None):
    """
    Save a card template (font, layout, style, checked fields) for a card type.
    """
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    template = {
        'card_type': card_type,
        'font_settings': font_settings,
        'checked_fields': checked_fields,
        'layout_settings': layout_settings or {},
        'style_settings': style_settings or {},
    }
    path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    return path

def load_template(template_name):
    """
    Load a card template by name.
    """
    path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template '{template_name}' not found.")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_templates():
    """
    List all available template names.
    """
    if not os.path.exists(TEMPLATE_DIR):
        return []
    return [f[:-5] for f in os.listdir(TEMPLATE_DIR) if f.endswith('.json')] 