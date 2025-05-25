# deck_learning_engine.py

import json
import os
from typing import List, Dict

LEARNING_DB = "deck_stats.json"

# Load or create the learning database
def load_learning_db() -> Dict:
    if os.path.exists(LEARNING_DB):
        with open(LEARNING_DB, 'r') as f:
            return json.load(f)
    else:
        return {}

# Save updated stats to DB
def save_learning_db(db: Dict):
    with open(LEARNING_DB, 'w') as f:
        json.dump(db, f, indent=2)

# Update card win contribution stats
def update_win_stats(deck: List[Dict], won: bool):
    db = load_learning_db()
    for card in deck:
        name = card['Name']
        if name not in db:
            db[name] = {'wins': 0, 'losses': 0}
        if won:
            db[name]['wins'] += 1
        else:
            db[name]['losses'] += 1
    save_learning_db(db)

# Get card performance modifier
def get_card_performance_score(name: str, db: Dict) -> float:
    stats = db.get(name)
    if not stats:
        return 0.0
    total = stats['wins'] + stats['losses']
    if total == 0:
        return 0.0
    win_rate = stats['wins'] / total
    return (win_rate - 0.5) * 4  # score ranges from -2.0 to +2.0

# Enhanced synergy logic using learning feedback
def smart_analyze_synergy(cards: List[Dict]) -> Dict[str, float]:
    base_scores = {}
    db = load_learning_db()
    for card in cards:
        text = card.get("oracle_text", "").lower()
        name = card["Name"]
        score = 0
        if "draw" in text:
            score += 2.0
        if "damage" in text or "counter" in text:
            score += 1.5
        if "haste" in text or "first strike" in text:
            score += 1.2
        if "mana" in text or "ramp" in text:
            score += 1.0
        if "lifelink" in text or "gain life" in text:
            score += 0.8
        score += get_card_performance_score(name, db)
        base_scores[name] = score
    return base_scores
