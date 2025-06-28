"""
Scryfall API integration for FoS_DeckPro
"""

import requests
import json
from typing import Dict, Any, Optional

def fetch_scryfall_data(card_identifier: str) -> Optional[Dict[str, Any]]:
    """
    Fetch card data from Scryfall API
    
    Args:
        card_identifier: Name or Scryfall ID of the card to fetch
        
    Returns:
        Dictionary containing card data or None if not found
    """
    try:
        # Try as Scryfall ID first (UUID format)
        if len(card_identifier) == 36 and '-' in card_identifier:
            url = f"https://api.scryfall.com/cards/{card_identifier}"
        else:
            # Try as card name with fuzzy search
            url = f"https://api.scryfall.com/cards/named?fuzzy={card_identifier}"
        
        response = requests.get(url)
        response.raise_for_status()
        card_data = response.json()
        
        # Extract useful fields for our app
        enriched_data = {
            'Name': card_data.get('name', ''),
            'Set name': card_data.get('set_name', ''),
            'Set code': card_data.get('set', ''),
            'Collector number': card_data.get('collector_number', ''),
            'Rarity': card_data.get('rarity', ''),
            'Type': card_data.get('type_line', ''),
            'Mana cost': card_data.get('mana_cost', ''),
            'Power': card_data.get('power', ''),
            'Toughness': card_data.get('toughness', ''),
            'Text': card_data.get('oracle_text', ''),
            'Artist': card_data.get('artist', ''),
            'Scryfall ID': card_data.get('id', ''),
            'image_url': card_data.get('image_uris', {}).get('normal', ''),
        }
        
        # Add pricing information
        if 'prices' in card_data:
            prices = card_data['prices']
            if 'usd' in prices and prices['usd']:
                enriched_data['Scryfall Price'] = f"${prices['usd']}"
            if 'usd_foil' in prices and prices['usd_foil']:
                enriched_data['Scryfall Foil Price'] = f"${prices['usd_foil']}"
        
        return enriched_data
        
    except requests.RequestException as e:
        print(f"Error fetching data for {card_identifier}: {e}")
        return None

def get_card_price(card_name: str, foil: bool = False) -> Optional[float]:
    """
    Get card price from Scryfall
    
    Args:
        card_name: Name of the card
        foil: Whether to get foil price
        
    Returns:
        Price as float or None if not available
    """
    card_data = fetch_scryfall_data(card_name)
    if not card_data:
        return None
    
    try:
        if foil and 'prices' in card_data and 'usd_foil' in card_data['prices']:
            price_str = card_data['prices']['usd_foil']
        elif 'prices' in card_data and 'usd' in card_data['prices']:
            price_str = card_data['prices']['usd']
        else:
            return None
            
        return float(price_str) if price_str else None
    except (ValueError, KeyError):
        return None 