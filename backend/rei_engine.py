import numpy as np
import yaml
from typing import Dict, Tuple, List, Any
import hashlib

class REIEngine:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)['rei']
        self.xi = self.config['universal_xi']
        self.invariance_threshold = 0.0
        self.recursive_depth = self.config['recursive_depth']
        self.equivalence_history = []

    def compute_equivalence(self, state1: Any, state2: Any, depth: int = 0) -> float:
        """
        Compute recursive equivalence between two states
        """
        if depth >= self.recursive_depth:
            return 1.0
        
        if isinstance(state1, np.ndarray) and isinstance(state2, np.ndarray):
            # For numpy arrays, compute normalized difference
            if state1.shape != state2.shape:
                return 0.0
            diff = np.linalg.norm(state1 - state2)
            norm = max(np.linalg.norm(state1), np.linalg.norm(state2))
            return 1.0 - (diff / (norm + 1e-10))
        
        elif isinstance(state1, dict) and isinstance(state2, dict):
            # For dictionaries, recursively compare values
            if set(state1.keys()) != set(state2.keys()):
                return 0.0
            similarities = []
            for key in state1:
                sim = self.compute_equivalence(state1[key], state2[key], depth + 1)
                similarities.append(sim)
            return np.mean(similarities)
        
        elif isinstance(state1, list) and isinstance(state2, list):
            # For lists, compare elements recursively
            if len(state1) != len(state2):
                return 0.0
            similarities = []
            for s1, s2 in zip(state1, state2):
                sim = self.compute_equivalence(s1, s2, depth + 1)
                similarities.append(sim)
            return np.mean(similarities)
        
        else:
            # For other types, use direct equality
            if isinstance(state1, np.ndarray) and isinstance(state2, np.ndarray):
                return float(np.array_equal(state1, state2))
            elif isinstance(state1, list) and isinstance(state2, list):
                return float(state1 == state2)
            else:
                return float(state1 == state2)

    def check_invariance(self, current_state=None, previous_state=None) -> bool:
        if current_state is None or previous_state is None:
            return True  # For health check
        equivalence = self.compute_equivalence(current_state, previous_state)
        self.equivalence_history.append(equivalence)
        if len(self.equivalence_history) > 1000:
            self.equivalence_history.pop(0)
        return bool(equivalence >= self.invariance_threshold)

    def analyze_transformation(self, states: List[Any]) -> Dict:
        """
        Analyze a sequence of state transformations for REI compliance
        """
        if len(states) < 2:
            return {'error': 'Insufficient states for analysis'}
        
        transformations = []
        for i in range(1, len(states)):
            equivalence = self.compute_equivalence(states[i], states[i-1])
            transformations.append({
                'step': i,
                'equivalence': equivalence,
                'invariant': equivalence >= self.invariance_threshold
            })
        
        return {
            'transformations': transformations,
            'average_equivalence': np.mean([t['equivalence'] for t in transformations]),
            'is_sequence_invariant': all(t['invariant'] for t in transformations)
        }

    def compute_xi_constant(self, states: List[Any]) -> float:
        """
        Compute the REI xi constant for a sequence of states
        """
        if len(states) < 2:
            return self.xi
        
        # Compute average equivalence
        equivalences = []
        for i in range(1, len(states)):
            equiv = self.compute_equivalence(states[i], states[i-1])
            equivalences.append(equiv)
        
        # Update xi based on observed equivalences
        observed_xi = np.mean(equivalences)
        self.xi = 0.9 * self.xi + 0.1 * observed_xi
        
        return self.xi

    def get_equivalence_diagram(self) -> Dict:
        """
        Generate equivalence diagram data for visualization
        """
        return {
            'equivalence_history': self.equivalence_history[-100:],
            'current_xi': self.xi,
            'invariance_threshold': self.invariance_threshold
        }

    def validate_transformation_chain(self, states: List[Any]) -> Dict:
        """
        Validate a chain of transformations for REI compliance
        """
        analysis = self.analyze_transformation(states)
        current_xi = self.compute_xi_constant(states)
        
        return {
            'is_valid': analysis['is_sequence_invariant'],
            'average_equivalence': analysis['average_equivalence'],
            'xi_constant': current_xi,
            'transformations': analysis['transformations']
        }

    def initialize(self) -> bool:
        """
        Initialize REI engine
        """
        try:
            self.equivalence_history = []
            return True
        except Exception:
            return False 