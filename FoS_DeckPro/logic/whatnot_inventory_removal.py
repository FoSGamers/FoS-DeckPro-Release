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
    Remove sold cards from inventory. For each sale, try to find a matching card in inventory and remove it.
    Returns (updated_inventory, removal_log)
    """
    updated_inventory = inventory.copy()
    removal_log = []
    for sale in sales:
        print(f"\n=== PROCESSING SALE ===\n{sale}")
        matches, ambiguity_reason = _find_matches(updated_inventory, sale)
        print(f"DEBUG: Matches found: {len(matches)} | Ambiguity: {ambiguity_reason}")
        if len(matches) == 1:
            # Remove the card
            match = matches[0]
            print(f"REMOVED: {match}")
            updated_inventory.remove(match)
            removal_log.append({'action': 'removed', 'sale': sale, 'match': match})
        elif len(matches) > 1:
            print(f"AMBIGUOUS: Multiple matches found for sale: {sale}")
            if user_prompt_callback:
                selected = user_prompt_callback(sale, matches)
                if selected:
                    print(f"USER SELECTED: {selected}")
                    updated_inventory.remove(selected)
                    removal_log.append({'action': 'removed', 'sale': sale, 'match': selected})
                else:
                    removal_log.append({'action': 'ambiguous', 'sale': sale, 'matches': matches, 'reason': ambiguity_reason})
            else:
                removal_log.append({'action': 'ambiguous', 'sale': sale, 'matches': matches, 'reason': ambiguity_reason})
        else:
            print(f"NOT FOUND: No match for sale: {sale}")
            removal_log.append({'action': 'not_found', 'sale': sale})
    return updated_inventory, removal_log

def _find_matches(inventory: List[Dict[str, Any]], sale: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    """
    Find inventory cards matching a sale. At least three fields must match, including name.
    Returns (matches, ambiguity_reason).
    """
    def norm(val):
        return str(val).strip().lower() if val is not None else ''
    sale_fields = ['Name', 'Collector number', 'Foil', 'Set code', 'Language']
    sale_norm = {f: norm(sale.get(f, '')) for f in sale_fields}
    print(f"DEBUG: Sale normalized fields: {sale_norm}")
    candidates = []
    for card in inventory:
        card_norm = {f: norm(card.get(f, '')) for f in sale_fields}
        # Count matching fields (name must match)
        match_count = sum(sale_norm[f] == card_norm[f] and sale_norm[f] != '' for f in sale_fields)
        print(f"DEBUG: Candidate card: {card_norm} | match_count: {match_count}")
        if sale_norm['Name'] == card_norm['Name'] and match_count >= 3:
            candidates.append(card)
    if candidates:
        return candidates, ''
    # Fallback: try 2 fields
    for card in inventory:
        card_norm = {f: norm(card.get(f, '')) for f in sale_fields}
        match_count = sum(sale_norm[f] == card_norm[f] and sale_norm[f] != '' for f in sale_fields)
        if sale_norm['Name'] == card_norm['Name'] and match_count >= 2:
            print(f"DEBUG: Fallback 2-field match: {card_norm}")
            candidates.append(card)
    if candidates:
        return candidates, 'matched on 2 fields'
    # Fallback: just name
    for card in inventory:
        card_norm = {f: norm(card.get(f, '')) for f in sale_fields}
        if sale_norm['Name'] == card_norm['Name']:
            print(f"DEBUG: Fallback name-only match: {card_norm}")
            candidates.append(card)
    if candidates:
        return candidates, 'matched on name only'
    return [], 'no match found' 