import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from PIL import Image
import numpy as np

class MultimodalPromptEngine:
    def __init__(self, media_dir: str = "media"):
        self.media_dir = media_dir
        os.makedirs(media_dir, exist_ok=True)
        self.prompt_history = []
    
    def _compute_phase_vector(self, text: str, images: List[str], audio: List[str]) -> str:
        """Compute phase vector using APTPT theory"""
        # Combine all inputs
        combined = text
        for img in images:
            if os.path.exists(img):
                with open(img, 'rb') as f:
                    combined += hashlib.sha256(f.read()).hexdigest()
        for aud in audio:
            if os.path.exists(aud):
                with open(aud, 'rb') as f:
                    combined += hashlib.sha256(f.read()).hexdigest()
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, text: str, images: List[str], audio: List[str]) -> float:
        """Compute entropy using HCE theory"""
        total_entropy = 0.0
        count = 0
        
        # Text entropy
        if text:
            char_freq = {}
            for char in text:
                char_freq[char] = char_freq.get(char, 0) + 1
            total = len(text)
            for count in char_freq.values():
                p = count / total
                total_entropy -= p * math.log2(p) if p > 0 else 0
            count += 1
        
        # Image entropy
        for img in images:
            if os.path.exists(img):
                try:
                    with Image.open(img) as im:
                        img_array = np.array(im)
                        hist = np.histogram(img_array, bins=256)[0]
                        hist = hist[hist > 0]
                        p = hist / hist.sum()
                        total_entropy -= np.sum(p * np.log2(p))
                        count += 1
                except Exception:
                    continue
        
        # Audio entropy (simplified)
        for aud in audio:
            if os.path.exists(aud):
                try:
                    with open(aud, 'rb') as f:
                        data = f.read()
                        byte_freq = {}
                        for byte in data:
                            byte_freq[byte] = byte_freq.get(byte, 0) + 1
                        total = len(data)
                        for count in byte_freq.values():
                            p = count / total
                            total_entropy -= p * math.log2(p) if p > 0 else 0
                        count += 1
                except Exception:
                    continue
        
        return total_entropy / max(count, 1)
    
    def _compute_rei_score(self, phase_vector: str) -> float:
        """Compute REI score using REI theory"""
        if not phase_vector:
            return 0.0
        # REI score based on phase vector properties
        return sum(ord(c) for c in phase_vector[:8]) / (8 * 255)
    
    def process_prompt(self, 
                      text: str, 
                      images: List[str] = None, 
                      audio: List[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process multimodal prompt with APTPT/HCE/REI analysis"""
        images = images or []
        audio = audio or []
        context = context or {}
        
        # Compute metrics
        phase_vector = self._compute_phase_vector(text, images, audio)
        entropy = self._compute_entropy(text, images, audio)
        rei_score = self._compute_rei_score(phase_vector)
        
        # Create prompt data
        prompt_data = {
            "text": text,
            "images": images,
            "audio": audio,
            "context": context,
            "metadata": {
                "phase_vector": phase_vector,
                "entropy": entropy,
                "rei_score": rei_score,
                "timestamp": datetime.now().isoformat(),
                "media_count": len(images) + len(audio)
            }
        }
        
        # Add to history
        self.prompt_history.append(prompt_data)
        
        return prompt_data
    
    def get_prompt_history(self) -> List[Dict[str, Any]]:
        """Get prompt history with APTPT/HCE/REI metrics"""
        return self.prompt_history
    
    def analyze_prompt_convergence(self) -> Dict[str, Any]:
        """Analyze prompt convergence using APTPT/HCE/REI theory"""
        if not self.prompt_history:
            return {
                "convergence": False,
                "reason": "No prompt history available"
            }
        
        # Analyze phase vector convergence
        phase_vectors = [p["metadata"]["phase_vector"] for p in self.prompt_history]
        unique_phases = len(set(phase_vectors))
        
        # Analyze entropy stability
        entropies = [p["metadata"]["entropy"] for p in self.prompt_history]
        entropy_std = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        
        # Analyze REI score stability
        rei_scores = [p["metadata"]["rei_score"] for p in self.prompt_history]
        rei_std = sum((r - sum(rei_scores)/len(rei_scores))**2 for r in rei_scores) / len(rei_scores)
        
        # Analyze media usage
        media_counts = [p["metadata"]["media_count"] for p in self.prompt_history]
        avg_media = sum(media_counts) / len(media_counts)
        
        return {
            "convergence": unique_phases < len(phase_vectors) * 0.5,
            "phase_diversity": unique_phases / len(phase_vectors),
            "entropy_stability": 1.0 - min(entropy_std, 1.0),
            "rei_stability": 1.0 - min(rei_std, 1.0),
            "avg_media_per_prompt": avg_media,
            "total_prompts": len(self.prompt_history)
        }
    
    def cleanup_old_prompts(self, days: int = 30):
        """Clean up old prompt history and media files"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Clean up history
        self.prompt_history = [
            p for p in self.prompt_history
            if datetime.fromisoformat(p["metadata"]["timestamp"]).timestamp() > cutoff
        ]
        
        # Clean up media files
        for prompt in self.prompt_history:
            for img in prompt["images"]:
                if os.path.exists(img):
                    try:
                        os.remove(img)
                    except Exception:
                        continue
            for aud in prompt["audio"]:
                if os.path.exists(aud):
                    try:
                        os.remove(aud)
                    except Exception:
                        continue

# Global instance
multimodal_engine = MultimodalPromptEngine() 