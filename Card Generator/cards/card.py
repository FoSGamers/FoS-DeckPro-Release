import os
from datetime import datetime
from .image_utils import generate_image_from_prompt, overlay_card, generate_borderless_art_image
from ai.ai_stub import generate_card_json
from utils.json_loader import load_wasteland_json
from utils.json_utils import get_card_back_fields
from utils.card_helpers import get_card_name, get_card_subtext, get_card_story, resolve_name

def get_card_stats(card, card_type, data_list=None):
    """
    Compose stats/info for the back of the card, only including fields selected for the card type.
    Shows real item/weapon names instead of keys/IDs.
    Only fields currently checked in config/card_back_fields.json are rendered.
    Handles missing/optional fields gracefully. Always resolves names for references.
    """
    if not isinstance(card, dict):
        return ''
    # Always reload config to avoid stale field selections
    from utils.json_utils import get_card_back_fields as reload_card_back_fields
    selected_fields = set(reload_card_back_fields(card_type))
    lines = []
    from utils.card_helpers import resolve_name as shared_resolve_name
    # Debug: show which fields are being rendered
    print(f"[DEBUG] Rendering card back for type '{card_type}' with fields: {selected_fields}")
    # Players/Enemies
    if card_type in ['players', 'enemies']:
        stats = card.get('Stats') or card.get('stats')
        if 'Stats' in selected_fields and stats:
            lines.append('Stats:')
            for k, v in stats.items():
                lines.append(f"  {k.upper()}: {v}")
        if 'AC' in selected_fields:
            ac = card.get('ac')
            if ac is not None:
                lines.append(f"AC: {ac}")
        if 'Equipment' in selected_fields:
            eq = card.get('equipment')
            if eq:
                lines.append('Equipment:')
                for k, v in eq.items():
                    lines.append(f"  {k.capitalize()}: {shared_resolve_name(v, data_list)}")
        if 'Buffs' in selected_fields:
            buffs = card.get('buffs')
            if buffs:
                lines.append('Buffs:')
                for b in buffs:
                    lines.append(f"  {shared_resolve_name(b, data_list)}")
        if 'Inventory' in selected_fields:
            inv = card.get('inventory')
            if inv:
                lines.append('Inventory:')
                for i in inv:
                    lines.append(f"  {shared_resolve_name(i, data_list)}")
    elif card_type == 'weapons':
        if 'Damage' in selected_fields:
            dmg = card.get('damage_dice', '')
            if dmg:
                lines.append(f"Damage: {dmg}")
        if 'Hit Modifier' in selected_fields:
            hit_mod = card.get('hit_modifier', '')
            if hit_mod != '':
                lines.append(f"Hit Modifier: {hit_mod}")
        if 'Type' in selected_fields:
            typ = card.get('type', '')
            if typ:
                lines.append(f"Type: {typ}")
        if 'Special Effects' in selected_fields:
            effects = card.get('special_effects')
            if effects:
                lines.append('Special Effects:')
                for eff in effects:
                    lines.append(f"  {shared_resolve_name(eff, data_list)}")
    elif card_type == 'armor':
        if 'Damage Resistance' in selected_fields:
            dr = card.get('damage_resistance')
            if dr:
                lines.append('Damage Resistance:')
                for k, v in dr.items():
                    lines.append(f"  {k.capitalize()}: {v}")
        if 'Hit Modifier' in selected_fields:
            hit_mod = card.get('hit_modifier', '')
            if hit_mod != '':
                lines.append(f"Hit Modifier: {hit_mod}")
        if 'Dodge Modifier' in selected_fields:
            dodge_mod = card.get('dodge_modifier', '')
            if dodge_mod != '':
                lines.append(f"Dodge Modifier: {dodge_mod}")
    elif card_type == 'items':
        if 'Type' in selected_fields:
            typ = card.get('type', '')
            if typ:
                lines.append(f"Type: {typ}")
        if 'Hit Modifier' in selected_fields:
            hit_mod = card.get('hit_modifier', '')
            if hit_mod != '':
                lines.append(f"Hit Modifier: {hit_mod}")
        if 'Properties' in selected_fields:
            props = card.get('properties')
            if props:
                lines.append('Properties:')
                for k, v in props.items():
                    lines.append(f"  {k}: {shared_resolve_name(v, data_list)}")
    elif card_type == 'locations':
        if 'Glossary' in selected_fields:
            lines.append('Glossary:')
            for key in ['events', 'enemies', 'items', 'sub_locations', 'environmental_effects']:
                val = card.get(key)
                if val:
                    lines.append(f"  {key.replace('_', ' ').capitalize()}: {shared_resolve_name(val, data_list)}")
    elif card_type == 'vendors':
        if 'Location' in selected_fields:
            loc = card.get('location', '')
            if loc:
                lines.append(f"Location: {loc}")
        if 'Inventory' in selected_fields:
            inv = card.get('inventory', '')
            if inv:
                lines.append(f"Inventory: {shared_resolve_name(inv, data_list)}")
    elif card_type == 'buffs':
        if 'Effect' in selected_fields:
            eff = card.get('effect', '')
            if eff:
                lines.append(f"Effect: {eff}")
        if 'Duration' in selected_fields:
            dur = card.get('duration', '')
            if dur:
                lines.append(f"Duration: {dur}")
    elif card_type == 'events':
        if 'Dice' in selected_fields:
            dice = card.get('dice', '')
            if dice:
                lines.append(f"Dice: {dice}")
        if 'Success Threshold' in selected_fields:
            st = card.get('success_threshold', '')
            if st != '':
                lines.append(f"Success Threshold: {st}")
        if 'Stat Bonuses' in selected_fields:
            sb = card.get('stat_bonuses', '')
            if sb:
                lines.append(f"Stat Bonuses: {sb}")
        if 'Loot' in selected_fields:
            loot = card.get('loot', '')
            if loot:
                lines.append(f"Loot: {shared_resolve_name(loot, data_list)}")
    # Only return non-empty lines
    return '\n'.join([l for l in lines if l and str(l).strip()])

