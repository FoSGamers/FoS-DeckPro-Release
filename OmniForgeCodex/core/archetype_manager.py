from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

class ArchetypeManager:
    def __init__(self):
        self.archetypes: Dict[str, Dict[str, Any]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.load_archetypes()
        
    def load_archetypes(self):
        """Load archetype definitions with validation"""
        try:
            with open(Path("resources/default_data/archetype_definitions.json"), 'r') as f:
                self.archetypes = json.load(f)
            self._validate_archetypes()
            self._load_metadata()
        except Exception as e:
            logging.error(f"Error loading archetypes: {e}")
            
    def _validate_archetypes(self):
        """Validate archetype definitions"""
        required_fields = {'creature_weight', 'instant_weight', 'max_cmc'}
        for name, archetype in self.archetypes.items():
            if not all(field in archetype for field in required_fields):
                raise ValueError(f"Missing required fields in archetype {name}")
            if not all(0 <= archetype[field] <= 1 for field in ['creature_weight', 'instant_weight']):
                raise ValueError(f"Invalid weight values in archetype {name}")
                
    def get_archetype_combinations(self, primary: str, secondary: Optional[str] = None) -> Dict[str, float]:
        """Get combined archetype weights"""
        if primary not in self.archetypes:
            raise ValueError(f"Unknown primary archetype: {primary}")
            
        weights = self.archetypes[primary].copy()
        
        if secondary:
            if secondary not in self.archetypes:
                raise ValueError(f"Unknown secondary archetype: {secondary}")
            # Blend weights based on metadata
            blend_factor = self.metadata.get('blend_factor', 0.5)
            for key in weights:
                if key in self.archetypes[secondary]:
                    weights[key] = (weights[key] * (1 - blend_factor) + 
                                 self.archetypes[secondary][key] * blend_factor)
                                 
        return weights
        
    def validate_deck_archetype(self, deck: Dict[str, Any], archetype: str) -> bool:
        """Validate if a deck matches an archetype"""
        if archetype not in self.archetypes:
            return False
            
        archetype_def = self.archetypes[archetype]
        deck_stats = self._calculate_deck_stats(deck)
        
        # Check creature ratio
        if not (archetype_def['creature_weight'] * 0.8 <= 
                deck_stats['creature_ratio'] <= 
                archetype_def['creature_weight'] * 1.2):
            return False
            
        # Check instant ratio
        if not (archetype_def['instant_weight'] * 0.8 <= 
                deck_stats['instant_ratio'] <= 
                archetype_def['instant_weight'] * 1.2):
            return False
            
        # Check CMC
        if deck_stats['avg_cmc'] > archetype_def['max_cmc']:
            return False
            
        return True 