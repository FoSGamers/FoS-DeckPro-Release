import json
import hashlib
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import asyncio
from functools import wraps

class PromptMiddleware:
    def __init__(self):
        self.middleware_chain = []
        self.prompt_history = []
    
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
    
    def add_middleware(self, func: Callable):
        """Add middleware function to the chain"""
        @wraps(func)
        async def wrapper(prompt: str, context: Dict[str, Any], *args, **kwargs):
            # Compute metrics before middleware
            phase_vector = self._compute_phase_vector(prompt, context)
            entropy = self._compute_entropy(prompt)
            rei_score = self._compute_rei_score(phase_vector)
            
            # Record pre-middleware state
            pre_state = {
                "prompt": prompt,
                "context": context,
                "metadata": {
                    "phase_vector": phase_vector,
                    "entropy": entropy,
                    "rei_score": rei_score,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Apply middleware
            result = await func(prompt, context, *args, **kwargs)
            
            # Compute metrics after middleware
            post_phase_vector = self._compute_phase_vector(result["prompt"], result["context"])
            post_entropy = self._compute_entropy(result["prompt"])
            post_rei_score = self._compute_rei_score(post_phase_vector)
            
            # Record post-middleware state
            post_state = {
                "prompt": result["prompt"],
                "context": result["context"],
                "metadata": {
                    "phase_vector": post_phase_vector,
                    "entropy": post_entropy,
                    "rei_score": post_rei_score,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Add to history
            self.prompt_history.append({
                "middleware": func.__name__,
                "pre_state": pre_state,
                "post_state": post_state
            })
            
            return result
        
        self.middleware_chain.append(wrapper)
        return wrapper
    
    async def process_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process prompt through middleware chain with APTPT/HCE/REI analysis"""
        current = {"prompt": prompt, "context": context}
        
        for middleware in self.middleware_chain:
            current = await middleware(current["prompt"], current["context"])
        
        return current
    
    def get_prompt_history(self) -> List[Dict[str, Any]]:
        """Get prompt history with APTPT/HCE/REI metrics"""
        return self.prompt_history
    
    def analyze_middleware_convergence(self) -> Dict[str, Any]:
        """Analyze middleware convergence using APTPT/HCE/REI theory"""
        if not self.prompt_history:
            return {
                "convergence": False,
                "reason": "No prompt history available"
            }
        
        # Analyze phase vector convergence
        pre_phases = [h["pre_state"]["metadata"]["phase_vector"] for h in self.prompt_history]
        post_phases = [h["post_state"]["metadata"]["phase_vector"] for h in self.prompt_history]
        unique_pre_phases = len(set(pre_phases))
        unique_post_phases = len(set(post_phases))
        
        # Analyze entropy stability
        pre_entropies = [h["pre_state"]["metadata"]["entropy"] for h in self.prompt_history]
        post_entropies = [h["post_state"]["metadata"]["entropy"] for h in self.prompt_history]
        pre_entropy_std = sum((e - sum(pre_entropies)/len(pre_entropies))**2 for e in pre_entropies) / len(pre_entropies)
        post_entropy_std = sum((e - sum(post_entropies)/len(post_entropies))**2 for e in post_entropies) / len(post_entropies)
        
        # Analyze REI score stability
        pre_rei_scores = [h["pre_state"]["metadata"]["rei_score"] for h in self.prompt_history]
        post_rei_scores = [h["post_state"]["metadata"]["rei_score"] for h in self.prompt_history]
        pre_rei_std = sum((r - sum(pre_rei_scores)/len(pre_rei_scores))**2 for r in pre_rei_scores) / len(pre_rei_scores)
        post_rei_std = sum((r - sum(post_rei_scores)/len(post_rei_scores))**2 for r in post_rei_scores) / len(post_rei_scores)
        
        return {
            "convergence": unique_post_phases < unique_pre_phases,
            "phase_diversity_reduction": (unique_pre_phases - unique_post_phases) / unique_pre_phases,
            "entropy_stability_improvement": (pre_entropy_std - post_entropy_std) / pre_entropy_std,
            "rei_stability_improvement": (pre_rei_std - post_rei_std) / pre_rei_std,
            "total_prompts": len(self.prompt_history)
        }
    
    def cleanup_old_history(self, days: int = 30):
        """Clean up old prompt history"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        self.prompt_history = [
            h for h in self.prompt_history
            if datetime.fromisoformat(h["pre_state"]["metadata"]["timestamp"]).timestamp() > cutoff
        ]

# Global instance
prompt_middleware = PromptMiddleware() 