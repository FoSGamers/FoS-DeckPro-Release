import json

def load_wasteland_json(json_path="wasteland_odyssey.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f) 