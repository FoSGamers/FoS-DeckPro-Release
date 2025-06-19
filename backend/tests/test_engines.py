import pytest
import numpy as np
from aptpt_feedback import APTPTFeedback
from hce_engine import HCEEngine
from rei_engine import REIEngine

@pytest.fixture
def aptpt():
    return APTPTFeedback()

@pytest.fixture
def hce():
    return HCEEngine()

@pytest.fixture
def rei():
    return REIEngine()

def test_aptpt_feedback(aptpt):
    # Test basic feedback computation
    current = np.array([1.0, 2.0, 3.0])
    target = np.array([2.0, 3.0, 4.0])
    
    feedback, error = aptpt.compute_feedback_vector(current, target)
    assert isinstance(feedback, np.ndarray)
    assert feedback.shape == current.shape
    assert error >= 0
    
    # Test state update
    new_state, metrics = aptpt.update_state(current, target)
    assert isinstance(new_state, np.ndarray)
    assert new_state.shape == current.shape
    assert "error" in metrics
    assert "gain" in metrics
    assert "noise_level" in metrics

def test_hce_phase_tracking(hce):
    # Test phase vector computation
    state = np.array([1.0, 2.0, 3.0])
    phase = hce.compute_phase_vector(state)
    assert isinstance(phase, str)
    assert len(phase) == 64  # SHA-256 hash length
    
    # Test entropy computation
    entropy = hce.compute_entropy(state)
    assert isinstance(entropy, float)
    assert entropy >= 0
    
    # Test phase state update
    metrics = hce.update_phase_state(state)
    assert "phase" in metrics
    assert "entropy" in metrics
    assert "phase_locked" in metrics
    assert "entropy_stable" in metrics

def test_rei_equivalence(rei):
    # Test basic equivalence computation
    state1 = np.array([1.0, 2.0, 3.0])
    state2 = np.array([1.1, 2.1, 3.1])
    
    equivalence = rei.compute_equivalence(state1, state2)
    assert isinstance(equivalence, float)
    assert 0 <= equivalence <= 1
    
    # Test invariance check
    is_invariant = rei.check_invariance(state1, state2)
    assert isinstance(is_invariant, bool)
    
    # Test transformation analysis
    states = [state1, state2, state1]
    analysis = rei.analyze_transformation(states)
    assert "transformations" in analysis
    assert "average_equivalence" in analysis
    assert "is_sequence_invariant" in analysis

def test_integrated_operation(aptpt, hce, rei):
    # Test integrated operation of all three engines
    current = np.array([1.0, 2.0, 3.0])
    target = np.array([2.0, 3.0, 4.0])
    
    # APTPT update
    new_state, aptpt_metrics = aptpt.update_state(current, target)
    
    # HCE phase tracking
    hce_metrics = hce.update_phase_state(new_state)
    
    # REI invariance check
    rei_valid = rei.check_invariance(new_state, current)
    
    # Verify all components work together
    assert isinstance(new_state, np.ndarray)
    assert isinstance(hce_metrics, dict)
    assert isinstance(rei_valid, bool)
    
    # Verify metrics are consistent
    assert aptpt_metrics["error"] >= 0
    assert hce_metrics["entropy"] >= 0
    assert 0 <= rei.compute_equivalence(new_state, current) <= 1

def test_parameter_optimization(aptpt):
    # Test parameter optimization
    states = [
        np.array([1.0, 2.0, 3.0]),
        np.array([1.5, 2.5, 3.5]),
        np.array([2.0, 3.0, 4.0])
    ]
    
    results = aptpt.batch_validate(states[:-1], states[1:])
    optimized = aptpt.optimize_parameters(results)
    
    assert "optimized_gain" in optimized
    assert "optimized_noise" in optimized
    assert 0 < optimized["optimized_gain"] <= 1
    assert optimized["optimized_noise"] >= 0 