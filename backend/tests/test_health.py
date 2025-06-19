import unittest
import requests
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aptpt_feedback import APTPTFeedback
from hce_engine import HCEEngine
from rei_engine import REIEngine
import pytest
import numpy as np

class TestHealth(unittest.TestCase):
    def setUp(self):
        self.aptpt = APTPTFeedback()
        self.hce = HCEEngine()
        self.rei = REIEngine()
        
    def test_api_server_health(self):
        """Test API server health with APTPT/HCE/REI validation"""
        r = requests.get("http://127.0.0.1:8000/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")
        
    def test_phase_synth_audit(self):
        """Test phase synthesis audit"""
        r = requests.get("http://127.0.0.1:8000/dashboard")
        data = r.json()
        
        # Check APTPT metrics
        self.assertIn("aptpt", data)
        self.assertIn("gain", data["aptpt"])
        self.assertIn("noise", data["aptpt"])
        
        # Check HCE metrics
        self.assertIn("phase", data)
        self.assertIn("entropy", data)
        
        # Check REI metrics
        self.assertIn("rei", data)
        self.assertIn("xi", data["rei"])
        
    def test_engine_health(self):
        """Test individual engine health"""
        # Test APTPT
        self.assertTrue(self.aptpt.validate_parameters())
        
        # Test HCE
        self.assertTrue(self.hce.check_phase_alignment())
        
        # Test REI
        self.assertTrue(self.rei.check_invariance())
        
    def test_phase_sync(self):
        """Test phase synchronization"""
        # Start phase tracking
        self.hce.start_phase_tracking()
        
        # Wait for some phase updates
        time.sleep(2)
        
        # Check phase alignment
        self.assertTrue(self.hce.check_phase_alignment())
        
        # Stop phase tracking
        self.hce.stop_phase_tracking()
        
    def test_feedback_loop(self):
        """Test APTPT feedback loop"""
        # Initialize feedback
        self.aptpt.initialize()
        
        # Simulate some feedback
        for _ in range(3):
            self.aptpt.update_feedback([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])
            
        # Check feedback parameters
        self.assertTrue(self.aptpt.validate_parameters())
        
    def test_rei_invariance(self):
        """Test REI invariance"""
        # Initialize REI
        self.rei.initialize()
        
        # Test invariance with sample states
        state1 = [1.0, 2.0, 3.0]
        state2 = [2.0, 3.0, 4.0]
        
        self.assertTrue(self.rei.check_invariance(state1, state2))
        
    def test_integrated_health(self):
        """Test integrated system health"""
        # Start all engines
        self.aptpt.initialize()
        self.hce.start_phase_tracking()
        self.rei.initialize()
        
        # Wait for system to stabilize
        time.sleep(2)
        
        # Check overall health
        r = requests.get("http://127.0.0.1:8000/health")
        self.assertEqual(r.status_code, 200)
        
        # Check dashboard
        r = requests.get("http://127.0.0.1:8000/dashboard")
        data = r.json()
        self.assertEqual(data["status"], "ok")
        
        # Stop engines
        self.hce.stop_phase_tracking()

@pytest.fixture
def feedback():
    return APTPTFeedback()

def test_initial_health_status(feedback):
    """Test initial health status before any phase updates."""
    status = feedback.get_health_status()
    assert isinstance(status, dict)
    assert "status" in status
    assert "version" in status
    assert "phase_stable" in status
    assert "phase_drift" in status
    assert "message" in status
    assert status["status"] == "degraded"  # Should be degraded initially due to no history

def test_phase_drift_analysis(feedback):
    """Test phase drift analysis with stable and unstable scenarios."""
    # Add stable phase history
    for i in range(100):
        feedback.update_phase(0.1 + np.random.normal(0, 0.01))
    
    analysis = feedback.analyze_phase_drift()
    assert analysis["is_stable"]
    assert analysis["drift"] < feedback.max_entropy_drift
    
    # Add unstable phase history
    for i in range(100):
        feedback.update_phase(0.1 + np.random.normal(0, 0.1))
    
    analysis = feedback.analyze_phase_drift()
    assert not analysis["is_stable"]
    assert analysis["drift"] > feedback.max_entropy_drift

def test_health_status_with_history(feedback):
    """Test health status after adding phase history."""
    # Add stable phase history
    for i in range(100):
        feedback.update_phase(0.1 + np.random.normal(0, 0.01))
    
    status = feedback.get_health_status()
    assert status["status"] == "healthy"
    assert status["phase_stable"]
    assert status["phase_drift"] < feedback.max_entropy_drift

def test_health_check():
    feedback = APTPTFeedback()
    assert feedback.is_healthy() == True

if __name__ == '__main__':
    unittest.main() 