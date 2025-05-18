import time
import requests
from PySide6.QtCore import QObject, Signal
from config import Config

class ScryfallClient(QObject):
    progress = Signal(str)

    def __init__(self):
        super().__init__()
        self.base_url = Config.SCRYFALL_API_URL
        self.delay = Config.SCRYFALL_REQUEST_DELAY

    def enrich_card_data(self, card_identifier: str, fields_needed: list) -> dict:
        max_retries = 3
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                time.sleep(self.delay)
                url = f"{self.base_url}/cards/named?exact={card_identifier}"
                response = requests.get(url)
                
                if response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', retry_delay))
                    time.sleep(retry_after)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                return self._process_card_data(data)
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    self.progress.emit(f"Error enriching {card_identifier}: {e}")
                    return {}
                time.sleep(retry_delay * (attempt + 1))

    def batch_enrich_cards(self, card_identifiers: list, batch_size: int = 75) -> list:
        results = []
        for i in range(0, len(card_identifiers), batch_size):
            batch = card_identifiers[i:i + batch_size]
            self.progress.emit(f"Enriching cards {i+1}-{min(i+batch_size, len(card_identifiers))}/{len(card_identifiers)}")
            
            # Use Scryfall's bulk endpoint if available
            if len(batch) > 1:
                try:
                    url = f"{self.base_url}/cards/collection"
                    response = requests.post(url, json={"identifiers": [{"name": name} for name in batch]})
                    response.raise_for_status()
                    results.extend(response.json()["data"])
                except Exception as e:
                    self.progress.emit(f"Batch error: {e}")
                    # Fall back to individual requests
                    for card in batch:
                        data = self.enrich_card_data(card, ["all"])
                        if data:
                            results.append(data)
            else:
                data = self.enrich_card_data(batch[0], ["all"])
                if data:
                    results.append(data)
                
            time.sleep(self.delay)
        return results

    def get_card_tags(self, card_name: str) -> list:
        tags = {
            "Lightning Bolt": ["burn", "removal"],
            "Counterspell": ["counter", "control"],
            "Delver of Secrets": ["tempo", "creature"]
        }
        return tags.get(card_name, [])

    def get_synergistic_cards(self, card_name: str, commander_name: str = None, format: str = None) -> list:
        synergies = {
            "Delver of Secrets": ["Ponder", "Brainstorm"],
            "Counterspell": ["Negate", "Mana Leak"]
        }
        return synergies.get(card_name, [])

    def _process_card_data(self, data: dict) -> dict:
        result = {
            "name": data.get("name", ""),
            "scryfall_id": data.get("id", ""),
            "type_line": data.get("type_line", ""),
            "cmc": data.get("cmc", 0),
            "colors": data.get("colors", []),
            "color_identity": data.get("color_identity", []),
            "legalities": data.get("legalities", {}),
            "oracle_text": data.get("oracle_text", ""),
            "prices": data.get("prices", {"usd": None}),
            "tags": self.get_card_tags(data.get("name"))
        }
        return result
