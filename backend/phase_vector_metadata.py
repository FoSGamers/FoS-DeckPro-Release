import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from scipy import stats

class PhaseVectorMetadata:
    def __init__(self):
        self.phase_history = []
        self.entropy_history = []
        self.rei_history = []
    
    def _compute_phase_vector(self, data: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def _compute_entropy(self, data: Dict[str, Any]) -> float:
        """Compute entropy using HCE theory"""
        if not data:
            return 0.0
        
        # Convert data to string for entropy calculation
        data_str = json.dumps(data, sort_keys=True)
        char_freq = {}
        for char in data_str:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(data_str)
        entropy = 0.0
        for count in char_freq.values():
            p = count / total
            entropy -= p * math.log2(p) if p > 0 else 0
        return entropy
    
    def _compute_rei_score(self, phase_vector: str) -> float:
        """Compute REI score using REI theory"""
        if not phase_vector:
            return 0.0
        # REI score based on phase vector properties
        return sum(ord(c) for c in phase_vector[:8]) / (8 * 255)
    
    def add_metadata(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add metadata with APTPT/HCE/REI analysis"""
        context = context or {}
        
        # Compute metrics
        phase_vector = self._compute_phase_vector({**data, **context})
        entropy = self._compute_entropy({**data, **context})
        rei_score = self._compute_rei_score(phase_vector)
        
        # Create metadata
        metadata = {
            "phase_vector": phase_vector,
            "entropy": entropy,
            "rei_score": rei_score,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }
        
        # Add to history
        self.phase_history.append(phase_vector)
        self.entropy_history.append(entropy)
        self.rei_history.append(rei_score)
        
        return metadata
    
    def get_metadata_history(self) -> List[Dict[str, Any]]:
        """Get metadata history with APTPT/HCE/REI metrics"""
        return [
            {
                "phase_vector": p,
                "entropy": e,
                "rei_score": r,
                "timestamp": datetime.now().isoformat()
            }
            for p, e, r in zip(self.phase_history, self.entropy_history, self.rei_history)
        ]
    
    def analyze_phase_convergence(self) -> Dict[str, Any]:
        """Analyze phase convergence using APTPT/HCE/REI theory"""
        if not self.phase_history:
            return {
                "convergence": False,
                "reason": "No phase history available"
            }
        
        # Analyze phase vector convergence
        unique_phases = len(set(self.phase_history))
        phase_diversity = unique_phases / len(self.phase_history)
        
        # Analyze entropy stability
        entropy_mean = np.mean(self.entropy_history)
        entropy_std = np.std(self.entropy_history)
        entropy_stability = 1.0 - min(entropy_std / entropy_mean, 1.0) if entropy_mean > 0 else 0.0
        
        # Analyze REI score stability
        rei_mean = np.mean(self.rei_history)
        rei_std = np.std(self.rei_history)
        rei_stability = 1.0 - min(rei_std / rei_mean, 1.0) if rei_mean > 0 else 0.0
        
        # Analyze temporal patterns
        entropy_trend = stats.linregress(range(len(self.entropy_history)), self.entropy_history)[0]
        rei_trend = stats.linregress(range(len(self.rei_history)), self.rei_history)[0]
        
        return {
            "convergence": phase_diversity < 0.5,
            "phase_diversity": phase_diversity,
            "entropy_stability": entropy_stability,
            "rei_stability": rei_stability,
            "entropy_trend": entropy_trend,
            "rei_trend": rei_trend,
            "total_phases": len(self.phase_history)
        }
    
    def cleanup_old_history(self, days: int = 30):
        """Clean up old phase history"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Keep only recent history
        self.phase_history = self.phase_history[-days:]
        self.entropy_history = self.entropy_history[-days:]
        self.rei_history = self.rei_history[-days:]
    
    def get_phase_statistics(self) -> Dict[str, Any]:
        """Get phase statistics using APTPT/HCE/REI theory"""
        if not self.phase_history:
            return {
                "error": "No phase history available"
            }
        
        return {
            "phase_vector": {
                "unique_count": len(set(self.phase_history)),
                "total_count": len(self.phase_history),
                "diversity": len(set(self.phase_history)) / len(self.phase_history)
            },
            "entropy": {
                "mean": np.mean(self.entropy_history),
                "std": np.std(self.entropy_history),
                "min": np.min(self.entropy_history),
                "max": np.max(self.entropy_history)
            },
            "rei_score": {
                "mean": np.mean(self.rei_history),
                "std": np.std(self.rei_history),
                "min": np.min(self.rei_history),
                "max": np.max(self.rei_history)
            }
        }

# Global instance
phase_metadata = PhaseVectorMetadata() 