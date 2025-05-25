import requests

def fetch_scryfall_data(scryfall_id):
    """Fetch card data from Scryfall API"""
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
        return {
            "type_line": data.get("type_line", ""),
            "mana_cost": data.get("mana_cost", ""),
            "colors": ", ".join(data.get("colors", [])),
            "color_identity": ", ".join(data.get("color_identity", [])),
            "oracle_text": data.get("oracle_text", ""),
            "legal_commander": data.get("legalities", {}).get("commander", "unknown"),
            "legal_pauper": data.get("legalities", {}).get("pauper", "unknown"),
            "image_url": image_url
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
            "image_url": ""
        }
