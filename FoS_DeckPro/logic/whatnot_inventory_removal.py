from typing import List, Dict, Any, Tuple, Callable
import copy
import difflib
import re

# Set code aliases for common sets (expand as needed)
SET_CODE_ALIASES = {
    'eld': ['eld', 'ELD', 'throne of eldraine'],
    'm21': ['m21', 'M21', 'core set 2021'],
    'pip': ['pip', 'PIP', 'fallout'],
    'tsr': ['tsr', 'TSR', 'time spiral remastered'],
    'm11': ['m11', 'M11', 'magic 2011'],
    # Add more as needed
}

# Normalize foil/normal values
FOIL_NORMAL_MAP = {
    'foil': ['foil', 'f', 'yes', 'true', '1'],
    'normal': ['normal', 'n', 'no', 'false', '0', ''],
    'etched': ['etched'],
}

def normalize_foil(val):
    val = str(val).strip().lower()
    for k, vlist in FOIL_NORMAL_MAP.items():
        if val in vlist:
            return k
    return val

def normalize_set_code(val):
    val = str(val).strip().lower()
    for canon, aliases in SET_CODE_ALIASES.items():
        if val in aliases:
            return canon
    return val

def fuzzy_name_match(name, candidates, threshold=0.7):
    """Return best fuzzy match from candidates if above threshold, else None. Now normalizes names by removing punctuation and spaces."""
    name_norm = normalize_name(name)
    candidates_norm = [normalize_name(c) for c in candidates]
    best = difflib.get_close_matches(name_norm, candidates_norm, n=1, cutoff=threshold)
    if best:
        # Return the original candidate that matches the normalized best
        idx = candidates_norm.index(best[0])
        return candidates[idx]
    return None

def normalize_name(val):
    # Lowercase, remove punctuation and extra spaces for robust matching
    return re.sub(r"[^a-z0-9 ]", "", str(val).strip().lower())

def normalize_collector_number(val):
    # Compare as exact string, do not strip leading zeros
    return str(val).strip().lower()

def normalize_language(val):
    return str(val).strip().lower()

