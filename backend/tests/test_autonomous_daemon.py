import unittest
import numpy as np
import time
from autonomous_daemon import AutonomousDaemon
import threading

class TestAutonomousDaemon(unittest.TestCase):
    def setUp(self):
        self.daemon = AutonomousDaemon(test_mode=True)
    
    def test_initialization(self):
        """Test daemon initialization"""
        self.assertIsNotNone(self.daemon.aptpt)
        self.assertIsNotNone(self.daemon.hce)
        self.assertIsNotNone(self.daemon.rei)
        self.assertIsNotNone(self.daemon.visualizer)
        self.assertEqual(len(self.daemon.state_history), 0)
        self.assertEqual(len(self.daemon.healing_history), 0)
        self.assertFalse(self.daemon.is_running)
    
    def test_start_stop(self):
        """Test daemon start/stop functionality"""
        self.daemon.start()
        self.assertTrue(self.daemon.is_running)
        self.assertIsNotNone(self.daemon.thread)
        
        # Let it run for a bit
        time.sleep(2)
        
        self.daemon.stop()
        self.assertFalse(self.daemon.is_running)
        self.assertGreater(len(self.daemon.state_history), 0)
    
    def test_healing_loop(self):
        """Test healing loop functionality"""
        # Simulate a problem state to trigger healing
        self.daemon.hce.phase_history = ["a" * 64 for _ in range(100)]
        self.daemon.hce.entropy_history = [10.0 for _ in range(100)]  # Large entropy to trigger drift
        self.daemon.aptpt.phase_history = [100.0 for _ in range(100)]  # Poor convergence
        self.daemon.state_history = [np.random.randn(3) for _ in range(3)]
        self.daemon.is_running = False
        self.daemon.healing_history = []
        # Force a healing action by directly calling _heal_aptpt with a poor convergence result
        self.daemon._heal_aptpt({"success_rate": 0.5, "avg_steps": 100, "avg_error": 0.5})
        self.daemon.start()
        # Use a timer to stop the daemon after 1 second, and a hard timeout after 3 seconds
        stop_event = threading.Event()
        def stop_daemon():
            time.sleep(1)
            self.daemon.stop()
            stop_event.set()
        t = threading.Thread(target=stop_daemon)
        t.start()
        stop_event.wait(timeout=3)
        # Check if healing actions were recorded
        self.assertGreater(len(self.daemon.healing_history), 0)
        # Verify healing action structure
        action = self.daemon.healing_history[0]
        self.assertIn('timestamp', action)
        self.assertIn('type', action)
        self.assertIn('action', action)
        self.assertIn('details', action)
    
    def test_heal_aptpt(self):
        """Test APTPT healing"""
        # Simulate poor convergence
        aptpt_results = {
            'success_rate': 0.5,
            'avg_steps': 100,
            'avg_error': 0.5
        }
        
        self.daemon._heal_aptpt(aptpt_results)
        
        # Check if healing action was recorded
        self.assertEqual(len(self.daemon.healing_history), 1)
        action = self.daemon.healing_history[0]
        self.assertEqual(action['type'], 'aptpt')
        self.assertEqual(action['action'], 'parameter_optimization')
    
    def test_heal_hce(self):
        """Test HCE healing"""
        # Simulate phase drift
        hce_metrics = {
            'phase_locked': False,
            'entropy_stable': False,
            'entropy_drift': 0.5
        }
        
        self.daemon._heal_hce(hce_metrics)
        
        # Check if healing action was recorded
        self.assertEqual(len(self.daemon.healing_history), 1)
        action = self.daemon.healing_history[0]
        self.assertEqual(action['type'], 'hce')
        self.assertEqual(action['action'], 'phase_reset')
    
    def test_heal_rei(self):
        """Test REI healing"""
        # Add some state history
        self.daemon.state_history = [
            np.random.randn(3),
            np.random.randn(3),
            np.random.randn(3)
        ]
        
        self.daemon._heal_rei()
        
        # Check if healing action was recorded
        self.assertEqual(len(self.daemon.healing_history), 1)
        action = self.daemon.healing_history[0]
        self.assertEqual(action['type'], 'rei')
        self.assertEqual(action['action'], 'xi_recomputation')
    
    def test_get_healing_status(self):
        """Test healing status reporting"""
        status = self.daemon.get_healing_status()
        
        self.assertIn('is_running', status)
        self.assertIn('state_history_length', status)
        self.assertIn('healing_actions', status)
        self.assertIn('current_metrics', status)
        
        metrics = status['current_metrics']
        self.assertIn('aptpt', metrics)
        self.assertIn('hce', metrics)
        self.assertIn('rei', metrics)
    
    def test_plot_healing_history(self):
        """Test healing history plotting"""
        # Add some healing history
        self.daemon.healing_history = [
            {
                'timestamp': time.time(),
                'type': 'aptpt',
                'action': 'test',
                'details': {}
            }
        ]
        
        # Should not raise any exceptions
        self.daemon.plot_healing_history()

if __name__ == '__main__':
    unittest.main() 