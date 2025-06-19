import json
import hashlib
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import importlib
import os
import sys

class PluginInterface:
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        os.makedirs(plugins_dir, exist_ok=True)
        self.plugins = {}
        self.plugin_history = []
    
    def _compute_phase_vector(self, plugin_data: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(plugin_data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def _compute_entropy(self, plugin_data: Dict[str, Any]) -> float:
        """Compute entropy using HCE theory"""
        if not plugin_data:
            return 0.0
        
        # Convert data to string for entropy calculation
        data_str = json.dumps(plugin_data, sort_keys=True)
        char_freq = {}
        for char in data_str:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(data_str)
        entropy = 0.0
        for count in char_freq.values():
            p = count / total
            entropy -= p * math.log2(p) if p > 0 else 0
        return entropy
    
    def _compute_rei_score(self, phase_vector: str) -> float:
        """Compute REI score using REI theory"""
        if not phase_vector:
            return 0.0
        # REI score based on phase vector properties
        return sum(ord(c) for c in phase_vector[:8]) / (8 * 255)
    
    def load_plugin(self, plugin_name: str, plugin_path: str) -> Dict[str, Any]:
        """Load a plugin with APTPT/HCE/REI analysis"""
        try:
            # Add plugin directory to Python path
            sys.path.append(os.path.dirname(plugin_path))
            
            # Import plugin module
            module = importlib.import_module(plugin_name)
            
            # Get plugin metadata
            plugin_data = {
                "name": plugin_name,
                "path": plugin_path,
                "version": getattr(module, "__version__", "1.0.0"),
                "description": getattr(module, "__doc__", ""),
                "functions": [name for name in dir(module) if callable(getattr(module, name)) and not name.startswith("_")]
            }
            
            # Compute metrics
            phase_vector = self._compute_phase_vector(plugin_data)
            entropy = self._compute_entropy(plugin_data)
            rei_score = self._compute_rei_score(phase_vector)
            
            # Add metadata
            plugin_data["metadata"] = {
                "phase_vector": phase_vector,
                "entropy": entropy,
                "rei_score": rei_score,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store plugin
            self.plugins[plugin_name] = {
                "module": module,
                "data": plugin_data
            }
            
            # Add to history
            self.plugin_history.append({
                "action": "load",
                "plugin": plugin_data
            })
            
            return plugin_data
            
        except Exception as e:
            raise ValueError(f"Failed to load plugin {plugin_name}: {str(e)}")
    
    def unload_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Unload a plugin with APTPT/HCE/REI analysis"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        plugin_data = self.plugins[plugin_name]["data"]
        
        # Add to history
        self.plugin_history.append({
            "action": "unload",
            "plugin": plugin_data
        })
        
        # Remove plugin
        del self.plugins[plugin_name]
        
        return plugin_data
    
    def get_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """Get plugin data by name"""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin {plugin_name} not found")
        return self.plugins[plugin_name]["data"]
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all plugins with APTPT/HCE/REI metrics"""
        return [p["data"] for p in self.plugins.values()]
    
    def analyze_plugins_convergence(self) -> Dict[str, Any]:
        """Analyze plugins convergence using APTPT/HCE/REI theory"""
        if not self.plugins:
            return {
                "convergence": False,
                "reason": "No plugins available"
            }
        
        # Analyze phase vector convergence
        phase_vectors = [p["data"]["metadata"]["phase_vector"] for p in self.plugins.values()]
        unique_phases = len(set(phase_vectors))
        
        # Analyze entropy stability
        entropies = [p["data"]["metadata"]["entropy"] for p in self.plugins.values()]
        entropy_std = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        
        # Analyze REI score stability
        rei_scores = [p["data"]["metadata"]["rei_score"] for p in self.plugins.values()]
        rei_std = sum((r - sum(rei_scores)/len(rei_scores))**2 for r in rei_scores) / len(rei_scores)
        
        # Analyze plugin structure
        total_functions = sum(len(p["data"]["functions"]) for p in self.plugins.values())
        avg_functions = total_functions / len(self.plugins)
        
        return {
            "convergence": unique_phases < len(phase_vectors) * 0.5,
            "phase_diversity": unique_phases / len(phase_vectors),
            "entropy_stability": 1.0 - min(entropy_std, 1.0),
            "rei_stability": 1.0 - min(rei_std, 1.0),
            "avg_functions_per_plugin": avg_functions,
            "total_plugins": len(self.plugins)
        }
    
    def cleanup_old_history(self, days: int = 30):
        """Clean up old plugin history"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        self.plugin_history = [
            h for h in self.plugin_history
            if datetime.fromisoformat(h["plugin"]["metadata"]["timestamp"]).timestamp() > cutoff
        ]
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get plugin statistics using APTPT/HCE/REI theory"""
        if not self.plugins:
            return {
                "error": "No plugins available"
            }
        
        return {
            "phase_vector": {
                "unique_count": len(set(p["data"]["metadata"]["phase_vector"] for p in self.plugins.values())),
                "total_count": len(self.plugins),
                "diversity": len(set(p["data"]["metadata"]["phase_vector"] for p in self.plugins.values())) / len(self.plugins)
            },
            "entropy": {
                "mean": sum(p["data"]["metadata"]["entropy"] for p in self.plugins.values()) / len(self.plugins),
                "std": sum((p["data"]["metadata"]["entropy"] - sum(p["data"]["metadata"]["entropy"] for p in self.plugins.values()) / len(self.plugins))**2 for p in self.plugins.values()) / len(self.plugins),
                "min": min(p["data"]["metadata"]["entropy"] for p in self.plugins.values()),
                "max": max(p["data"]["metadata"]["entropy"] for p in self.plugins.values())
            },
            "rei_score": {
                "mean": sum(p["data"]["metadata"]["rei_score"] for p in self.plugins.values()) / len(self.plugins),
                "std": sum((p["data"]["metadata"]["rei_score"] - sum(p["data"]["metadata"]["rei_score"] for p in self.plugins.values()) / len(self.plugins))**2 for p in self.plugins.values()) / len(self.plugins),
                "min": min(p["data"]["metadata"]["rei_score"] for p in self.plugins.values()),
                "max": max(p["data"]["metadata"]["rei_score"] for p in self.plugins.values())
            }
        }

# Global instance
plugin_interface = PluginInterface() 