def remove_sold_cards_from_inventory(
    inventory: List[Dict[str, Any]],
    sales: List[Dict[str, Any]],
    user_prompt_callback: Callable[[Dict[str, Any], List[Dict[str, Any]]], Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Remove sold cards from inventory using best-match logic.
    Returns (updated_inventory, removal_log).
    removal_log: list of dicts with keys: action (removed/not_found/ambiguous), sale, matched_card, reason
    user_prompt_callback: function(sale, matches) -> selected_card (for ambiguous cases)
    """
    updated_inventory = copy.deepcopy(inventory)
    removal_log = []
    def card_key(card):
        return (
            str(card.get('Name', '')).strip().lower(),
            str(card.get('Set code', '')).strip().lower(),
            str(card.get('Collector number', '')).strip().lower(),
            str(card.get('Foil', '')).strip().lower(),
            str(card.get('Language', '')).strip().lower(),
        )
    decremented_cards = set()
    decremented_to_zero = set()
    for sale in sales:
        matches, ambiguity_reason = _find_matches(updated_inventory, sale)
        if len(matches) == 1:
            card = matches[0]
            qty_to_remove = sale.get('Quantity', 1)
            inv_qty = int(card.get('Quantity', 1))
            if inv_qty >= qty_to_remove:
                card['Quantity'] = inv_qty - qty_to_remove
                decremented_cards.add(card_key(card))
                if card['Quantity'] == 0:
                    decremented_to_zero.add(card_key(card))
                removal_log.append({'action': 'removed', 'sale': sale, 'matched_card': card, 'reason': ''})
            else:
                card['Quantity'] = 0
                decremented_cards.add(card_key(card))
                decremented_to_zero.add(card_key(card))
                removal_log.append({'action': 'removed', 'sale': sale, 'matched_card': card, 'reason': f'Only {inv_qty} in inventory, needed {qty_to_remove}'})
        elif len(matches) == 0:
            removal_log.append({'action': 'not_found', 'sale': sale, 'matched_card': None, 'reason': 'No match in inventory'})
        else:
            if user_prompt_callback:
                selected = user_prompt_callback(sale, matches)
                if selected:
                    qty_to_remove = sale.get('Quantity', 1)
                    inv_qty = int(selected.get('Quantity', 1))
                    if inv_qty >= qty_to_remove:
                        selected['Quantity'] = inv_qty - qty_to_remove
                        decremented_cards.add(card_key(selected))
                        if selected['Quantity'] == 0:
                            decremented_to_zero.add(card_key(selected))
                        removal_log.append({'action': 'removed', 'sale': sale, 'matched_card': selected, 'reason': 'User selected from ambiguous'})
                    else:
                        selected['Quantity'] = 0
                        decremented_cards.add(card_key(selected))
                        decremented_to_zero.add(card_key(selected))
                        removal_log.append({'action': 'removed', 'sale': sale, 'matched_card': selected, 'reason': f'User selected from ambiguous, only {inv_qty} in inventory, needed {qty_to_remove}'})
                else:
                    removal_log.append({'action': 'ambiguous', 'sale': sale, 'matched_card': matches, 'reason': ambiguity_reason or f'{len(matches)} possible matches'})
            else:
                removal_log.append({'action': 'ambiguous', 'sale': sale, 'matched_card': matches, 'reason': ambiguity_reason or f'{len(matches)} possible matches'})
    # Only remove cards with Quantity 0 if they were decremented to zero by a removal
    updated_inventory = [c for c in updated_inventory if card_key(c) not in decremented_to_zero]
    return updated_inventory, removal_log

def _find_matches(inventory: List[Dict[str, Any]], sale: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Find inventory cards matching a sale. At least three fields must match, prioritizing collector number, foil/normal, and set code after name.
    If multiple languages are found and language is not specified, set ambiguity reason for user intervention.
    Returns (matches, ambiguity_reason).
    """
    sale_name = normalize_name(sale.get('Name', ''))
    sale_set_code = normalize_set_code(sale.get('Set code', ''))
    sale_collector = normalize_collector_number(sale.get('Collector number', ''))
    sale_foil = normalize_foil(sale.get('Foil', ''))
    sale_language = normalize_language(sale.get('Language', ''))

    # Build normalized inventory index
    norm_inv = []
    for c in inventory:
        norm = {
            'Name': normalize_name(c.get('Name', '')),
            'Set code': normalize_set_code(c.get('Set code', '')),
            'Collector number': normalize_collector_number(c.get('Collector number', '')),
            'Foil': normalize_foil(c.get('Foil', '')),
            'Language': normalize_language(c.get('Language', '')),
            'orig': c
        }
        norm_inv.append(norm)

    matches = []
    ambiguity_reason = ''

    # Score each card in inventory by number of matching fields (prioritize collector number, foil, set code)
    scored = []
    for n in norm_inv:
        score = 0
        if n['Name'] == sale_name:
            score += 1
        if n['Collector number'] == sale_collector and sale_collector:
            score += 1
        if n['Foil'] == sale_foil and sale_foil:
            score += 1
        if n['Set code'] == sale_set_code and sale_set_code:
            score += 1
        if sale_language and n['Language'] == sale_language:
            score += 1
        scored.append((score, n['orig']))
    max_score = max((s for s, _ in scored), default=0)
    # Only consider matches with at least 3 fields matching
    matches = [c for s, c in scored if s == max_score and s >= 3]
    if not matches:
        ambiguity_reason = 'No match with at least 3 fields'
    # If multiple matches and only language differs, set ambiguity reason
    if matches and len(matches) > 1:
        fields = ['Name', 'Set code', 'Collector number', 'Foil']
        first = matches[0]
        if all(all(normalize_name(c.get(f, '')) == normalize_name(first.get(f, '')) for f in fields) for c in matches):
            languages = set(normalize_language(c.get('Language', '')) for c in matches)
            if len(languages) > 1:
                ambiguity_reason = 'Multiple languages in inventory, language not specified or not found in sale (language ambiguity)'
    return matches, ambiguity_reason 