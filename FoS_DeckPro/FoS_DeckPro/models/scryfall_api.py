import requests
from typing import Dict, Any

def fetch_scryfall_data(scryfall_id: str) -> Dict[str, Any]:
    """
    Fetch card data from Scryfall API including all price fields and purchase URIs.
    
    Args:
        scryfall_id: The Scryfall ID of the card to fetch
        
    Returns:
        Dict containing all card data including:
        - Basic card info (type_line, mana_cost, etc.)
        - Price fields (usd, usd_foil, usd_etched, eur, eur_foil, eur_etched, tix)
        - Purchase URIs (tcgplayer_url, cardmarket_url, cardhoarder_url)
        - Image URL
        - Legality info
    """
    url = f"https://api.scryfall.com/cards/{scryfall_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Get the image URL from the card data
        image_url = ""
        if "image_uris" in data:
            image_url = data["image_uris"].get("normal", "")
        elif "card_faces" in data and len(data["card_faces"]) > 0:
            # Handle double-faced cards
            image_url = data["card_faces"][0]["image_uris"].get("normal", "")
            
        # Extract price fields from the prices object
        prices = data.get("prices", {})
        usd = prices.get("usd", "")
        usd_foil = prices.get("usd_foil", "")
        usd_etched = prices.get("usd_etched", "")
        eur = prices.get("eur", "")
        eur_foil = prices.get("eur_foil", "")
        eur_etched = prices.get("eur_etched", "")
        tix = prices.get("tix", "")
        
        # Extract purchase URIs
        purchase_uris = data.get("purchase_uris", {})
        tcgplayer_url = purchase_uris.get("tcgplayer", "")
        cardmarket_url = purchase_uris.get("cardmarket", "")
        cardhoarder_url = purchase_uris.get("cardhoarder", "")
        
        return {
            # Basic card info
            "type_line": data.get("type_line", ""),
            "mana_cost": data.get("mana_cost", ""),
            "colors": ", ".join(data.get("colors", [])),
            "color_identity": ", ".join(data.get("color_identity", [])),
            "oracle_text": data.get("oracle_text", ""),
            "cmc": str(data.get("cmc", "")),
            "image_url": image_url,
            
            # Legality info
            "legal_commander": data.get("legalities", {}).get("commander", "unknown"),
            "legal_pauper": data.get("legalities", {}).get("pauper", "unknown"),
            
            # Price fields
            "usd": usd,
            "usd_foil": usd_foil,
            "usd_etched": usd_etched,
            "eur": eur,
            "eur_foil": eur_foil,
            "eur_etched": eur_etched,
            "tix": tix,
            
            # Purchase URIs
            "tcgplayer_url": tcgplayer_url,
            "cardmarket_url": cardmarket_url,
            "cardhoarder_url": cardhoarder_url
        }
    except Exception as e:
        print(f"❌ Error fetching {scryfall_id}: {e}")
        return {
            # Basic card info
            "type_line": "ERROR",
            "mana_cost": "",
            "colors": "",
            "color_identity": "",
            "oracle_text": "",
            "cmc": "",
            "image_url": "",
            
            # Legality info
            "legal_commander": "unknown",
            "legal_pauper": "unknown",
            
            # Price fields
            "usd": "",
            "usd_foil": "",
            "usd_etched": "",
            "eur": "",
            "eur_foil": "",
            "eur_etched": "",
            "tix": "",
            
            # Purchase URIs
            "tcgplayer_url": "",
            "cardmarket_url": "",
            "cardhoarder_url": ""
        }
