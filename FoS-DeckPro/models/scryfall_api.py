import requests

def fetch_scryfall_data(scryfall_id):
    """Fetch card data from Scryfall API, including all available price fields and purchase URIs."""
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
        # Get price fields
        prices = data.get("prices", {})
        # Get purchase URIs
        purchase_uris = data.get("purchase_uris", {})
        return {
            "type_line": data.get("type_line", ""),
            "mana_cost": data.get("mana_cost", ""),
            "colors": ", ".join(data.get("colors", [])),
            "color_identity": ", ".join(data.get("color_identity", [])),
            "oracle_text": data.get("oracle_text", ""),
            "legal_commander": data.get("legalities", {}).get("commander", "unknown"),
            "legal_pauper": data.get("legalities", {}).get("pauper", "unknown"),
            "image_url": image_url,
            # Scryfall price fields
            "price_usd": prices.get("usd"),
            "price_usd_foil": prices.get("usd_foil"),
            "price_usd_etched": prices.get("usd_etched"),
            "price_eur": prices.get("eur"),
            "price_eur_foil": prices.get("eur_foil"),
            "price_eur_etched": prices.get("eur_etched"),
            "price_tix": prices.get("tix"),
            # Scryfall purchase URIs
            "buy_tcgplayer": purchase_uris.get("tcgplayer"),
            "buy_cardmarket": purchase_uris.get("cardmarket"),
            "buy_cardhoarder": purchase_uris.get("cardhoarder"),
            "buy_mtgo": purchase_uris.get("mtgo"),
            "buy_cardkingdom": purchase_uris.get("cardkingdom"),
            "buy_cardkingdom_foil": purchase_uris.get("cardkingdom_foil"),
        }
    except Exception as e:
        print(f"❌ Error fetching {scryfall_id}: {e}")
        return {
            "type_line": "ERROR",
            "mana_cost": "",
            "colors": "",
            "color_identity": "",
            "oracle_text": "",
            "legal_commander": "unknown",
            "legal_pauper": "unknown",
            "image_url": "",
            "price_usd": None,
            "price_usd_foil": None,
            "price_usd_etched": None,
            "price_eur": None,
            "price_eur_foil": None,
            "price_eur_etched": None,
            "price_tix": None,
            "buy_tcgplayer": None,
            "buy_cardmarket": None,
            "buy_cardhoarder": None,
            "buy_mtgo": None,
            "buy_cardkingdom": None,
            "buy_cardkingdom_foil": None,
        }