def get_card_image_filenames(card, card_type):
    name = get_card_name(card)
    title = name.replace(" ", "_")
    card_id = card.get('id', None) if isinstance(card, dict) else None
    if card_id:
        front = f"{title}_{card_id}_front.png"
        back = f"{title}_{card_id}_back.png"
    else:
        front = f"{title}_front.png"
        back = f"{title}_back.png"
    return front, back

def generate_cards_batch(prompt, count, card_type, db_entries=None, font_path=None):
    wasteland_data = load_wasteland_json()
    schema = wasteland_data.get("schema", {}).get(card_type, {})
    data_list = wasteland_data.get(card_type, [])
    if db_entries:
        cards = generate_card_json("", len(db_entries), card_type=card_type, data_list=data_list, schema=schema, db_entries=db_entries)
    else:
        cards = generate_card_json(prompt, count, card_type=card_type, data_list=data_list, schema=schema)
    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    base_dir = os.path.join('generated_cards', today)
    for card in cards:
        card_type_dir = card.get('CardType', card_type) if isinstance(card, dict) else card_type
        card_type_dir = card_type_dir or card_type
        type_dir = os.path.join(base_dir, card_type_dir)
        os.makedirs(type_dir, exist_ok=True)
        name = get_card_name(card)
        subtext = get_card_subtext(card, card_type)
        story = get_card_story(card, card_type)
        stats = get_card_stats(card, card_type, data_list)
        title = name.replace(" ", "_")
        front_path, back_path = get_card_image_filenames(card, card_type)
        front_prompt = name
        if isinstance(card, dict):
            desc = card.get('description') or card.get('Lore') or ''
            if desc:
                front_prompt = f"{name}: {desc}"
        generate_image_from_prompt(front_prompt, front_path)
        overlay_card(front_path, front_path, name, subtext, mode="front", font_path=font_path)
        back_text = f"{name}\n\n{story}\n\n{stats}".strip()
        generate_image_from_prompt(name, back_path)
        overlay_card(back_path, back_path, name, subtext, back_text, mode="back", font_path=font_path)
        if not os.path.exists(front_path):
            print(f"[DEBUG] Front image not created: {front_path}")
        if not os.path.exists(back_path):
            print(f"[DEBUG] Back image not created: {back_path}")
        if isinstance(card, dict):
            card['_date_folder'] = today
        results.append(card)
    return results

def regenerate_card_images(card, card_type, font_path=None):
    """
    Regenerate the front and back images for a single card using the latest font settings.
    """
    wasteland_data = load_wasteland_json()
    data_list = wasteland_data.get(card_type, [])
    name = get_card_name(card)
    subtext = get_card_subtext(card, card_type)
    story = get_card_story(card, card_type)
    stats = get_card_stats(card, card_type, data_list)
    title = name.replace(" ", "_")
    today = card.get('_date_folder') if isinstance(card, dict) else None
    card_type_dir = card.get('CardType', card_type) if isinstance(card, dict) else card_type
    card_type_dir = card_type_dir or card_type
    if today:
        base_dir = os.path.join('generated_cards', today)
    else:
        base_dir = 'generated_cards'
    type_dir = os.path.join(base_dir, card_type_dir)
    os.makedirs(type_dir, exist_ok=True)
    front_path, back_path = get_card_image_filenames(card, card_type)
    front_prompt = name
    if isinstance(card, dict):
        desc = card.get('description') or card.get('Lore') or ''
        if desc:
            front_prompt = f"{name}: {desc}"
    generate_image_from_prompt(front_prompt, front_path)
    overlay_card(front_path, front_path, name, subtext, mode="front", font_path=font_path)
    back_text = f"{name}\n\n{story}\n\n{stats}".strip()
    generate_image_from_prompt(name, back_path)
    overlay_card(back_path, back_path, name, subtext, back_text, mode="back", font_path=font_path)
    if not os.path.exists(front_path):
        print(f"[DEBUG] Front image not created: {front_path}")
    if not os.path.exists(back_path):
        print(f"[DEBUG] Back image not created: {back_path}")
    if isinstance(card, dict):
        card['_date_folder'] = today
    return card 