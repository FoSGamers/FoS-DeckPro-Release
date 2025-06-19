"""
Test suite for APTPT functionality.
"""

import unittest
from .aptpt import aptpt_wrapper
from .demo_modules import get_temperature, get_status_vector, risky_division
from .aptpt_config import get_config, update_config

class TestAPTPT(unittest.TestCase):
    """Test cases for APTPT functionality."""
    
    def test_temperature_monitoring(self):
        """Test temperature monitoring with APTPT."""
        target = 72.0
        result = aptpt_wrapper(target, get_temperature)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, float)
    
    def test_vector_monitoring(self):
        """Test vector monitoring with APTPT."""
        target = [1.0, 0.0, -0.1]
        result = aptpt_wrapper(target, get_status_vector)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), len(target))
    
    def test_error_handling(self):
        """Test error handling with APTPT."""
        with self.assertRaises(ZeroDivisionError):
            aptpt_wrapper(0, risky_division, 10, 0)
    
    def test_config_management(self):
        """Test configuration management."""
        # Test default config
        config = get_config("test_function")
        self.assertIn("threshold", config)
        
        # Test config update
        new_config = {"threshold": 0.1, "description": "Test function"}
        update_config("test_function", new_config)
        updated_config = get_config("test_function")
        self.assertEqual(updated_config["threshold"], 0.1)
        self.assertEqual(updated_config["description"], "Test function")

if __name__ == "__main__":
    unittest.main() 