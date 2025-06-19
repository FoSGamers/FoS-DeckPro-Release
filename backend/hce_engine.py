import numpy as np
import yaml
from typing import Dict, Tuple, List
import hashlib

class HCEEngine:
    def __init__(self, config_path: str = "config.yaml"):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                hce_config = config.get('hce', {})
                self.config = hce_config
                self.phase_history = []
                self.entropy_history = []
                self.phase_lock_threshold = hce_config.get('phase_lock_threshold', 0.98)
                self.max_entropy_drift = hce_config.get('max_entropy_drift', 0.1)
                self.is_tracking = False
                self.phase_threshold = hce_config.get('phase_threshold', 0.1)
        except Exception as e:
            print(f"Error initializing HCE engine: {e}")
            # Set defaults
            self.config = {}
            self.phase_history = []
            self.entropy_history = []
            self.phase_lock_threshold = 0.98
            self.max_entropy_drift = 0.1
            self.is_tracking = False
            self.phase_threshold = 0.1

    def compute_phase_vector(self, state: np.ndarray) -> str:
        """
        Compute phase vector using SHA-256 hash of state
        """
        state_bytes = state.tobytes()
        return hashlib.sha256(state_bytes).hexdigest()

    def compute_entropy(self, state: np.ndarray) -> float:
        """
        Compute Shannon entropy of state vector
        """
        try:
            # Normalize state to probability distribution
            state_abs = np.abs(state)
            state_sum = np.sum(state_abs)
            if state_sum == 0:
                return 0.0  # Return 0 entropy for zero state
            state_norm = state_abs / state_sum
            # Compute entropy: -sum(p * log(p))
            entropy = -np.sum(state_norm * np.log2(state_norm + 1e-10))
            return float(entropy)
        except Exception as e:
            print(f"Error computing entropy: {e}")
            return 0.0

    def check_phase_lock(self, current_phase: str, previous_phase: str) -> bool:
        """
        Check if phase is locked (similar to previous phase)
        """
        if not previous_phase:
            return True
        
        # Compute Hamming distance between phase vectors
        distance = sum(c1 != c2 for c1, c2 in zip(current_phase, previous_phase))
        similarity = 1 - (distance / len(current_phase))
        
        return similarity >= self.phase_lock_threshold

    def check_entropy_drift(self, current_entropy: float, previous_entropy: float) -> bool:
        """
        Check if entropy drift is within acceptable bounds
        """
        if previous_entropy is None:
            return True
        
        drift = abs(current_entropy - previous_entropy)
        return drift <= self.max_entropy_drift

    def update_phase_state(self, state: np.ndarray) -> Dict:
        """
        Update phase and entropy state, check for violations
        """
        current_phase = self.compute_phase_vector(state)
        current_entropy = self.compute_entropy(state)
        
        # Get previous state
        previous_phase = self.phase_history[-1] if self.phase_history else None
        previous_entropy = self.entropy_history[-1] if self.entropy_history else None
        
        # Check phase lock and entropy drift
        phase_locked = self.check_phase_lock(current_phase, previous_phase)
        entropy_stable = self.check_entropy_drift(current_entropy, previous_entropy)
        
        # Update history
        self.phase_history.append(current_phase)
        self.entropy_history.append(current_entropy)
        
        # Keep history within bounds
        if len(self.phase_history) > 1000:
            self.phase_history.pop(0)
            self.entropy_history.pop(0)
        
        return {
            'phase': current_phase,
            'entropy': current_entropy,
            'phase_locked': phase_locked,
            'entropy_stable': entropy_stable,
            'phase_history': self.phase_history[-10:],
            'entropy_history': self.entropy_history[-10:]
        }

    def analyze_phase_drift(self, window_size: int = 100) -> Dict:
        """
        Analyze phase and entropy drift over time window
        """
        if len(self.phase_history) < window_size:
            return {'error': 'Insufficient history', 'entropy_drift': 0.0, 'phase_stability': 0.0, 'is_stable': False}
        
        recent_phases = self.phase_history[-window_size:]
        recent_entropy = self.entropy_history[-window_size:]
        
        # Compute phase stability
        phase_stability = sum(1 for i in range(1, len(recent_phases))
                            if self.check_phase_lock(recent_phases[i], recent_phases[i-1])) / (len(recent_phases) - 1)
        
        # Compute entropy drift
        entropy_drift = np.std(recent_entropy)
        
        return {
            'phase_stability': phase_stability,
            'entropy_drift': entropy_drift,
            'is_stable': phase_stability >= self.phase_lock_threshold and entropy_drift <= self.max_entropy_drift
        }

    def get_phase_diagram(self) -> Dict:
        """
        Generate phase diagram data for visualization
        """
        return {
            'phases': self.phase_history[-100:],
            'entropy': self.entropy_history[-100:],
            'stability': self.analyze_phase_drift(100)
        }

    def start_phase_tracking(self) -> bool:
        """
        Start phase tracking
        """
        try:
            self.phase_history = []
            self.entropy_history = []
            self.is_tracking = True
            return True
        except Exception:
            return False

    def stop_phase_tracking(self) -> bool:
        """
        Stop phase tracking
        """
        try:
            self.is_tracking = False
            return True
        except Exception:
            return False

    def check_phase_alignment(self, project_path: str = None) -> bool:
        """
        Check phase alignment
        """
        try:
            if not self.phase_history:
                return True  # Assume aligned if no data
            # Check if phases are within acceptable range
            recent_phases = self.phase_history[-10:]
            phase_std = np.std(recent_phases)
            return phase_std < self.phase_threshold
        except Exception:
            return False 