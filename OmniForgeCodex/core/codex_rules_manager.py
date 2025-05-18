from PySide6.QtCore import QObject
from utils import load_json
from config import Config
import os
from functools import lru_cache

class CodexRulesManager(QObject):
    def __init__(self):
        super().__init__()
        self._load_rules()

    def _load_rules(self):
        try:
            self.rules = load_json(os.path.join(Config.DEFAULT_DATA_DIR, "codex_rules.json"))
            self.archetypes = load_json(os.path.join(Config.DEFAULT_DATA_DIR, "archetype_definitions.json"))
            self.staples = load_json(os.path.join(Config.DEFAULT_DATA_DIR, "staple_cards.json"))
        except Exception as e:
            self.rules = {}
            self.archetypes = {}
            self.staples = {}
            print(f"Error loading rules: {e}")

    @lru_cache(maxsize=1000)
    def get_staple_score(self, card_name: str, game_format: str, archetype: str) -> float:
        format_staples = self.staples.get(game_format, {})
        archetype_staples = format_staples.get(archetype, [])
        return 1.0 if card_name in archetype_staples else 0.0

    def get_archetype_fit_score(self, card_object: dict, archetype: str) -> float:
        archetype_def = self.archetypes.get(archetype, {})
        type_line = card_object.get("type_line", "").lower()
        cmc = card_object.get("cmc", 0)

        score = 0.0
        if "creature" in type_line and archetype_def.get("creature_weight", 0) > 0:
            score += archetype_def["creature_weight"]
        if "instant" in type_line and archetype_def.get("instant_weight", 0) > 0:
            score += archetype_def["instant_weight"]
        if cmc <= archetype_def.get("max_cmc", 6):
            score += 0.2
        return min(score, 1.0)

    def get_theme_fit_score(self, card_object: dict, themes: list) -> float:
        type_line = card_object.get("type_line", "").lower()
        for theme in themes:
            if theme.lower() in type_line or theme.lower() in card_object.get("oracle_text", "").lower():
                return 1.0
        return 0.0

    def get_synergy_score(self, card1_obj: dict, card2_obj: dict, deck_context: dict) -> float:
        tags1 = card1_obj.get("tags", [])
        tags2 = card2_obj.get("tags", [])
        common_tags = set(tags1) & set(tags2)
        return len(common_tags) * 0.3
