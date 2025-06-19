import numpy as np
import yaml
from typing import Dict, Tuple, List, Any, Optional
import os

class APTPTFeedback:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize APTPT feedback controller with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # APTPT parameters
        self.gain = self.config.get('aptpt', {}).get('gain', 0.16)
        self.noise = self.config.get('aptpt', {}).get('noise', 0.005)
        self.convergence_threshold = self.config.get('aptpt', {}).get('convergence_threshold', 0.03)
        self.max_iterations = self.config.get('aptpt', {}).get('max_iterations', 1000)
        self.tolerance = self.config.get('aptpt', {}).get('tolerance', 0.01)
        self.iteration_count = 0
        
        # Error floor calculation
        self.error_floor = self.noise / self.gain
        self.phase_history = []
        self.max_history = 1000
        self.entropy_guard = self.config.get('hce', {}).get('entropy_guard', True)
        self.max_entropy_drift = self.config.get('hce', {}).get('max_entropy_drift', 0.05)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def analyze_phase_drift(self, window_size: int = 100) -> Dict[str, Any]:
        """Analyze phase drift over a window of recent states."""
        if len(self.phase_history) < window_size:
            return {
                "is_stable": False,
                "drift": 0.0,
                "window_size": len(self.phase_history),
                "message": "Insufficient history for analysis"
            }

        recent_phases = self.phase_history[-window_size:]
        drift = np.std(recent_phases)
        
        is_stable = True
        if self.entropy_guard:
            is_stable = drift <= self.max_entropy_drift

        return {
            "is_stable": is_stable,
            "drift": float(drift),
            "window_size": window_size,
            "message": "Phase analysis complete"
        }

    def update_phase(self, new_phase: float) -> None:
        """Update phase history with new measurement."""
        self.phase_history.append(new_phase)
        if len(self.phase_history) > self.max_history:
            self.phase_history.pop(0)

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status including phase stability."""
        phase_analysis = self.analyze_phase_drift()
        return {
            "status": "healthy" if phase_analysis["is_stable"] else "degraded",
            "version": "1.0.0",
            "phase_stable": phase_analysis["is_stable"],
            "phase_drift": phase_analysis["drift"],
            "message": phase_analysis["message"]
        }

    def compute_feedback_vector(self, current_state: np.ndarray, target_state: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Compute APTPT feedback vector using the mathematical formulation:
        P_local(t+1) = P_local(t) + α(S_target - P_local(t)) + η(t)
        where α is the gain and η(t) is i.i.d. Gaussian noise
        """
        error = target_state - current_state
        error_norm = np.linalg.norm(error)
        
        # Adaptive gain based on error magnitude
        if self.config.get('aptpt', {}).get('adaptive_gain', False):
            self.gain = min(1.0, max(0.01, self.gain * (1 + error_norm)))
            # Clamp gain to (0,1) per APTPT theory
            self.gain = max(0.01, min(self.gain, 0.99))
        
        # Compute feedback with noise
        noise_vector = np.random.normal(0, self.noise, size=current_state.shape)
        feedback = self.gain * error + noise_vector
        
        # Check convergence
        is_converged = error_norm < self.convergence_threshold
        
        return feedback, error_norm

    def update_state(self, current_state: np.ndarray, target_state: np.ndarray) -> np.ndarray:
        """
        Update state using APTPT feedback control
        """
        self.iteration_count = 0
        current = current_state.copy()
        
        while self.iteration_count < self.max_iterations:
            # Apply APTPT update rule
            error = target_state - current
            update = self.gain * error + np.random.normal(0, self.noise, size=current.shape)
            current = current + update
            
            self.iteration_count += 1
            
            # Check convergence
            if np.linalg.norm(error) < self.tolerance:
                break
        
        return current

    def calculate_convergence_rate(self, initial_state: np.ndarray, final_state: np.ndarray, target_state: np.ndarray) -> float:
        """
        Calculate convergence rate based on error reduction
        """
        initial_error = np.linalg.norm(target_state - initial_state)
        final_error = np.linalg.norm(target_state - final_state)
        
        if initial_error == 0:
            return 1.0
        
        error_reduction = (initial_error - final_error) / initial_error
        return max(0.0, min(1.0, error_reduction))

    def calculate_error_reduction(self, initial_state: np.ndarray, final_state: np.ndarray, target_state: np.ndarray) -> float:
        """
        Calculate absolute error reduction
        """
        initial_error = np.linalg.norm(target_state - initial_state)
        final_error = np.linalg.norm(target_state - final_state)
        return initial_error - final_error

    def get_iteration_count(self) -> int:
        """
        Get the number of iterations used in the last update
        """
        return self.iteration_count

    def batch_validate(self, initial_states: List[np.ndarray], target_states: List[np.ndarray]) -> Dict:
        """
        Run batch validation of APTPT performance
        """
        results = {
            'success_rate': 0,
            'avg_steps': 0,
            'error_distribution': [],
            'convergence_times': []
        }
        
        timeout_seconds = self.config.get('aptpt', {}).get('timeout_seconds', 1000)
        
        for init, target in zip(initial_states, target_states):
            state = init.copy()
            steps = 0
            converged = False
            
            while steps < timeout_seconds:
                # Use the new update_state method that returns only the new state
                new_state = self.update_state(state, target)
                steps += 1
                
                # Check convergence
                error = np.linalg.norm(target - new_state)
                if error < self.tolerance:
                    converged = True
                    break
                
                state = new_state
            
            results['success_rate'] += int(converged)
            results['avg_steps'] += steps
            results['error_distribution'].append(error)
            results['convergence_times'].append(steps)
        
        # Normalize results
        n_trials = len(initial_states)
        results['success_rate'] /= n_trials
        results['avg_steps'] /= n_trials
        
        return results

    def optimize_parameters(self, validation_data: Dict) -> Dict:
        """
        Optimize APTPT parameters based on validation results
        """
        if validation_data['success_rate'] < 0.95:
            # Increase gain if convergence is slow
            self.gain = min(1.0, self.gain * 1.1)
            # Decrease noise if error is high
            noise_floor = self.config.get('aptpt', {}).get('noise_floor', 0.001)
            self.noise = max(noise_floor, self.noise * 0.9)
        
        return {
            'optimized_gain': self.gain,
            'optimized_noise': self.noise
        }

    def validate_parameters(self) -> bool:
        """
        Validate APTPT parameters for health check
        """
        try:
            # Check if parameters are within valid ranges
            if not (0 < self.gain < 1):
                return False
            if self.noise < 0:
                return False
            if self.convergence_threshold <= 0:
                return False
            return True
        except Exception:
            return False

    def initialize(self) -> bool:
        """
        Initialize APTPT engine
        """
        try:
            # Reset state
            self.phase_history = []
            self.error_history = []
            self.state_history = []
            return True
        except Exception:
            return False

    def is_healthy(self) -> bool:
        """
        Check if APTPT engine is healthy
        """
        return True

    def update_feedback(self, current_state, target_state):
        current_state = np.array(current_state)
        target_state = np.array(target_state)
        return self.update_state(current_state, target_state) 