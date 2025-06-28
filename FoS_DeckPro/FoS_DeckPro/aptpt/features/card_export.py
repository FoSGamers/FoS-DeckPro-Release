from typing import Dict, Any, List
import json
import csv
from datetime import datetime
from FoS_DeckPro.aptpt import log_aptpt_event

def export_cards_to_csv(cards: List[Dict[str, Any]], filename: str) -> bool:
    """Export cards to a CSV file."""
    try:
        # Get all unique fields
        fields = set()
        for card in cards:
            fields.update(card.keys())
        
        # Write CSV
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fields))
            writer.writeheader()
            writer.writerows(cards)
        
        # Log success
        log_aptpt_event(
            'info',
            'Cards exported successfully',
            {
                'filename': filename,
                'card_count': len(cards)
            }
        )
        
        return True
        
    except Exception as e:
        # Log error
        log_aptpt_event(
            'error',
            'Failed to export cards',
            {
                'filename': filename,
                'error': str(e)
            }
        )
        
        return False

def export_cards_to_json(cards: List[Dict[str, Any]], filename: str) -> bool:
    """Export cards to a JSON file."""
    try:
        # Write JSON
        with open(filename, 'w') as f:
            json.dump(cards, f, indent=2)
        
        # Log success
        log_aptpt_event(
            'info',
            'Cards exported successfully',
            {
                'filename': filename,
                'card_count': len(cards)
            }
        )
        
        return True
        
    except Exception as e:
        # Log error
        log_aptpt_event(
            'error',
            'Failed to export cards',
            {
                'filename': filename,
                'error': str(e)
            }
        )
        
        return False

def get_feature_info() -> Dict[str, Any]:
    """Get feature information."""
    return {
        'name': 'card_export',
        'description': 'Export cards to CSV or JSON format',
        'requirements': [
            'card_data_loaded',
            'write_permission'
        ],
        'dependencies': [],
        'implementation': {
            'csv': export_cards_to_csv,
            'json': export_cards_to_json
        }
    } 