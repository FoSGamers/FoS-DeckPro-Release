"""
Runtime configuration and extension module for APTPT.
Provides per-function configuration for thresholds, auto-adaptation, and more.
"""

def get_config(func_name):
    """
    Get configuration for a specific function.
    
    Args:
        func_name: Name of the function to get configuration for
        
    Returns:
        dict: Configuration dictionary for the function
    """
    # Per-function: set thresholds, auto-adaptation, etc.
    # Extend this dict to control thresholds per module or allow user/AI to modify at runtime!
    configs = {
        "get_temperature": {
            "threshold": 2.0,
            "description": "Temperature sensor reading",
            "unit": "°F"
        },
        "get_status_vector": {
            "threshold": 0.1,
            "description": "Multi-sensor status vector",
            "dimensions": 3
        },
        # Add more as needed
    }
    
    # Default config with reasonable defaults
    default_config = {
        "threshold": 0.05,
        "description": "Generic function",
        "autoadapt": None  # No auto-adaptation by default
    }
    
    return configs.get(func_name, default_config)

def update_config(func_name, new_config):
    """
    Update configuration for a specific function.
    This allows runtime modification of thresholds and behavior.
    
    Args:
        func_name: Name of the function to update
        new_config: Dictionary of new configuration values
    """
    global configs
    if func_name not in configs:
        configs[func_name] = {}
    configs[func_name].update(new_config) 