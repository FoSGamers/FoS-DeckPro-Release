import threading
import time
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import yaml
from aptpt_feedback import APTPTFeedback
from hce_engine import HCEEngine
from rei_engine import REIEngine
from visualizer import PhaseSynthVisualizer

class AutonomousDaemon:
    def __init__(self, config_path: str = "config.yaml", test_mode: bool = False):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.aptpt = APTPTFeedback(config_path)
        self.hce = HCEEngine(config_path)
        self.rei = REIEngine(config_path)
        self.visualizer = PhaseSynthVisualizer(config_path)
        
        self.state_history = []
        self.healing_history = []
        self.is_running = False
        self.thread = None
        self.test_mode = test_mode
        
        # Load initial state if available
        try:
            data = self.visualizer.load_visualization_data()
            self.state_history = data['states'].tolist()
        except:
            pass
    
    def start(self):
        """
        Start the autonomous daemon
        """
        if self.is_running:
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._healing_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """
        Stop the autonomous daemon
        """
        self.is_running = False
        if self.thread:
            self.thread.join()
    
    def _healing_loop(self):
        """
        Main healing loop implementing APTPT/HCE/REI theory
        """
        while self.is_running:
            try:
                # Get current system state
                current_state = self._get_current_state()
                self.state_history.append(current_state)
                
                # APTPT: Check convergence and optimize parameters
                if len(self.state_history) >= 2:
                    aptpt_results = self.aptpt.batch_validate(
                        self.state_history[-2:-1],
                        self.state_history[-1:]
                    )
                    
                    if aptpt_results['success_rate'] < 0.95:
                        self._heal_aptpt(aptpt_results)
                
                # HCE: Check phase stability and entropy drift
                hce_metrics = self.hce.update_phase_state(current_state)
                if not hce_metrics['phase_locked'] or not hce_metrics['entropy_stable']:
                    self._heal_hce(hce_metrics)
                
                # REI: Check transformation invariance
                if len(self.state_history) >= 2:
                    rei_valid = self.rei.check_invariance(
                        current_state,
                        self.state_history[-2]
                    )
                    if not rei_valid:
                        self._heal_rei()
                
                # Save visualization data periodically
                if len(self.state_history) % 100 == 0:
                    self.visualizer.save_visualization_data(self.state_history)
                
                # Sleep for next iteration
                if self.test_mode:
                    time.sleep(0.1)
                else:
                    time.sleep(self.config['system']['snapshot_interval'])
                
            except Exception as e:
                print(f"Error in healing loop: {e}")
                time.sleep(5)  # Wait before retrying
    
    def _get_current_state(self) -> np.ndarray:
        """
        Get current system state
        Override this method in subclasses
        """
        # Default: Return random state for testing
        return np.random.randn(3)
    
    def _heal_aptpt(self, aptpt_results: Dict):
        """
        Heal APTPT convergence issues
        """
        # Optimize parameters
        optimized = self.aptpt.optimize_parameters(aptpt_results)
        
        # Record healing action
        self.healing_history.append({
            'timestamp': time.time(),
            'type': 'aptpt',
            'action': 'parameter_optimization',
            'details': optimized
        })
    
    def _heal_hce(self, hce_metrics: Dict):
        """
        Heal HCE phase/entropy issues
        """
        # Analyze phase drift
        drift_analysis = self.hce.analyze_phase_drift(100)
        
        if drift_analysis['entropy_drift'] > self.config['phase_rules']['max_entropy_drift']:
            # Reset phase vector if entropy drift is too high
            self.hce.phase_history = []
            self.hce.entropy_history = []
        
        # Record healing action
        self.healing_history.append({
            'timestamp': time.time(),
            'type': 'hce',
            'action': 'phase_reset',
            'details': drift_analysis
        })
    
    def _heal_rei(self):
        """
        Heal REI invariance issues
        """
        # Recompute xi constant
        if len(self.state_history) >= 3:
            new_xi = self.rei.compute_xi_constant(self.state_history[-3:])
            
            # Record healing action
            self.healing_history.append({
                'timestamp': time.time(),
                'type': 'rei',
                'action': 'xi_recomputation',
                'details': {'new_xi': new_xi}
            })
    
    def get_healing_status(self) -> Dict:
        """
        Get current healing status
        """
        return {
            'is_running': self.is_running,
            'state_history_length': len(self.state_history),
            'healing_actions': self.healing_history[-10:],
            'current_metrics': {
                'aptpt': {
                    'gain': self.aptpt.gain,
                    'noise': self.aptpt.noise
                },
                'hce': self.hce.analyze_phase_drift(100),
                'rei': {
                    'xi': self.rei.xi,
                    'invariance_threshold': self.rei.invariance_threshold
                }
            }
        }
    
    def plot_healing_history(self) -> None:
        """
        Plot healing history
        """
        if not self.healing_history:
            return
        
        timestamps = [h['timestamp'] for h in self.healing_history]
        types = [h['type'] for h in self.healing_history]
        
        plt.figure(figsize=(12, 6))
        plt.scatter(timestamps, types)
        plt.title('Healing History')
        plt.xlabel('Timestamp')
        plt.ylabel('Healing Type')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show() 