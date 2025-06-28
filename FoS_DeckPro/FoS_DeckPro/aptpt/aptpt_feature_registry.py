import os
import importlib
import pkgutil
from typing import Dict, Any, List, Optional
from .aptpt import log_aptpt_event

class APTPTFeatureRegistry:
    """Registry for managing available features."""
    
    def __init__(self):
        self.features: Dict[str, Dict[str, Any]] = {}
        self._load_features()
    
    def _load_features(self) -> None:
        """Load all available features."""
        try:
            # Get features directory
            features_dir = os.path.join(
                os.path.dirname(__file__),
                'features'
            )
            
            # Create features directory if it doesn't exist
            if not os.path.exists(features_dir):
                os.makedirs(features_dir)
            
            # Load features
            for _, name, _ in pkgutil.iter_modules([features_dir]):
                try:
                    # Import feature module
                    module = importlib.import_module(f'.features.{name}', package=__package__)
                    
                    # Get feature info
                    if hasattr(module, 'get_feature_info'):
                        feature_info = module.get_feature_info()
                        self.features[feature_info['name']] = feature_info
                        
                        # Log feature loaded
                        log_aptpt_event(
                            'info',
                            'Feature loaded',
                            {'feature': feature_info['name']}
                        )
                    
                except Exception as e:
                    # Log error
                    log_aptpt_event(
                        'error',
                        'Failed to load feature',
                        {
                            'feature': name,
                            'error': str(e)
                        }
                    )
        
        except Exception as e:
            # Log error
            log_aptpt_event(
                'error',
                'Failed to load features',
                {'error': str(e)}
            )
    
    def get_feature(self, name: str) -> Optional[Dict[str, Any]]:
        """Get feature by name."""
        return self.features.get(name)
    
    def get_all_features(self) -> List[Dict[str, Any]]:
        """Get all available features."""
        return list(self.features.values())
    
    def get_feature_names(self) -> List[str]:
        """Get all feature names."""
        return list(self.features.keys())
    
    def reload_features(self) -> None:
        """Reload all features."""
        self.features.clear()
        self._load_features()

# Create global registry instance
feature_registry = APTPTFeatureRegistry() 