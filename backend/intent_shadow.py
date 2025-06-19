import random
import hashlib
from typing import List, Dict, Any
from datetime import datetime

class ShadowEngine:
    def __init__(self):
        self.shadow_history = []
    
    def _compute_phase_vector(self, prompt: str, context: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{prompt}{str(context)}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, text: str) -> float:
        """Compute entropy using HCE theory"""
        if not text:
            return 0.0
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(text)
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
    
    def spawn_shadows(self, prompt: str, context: Dict[str, Any], num: int = 3) -> List[Dict[str, Any]]:
        """Spawn shadow prompts with APTPT/HCE/REI variations"""
        base_phase_vector = self._compute_phase_vector(prompt, context)
        base_entropy = self._compute_entropy(prompt)
        base_rei_score = self._compute_rei_score(base_phase_vector)
        
        shadows = []
        for i in range(num):
            # Create shadow context with APTPT variations
            shadow_context = context.copy()
            shadow_context["APTPT_Gain"] = round(random.uniform(0.10, 0.18), 3)
            shadow_context["REI_Xi"] = context.get("REI_Xi", 7.24e-12) * random.uniform(0.9, 1.1)
            shadow_context["Shadow"] = f"shadow_{i}"
            
            # Compute shadow metrics
            shadow_phase_vector = self._compute_phase_vector(prompt, shadow_context)
            shadow_entropy = self._compute_entropy(prompt + str(shadow_context))
            shadow_rei_score = self._compute_rei_score(shadow_phase_vector)
            
            # Create shadow prompt
            shadow_prompt = f"{prompt}\n[PhaseSynth Shadow Mode]\n{str(shadow_context)}"
            
            # Record shadow
            shadow_data = {
                "prompt": shadow_prompt,
                "context": shadow_context,
                "metadata": {
                    "phase_vector": shadow_phase_vector,
                    "entropy": shadow_entropy,
                    "rei_score": shadow_rei_score,
                    "timestamp": datetime.now().isoformat(),
                    "base_phase_vector": base_phase_vector,
                    "base_entropy": base_entropy,
                    "base_rei_score": base_rei_score
                }
            }
            
            shadows.append(shadow_data)
            self.shadow_history.append(shadow_data)
        
        return shadows
    
    def get_shadow_history(self) -> List[Dict[str, Any]]:
        """Get shadow history with APTPT/HCE/REI metrics"""
        return self.shadow_history
    
    def analyze_shadow_convergence(self) -> Dict[str, Any]:
        """Analyze shadow convergence using APTPT/HCE/REI theory"""
        if not self.shadow_history:
            return {
                "convergence": False,
                "reason": "No shadow history available"
            }
        
        # Analyze phase vector convergence
        phase_vectors = [s["metadata"]["phase_vector"] for s in self.shadow_history]
        unique_phases = len(set(phase_vectors))
        
        # Analyze entropy stability
        entropies = [s["metadata"]["entropy"] for s in self.shadow_history]
        entropy_std = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        
        # Analyze REI score stability
        rei_scores = [s["metadata"]["rei_score"] for s in self.shadow_history]
        rei_std = sum((r - sum(rei_scores)/len(rei_scores))**2 for r in rei_scores) / len(rei_scores)
        
        return {
            "convergence": unique_phases < len(phase_vectors) * 0.5,
            "phase_diversity": unique_phases / len(phase_vectors),
            "entropy_stability": 1.0 - min(entropy_std, 1.0),
            "rei_stability": 1.0 - min(rei_std, 1.0),
            "total_shadows": len(self.shadow_history)
        }
    
    def cleanup_old_shadows(self, days: int = 30):
        """Clean up old shadow history"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        self.shadow_history = [
            s for s in self.shadow_history
            if datetime.fromisoformat(s["metadata"]["timestamp"]).timestamp() > cutoff
        ]

# Global instance
shadow_engine = ShadowEngine() 