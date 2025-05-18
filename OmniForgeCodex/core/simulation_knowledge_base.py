from PySide6.QtCore import QObject
from utils import save_json, load_json
from config import Config
import os
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

class SimulationKnowledgeBase(QObject):
    def __init__(self):
        super().__init__()
        self.data_path = Path(Config.SIMULATION_DATA_DIR) / "simulations.json"
        self.backup_path = self.data_path.with_suffix('.json.bak')
        self.max_simulations_per_deck = 1000
        self.max_storage_mb = 100
        self._load_data()

    def _load_data(self):
        try:
            if self.data_path.exists():
                # Create backup before loading
                shutil.copy2(self.data_path, self.backup_path)
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                self._validate_data()
            else:
                self.data = {}
        except Exception as e:
            print(f"Error loading data: {e}")
            if self.backup_path.exists():
                shutil.copy2(self.backup_path, self.data_path)
                self._load_data()
            else:
                self.data = {}
                
    def _validate_data(self):
        """Validate data structure and clean if necessary"""
        for deck_hash in list(self.data.keys()):
            if not isinstance(self.data[deck_hash], list):
                del self.data[deck_hash]
                continue
                
            # Prune old simulations
            if len(self.data[deck_hash]) > self.max_simulations_per_deck:
                self.data[deck_hash] = self.data[deck_hash][-self.max_simulations_per_deck:]
                
    def _check_storage(self):
        """Check if storage limit is exceeded"""
        if self.data_path.exists():
            size_mb = self.data_path.stat().st_size / (1024 * 1024)
            if size_mb > self.max_storage_mb:
                self._prune_old_data()
                
    def _prune_old_data(self):
        """Remove oldest simulations to free space"""
        for deck_hash in self.data:
            if len(self.data[deck_hash]) > self.max_simulations_per_deck:
                self.data[deck_hash] = self.data[deck_hash][-self.max_simulations_per_deck:]

    def record_simulation_results(self, deck_hash: str, parsed_log_events: dict, win_status: bool, performance_metrics: dict):
        if deck_hash not in self.data:
            self.data[deck_hash] = []

        self.data[deck_hash].append({
            "events": parsed_log_events,
            "win": win_status,
            "metrics": performance_metrics
        })
        save_json(self.data, self.data_path)

    def get_performance_data(self, card_name_or_id_or_combo: str) -> dict:
        metrics = {"win_rate": 0.0, "games": 0}
        for deck_hash, sims in self.data.items():
            for sim in sims:
                if card_name_or_id_or_combo in sim["events"].get("cards_played", []):
                    metrics["games"] += 1
                    if sim["win"]:
                        metrics["win_rate"] += 1
        if metrics["games"] > 0:
            metrics["win_rate"] /= metrics["games"]
        return metrics

    def get_successful_deck_archetypes(self, format: str) -> list:
        archetypes = {}
        for deck_hash, sims in self.data.items():
            archetype = sims[0]["metrics"].get("archetype", "unknown")
            wins = sum(1 for sim in sims if sim["win"])
            archetypes[archetype] = archetypes.get(archetype, 0) + wins
        return sorted(archetypes.items(), key=lambda x: x[1], reverse=True)
