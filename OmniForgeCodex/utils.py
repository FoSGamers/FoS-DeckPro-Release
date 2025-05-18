import csv
import json
import os
from typing import List, Dict, Any, Optional, Union

def parse_csv_with_headers(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]
    except Exception as e:
        raise ValueError(f"Failed to parse CSV: {e}")

def save_json(data: Any, file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(file_path: str) -> Any:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load JSON: {e}")

def validate_card_name(name: str, scryfall_client: Any) -> bool:
    try:
        data = scryfall_client.enrich_card_data(name, ["name"])
        return bool(data)
    except:
        return False
