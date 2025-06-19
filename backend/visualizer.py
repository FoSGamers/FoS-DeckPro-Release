import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
import yaml
from aptpt_feedback import APTPTFeedback
from hce_engine import HCEEngine
from rei_engine import REIEngine

class PhaseSynthVisualizer:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.aptpt = APTPTFeedback(config_path)
        self.hce = HCEEngine(config_path)
        self.rei = REIEngine(config_path)
        
    def plot_phase_diagram(self, states: List[np.ndarray], save_path: str = None) -> plt.Figure:
        """
        Plot APTPT phase diagram showing convergence regions
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot state trajectories
        states_array = np.array(states)
        for i in range(states_array.shape[1]):
            ax1.plot(states_array[:, i], label=f'Dimension {i+1}')
        ax1.set_title('State Trajectories')
        ax1.set_xlabel('Time Step')
        ax1.set_ylabel('State Value')
        ax1.legend()
        
        # Plot phase/entropy evolution
        phases = []
        entropies = []
        for state in states:
            hce_metrics = self.hce.update_phase_state(state)
            phases.append(hce_metrics['phase'][:8])  # First 8 chars for readability
            entropies.append(hce_metrics['entropy'])
        
        ax2.plot(entropies, label='Entropy')
        ax2.set_title('Phase/Entropy Evolution')
        ax2.set_xlabel('Time Step')
        ax2.set_ylabel('Entropy')
        ax2.legend()
        
        if save_path:
            plt.savefig(save_path)
        
        return fig
    
    def plot_convergence_map(self, gain_range: Tuple[float, float], 
                           noise_range: Tuple[float, float],
                           n_points: int = 20) -> plt.Figure:
        """
        Plot APTPT convergence map showing stable regions
        """
        gains = np.linspace(gain_range[0], gain_range[1], n_points)
        noises = np.linspace(noise_range[0], noise_range[1], n_points)
        
        convergence = np.zeros((n_points, n_points))
        for i, gain in enumerate(gains):
            for j, noise in enumerate(noises):
                self.aptpt.gain = gain
                self.aptpt.noise = noise
                
                # Test convergence with random states
                states = [np.random.randn(3) for _ in range(10)]
                results = self.aptpt.batch_validate(states[:-1], states[1:])
                convergence[i, j] = results['success_rate']
        
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(convergence, origin='lower', 
                      extent=[noise_range[0], noise_range[1], gain_range[0], gain_range[1]])
        plt.colorbar(im, ax=ax, label='Convergence Rate')
        ax.set_xlabel('Noise Level')
        ax.set_ylabel('Gain')
        ax.set_title('APTPT Convergence Map')
        
        return fig
    
    def plot_rei_equivalence(self, states: List[np.ndarray]) -> plt.Figure:
        """
        Plot REI equivalence relationships between states
        """
        n_states = len(states)
        equivalence_matrix = np.zeros((n_states, n_states))
        
        for i in range(n_states):
            for j in range(n_states):
                equivalence_matrix[i, j] = self.rei.compute_equivalence(states[i], states[j])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(equivalence_matrix, cmap='viridis')
        plt.colorbar(im, ax=ax, label='Equivalence Score')
        ax.set_xlabel('State Index')
        ax.set_ylabel('State Index')
        ax.set_title('REI Equivalence Matrix')
        
        return fig
    
    def generate_dashboard(self) -> Dict:
        """
        Generate comprehensive dashboard data
        """
        return {
            'aptpt_metrics': {
                'current_gain': self.aptpt.gain,
                'current_noise': self.aptpt.noise,
                'error_floor': self.aptpt.error_floor
            },
            'hce_metrics': {
                'phase_stability': self.hce.analyze_phase_drift(100)['phase_stability'],
                'entropy_drift': self.hce.analyze_phase_drift(100)['entropy_drift'],
                'is_stable': self.hce.analyze_phase_drift(100)['is_stable']
            },
            'rei_metrics': {
                'current_xi': self.rei.xi,
                'invariance_threshold': self.rei.invariance_threshold,
                'equivalence_history': self.rei.equivalence_history[-10:]
            }
        }
    
    def save_visualization_data(self, states: List[np.ndarray], 
                              filepath: str = 'visualization_data.npz'):
        """
        Save visualization data for later analysis
        """
        states_array = np.array(states)
        phases = []
        entropies = []
        equivalences = []
        
        for state in states:
            hce_metrics = self.hce.update_phase_state(state)
            phases.append(hce_metrics['phase'])
            entropies.append(hce_metrics['entropy'])
        
        for i in range(len(states)-1):
            equiv = self.rei.compute_equivalence(states[i], states[i+1])
            equivalences.append(equiv)
        
        np.savez(filepath,
                states=states_array,
                phases=phases,
                entropies=entropies,
                equivalences=equivalences)
    
    def load_visualization_data(self, filepath: str = 'visualization_data.npz') -> Dict:
        """
        Load saved visualization data
        """
        data = np.load(filepath)
        return {
            'states': data['states'],
            'phases': data['phases'],
            'entropies': data['entropies'],
            'equivalences': data['equivalences']
        } 