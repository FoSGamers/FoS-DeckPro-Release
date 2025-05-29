from typing import List, Dict, Any, Tuple
import copy

def remove_sold_cards_from_inventory(inventory: List[Dict[str, Any]], sales: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Remove sold cards from inventory using best-match logic.
    Returns (updated_inventory, removal_log).
    removal_log: list of dicts with keys: action (removed/not_found/ambiguous), sale, matched_card, reason
    """
    updated_inventory = copy.deepcopy(inventory)
    removal_log = []
    for sale in sales:
        matches = _find_matches(updated_inventory, sale)
        if len(matches) == 1:
            card = matches[0]
            # Remove quantity
            qty_to_remove = sale.get('Quantity', 1)
            inv_qty = int(card.get('Quantity', 1))
            if inv_qty >= qty_to_remove:
                card['Quantity'] = inv_qty - qty_to_remove
                removal_log.append({'action': 'removed', 'sale': sale, 'matched_card': card, 'reason': ''})
            else:
                # Remove all, but log shortfall
                card['Quantity'] = 0
                removal_log.append({'action': 'removed', 'sale': sale, 'matched_card': card, 'reason': f'Only {inv_qty} in inventory, needed {qty_to_remove}'})
        elif len(matches) == 0:
            removal_log.append({'action': 'not_found', 'sale': sale, 'matched_card': None, 'reason': 'No match in inventory'})
        else:
            removal_log.append({'action': 'ambiguous', 'sale': sale, 'matched_card': matches, 'reason': f'{len(matches)} possible matches'})
    # Remove cards with Quantity 0
    updated_inventory = [c for c in updated_inventory if int(c.get('Quantity', 1)) > 0]
    return updated_inventory, removal_log

def _find_matches(inventory: List[Dict[str, Any]], sale: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Try strict match on all fields
    fields = ['Name', 'Set code', 'Collector number', 'Language', 'Foil']
    strict = [c for c in inventory if all(str(c.get(f, '')).lower() == str(sale.get(f, '')).lower() for f in fields)]
    if strict:
        return strict
    # Relax to Name + Set code + Collector number
    fields2 = ['Name', 'Set code', 'Collector number']
    loose = [c for c in inventory if all(str(c.get(f, '')).lower() == str(sale.get(f, '')).lower() for f in fields2)]
    return loose 