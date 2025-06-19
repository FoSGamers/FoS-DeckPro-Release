from typing import Dict, Any
import json
import os
from .aptpt_logger import log_aptpt_event

# Default configuration
DEFAULT_CONFIG = {
    'load_time': {
        'threshold': 1.0,  # seconds
        'target': 0.5,     # seconds
        'autoadapt': True
    },
    'save_time': {
        'threshold': 1.0,  # seconds
        'target': 0.5,     # seconds
        'autoadapt': True
    },
    'filter_time': {
        'threshold': 0.5,  # seconds
        'target': 0.2,     # seconds
        'autoadapt': True
    },
    'search_time': {
        'threshold': 0.5,  # seconds
        'target': 0.2,     # seconds
        'autoadapt': True
    },
    'merge_time': {
        'threshold': 1.0,  # seconds
        'target': 0.5,     # seconds
        'autoadapt': True
    },
    'update_time': {
        'threshold': 0.5,  # seconds
        'target': 0.2,     # seconds
        'autoadapt': True
    },
    'sort_time': {
        'threshold': 0.5,  # seconds
        'target': 0.2,     # seconds
        'autoadapt': True
    }
}

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'aptpt_config.json')

def get_config(function_name: str) -> Dict[str, Any]:
    """Get configuration for a specific function."""
    try:
        # Load configuration from file if it exists
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        else:
            config = DEFAULT_CONFIG.copy()
            # Save default configuration
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        
        # Return function-specific configuration or default
        return config.get(function_name, DEFAULT_CONFIG.get(function_name, {
            'threshold': 1.0,
            'target': 0.5,
            'autoadapt': True
        }))
    except Exception as e:
        log_aptpt_event(
            'error',
            'Failed to get APTPT configuration',
            {'error': str(e), 'function': function_name}
        )
        # Return default configuration on error
        return DEFAULT_CONFIG.get(function_name, {
            'threshold': 1.0,
            'target': 0.5,
            'autoadapt': True
        })

def update_config(function_name: str, updates: Dict[str, Any]) -> None:
    """Update configuration for a specific function."""
    try:
        # Load current configuration
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        else:
            config = DEFAULT_CONFIG.copy()
        
        # Update configuration
        if function_name not in config:
            config[function_name] = DEFAULT_CONFIG.get(function_name, {
                'threshold': 1.0,
                'target': 0.5,
                'autoadapt': True
            })
        
        config[function_name].update(updates)
        
        # Save updated configuration
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        log_aptpt_event(
            'success',
            'APTPT configuration updated',
            {
                'function': function_name,
                'updates': updates
            }
        )
    except Exception as e:
        log_aptpt_event(
            'error',
            'Failed to update APTPT configuration',
            {
                'error': str(e),
                'function': function_name,
                'updates': updates
            }
        )
        raise

def reset_config() -> None:
    """Reset configuration to defaults."""
    try:
        # Save default configuration
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        
        log_aptpt_event(
            'success',
            'APTPT configuration reset to defaults',
            {'config': DEFAULT_CONFIG}
        )
    except Exception as e:
        log_aptpt_event(
            'error',
            'Failed to reset APTPT configuration',
            {'error': str(e)}
        )
        raise 