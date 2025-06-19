import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import markdown
from bs4 import BeautifulSoup

class UltraDocsEngine:
    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = docs_dir
        os.makedirs(docs_dir, exist_ok=True)
        self.docs_history = []
    
    def _compute_phase_vector(self, content: str, metadata: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{content}{str(metadata)}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, content: str) -> float:
        """Compute entropy using HCE theory"""
        if not content:
            return 0.0
        char_freq = {}
        for char in content:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(content)
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
    
    def create_doc(self, 
                  title: str,
                  content: str,
                  doc_type: str = "markdown",
                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new document with APTPT/HCE/REI analysis"""
        metadata = metadata or {}
        
        # Compute metrics
        phase_vector = self._compute_phase_vector(content, metadata)
        entropy = self._compute_entropy(content)
        rei_score = self._compute_rei_score(phase_vector)
        
        # Create doc data
        doc_id = hashlib.md5(f"{title}{datetime.now().isoformat()}".encode()).hexdigest()
        doc_data = {
            "id": doc_id,
            "title": title,
            "content": content,
            "type": doc_type,
            "metadata": {
                "phase_vector": phase_vector,
                "entropy": entropy,
                "rei_score": rei_score,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Save to file
        file_path = os.path.join(self.docs_dir, f"{doc_id}.{doc_type}")
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Add to history
        self.docs_history.append({
            "action": "create",
            "doc": doc_data,
            "file_path": file_path
        })
        
        return doc_data
    
    def update_doc(self,
                  doc_id: str,
                  content: str,
                  metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update an existing document with APTPT/HCE/REI analysis"""
        # Find doc in history
        doc_entry = next((h for h in self.docs_history if h["doc"]["id"] == doc_id), None)
        if not doc_entry:
            raise ValueError("Document not found")
        
        metadata = metadata or {}
        
        # Compute metrics
        phase_vector = self._compute_phase_vector(content, metadata)
        entropy = self._compute_entropy(content)
        rei_score = self._compute_rei_score(phase_vector)
        
        # Update doc data
        doc_data = doc_entry["doc"].copy()
        doc_data["content"] = content
        doc_data["metadata"].update({
            "phase_vector": phase_vector,
            "entropy": entropy,
            "rei_score": rei_score,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update file
        with open(doc_entry["file_path"], 'w') as f:
            f.write(content)
        
        # Add to history
        self.docs_history.append({
            "action": "update",
            "doc": doc_data,
            "file_path": doc_entry["file_path"]
        })
        
        return doc_data
    
    def get_doc(self, doc_id: str) -> Dict[str, Any]:
        """Get document by ID"""
        doc_entry = next((h for h in self.docs_history if h["doc"]["id"] == doc_id), None)
        if not doc_entry:
            raise ValueError("Document not found")
        return doc_entry["doc"]
    
    def list_docs(self) -> List[Dict[str, Any]]:
        """List all documents with APTPT/HCE/REI metrics"""
        return [h["doc"] for h in self.docs_history]
    
    def analyze_docs_convergence(self) -> Dict[str, Any]:
        """Analyze docs convergence using APTPT/HCE/REI theory"""
        if not self.docs_history:
            return {
                "convergence": False,
                "reason": "No documents available"
            }
        
        # Analyze phase vector convergence
        phase_vectors = [h["doc"]["metadata"]["phase_vector"] for h in self.docs_history]
        unique_phases = len(set(phase_vectors))
        
        # Analyze entropy stability
        entropies = [h["doc"]["metadata"]["entropy"] for h in self.docs_history]
        entropy_std = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        
        # Analyze REI score stability
        rei_scores = [h["doc"]["metadata"]["rei_score"] for h in self.docs_history]
        rei_std = sum((r - sum(rei_scores)/len(rei_scores))**2 for r in rei_scores) / len(rei_scores)
        
        # Analyze content structure
        total_chars = sum(len(h["doc"]["content"]) for h in self.docs_history)
        avg_chars = total_chars / len(self.docs_history)
        
        return {
            "convergence": unique_phases < len(phase_vectors) * 0.5,
            "phase_diversity": unique_phases / len(phase_vectors),
            "entropy_stability": 1.0 - min(entropy_std, 1.0),
            "rei_stability": 1.0 - min(rei_std, 1.0),
            "avg_doc_size": avg_chars,
            "total_docs": len(self.docs_history)
        }
    
    def cleanup_old_docs(self, days: int = 30):
        """Clean up old documents and history"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Find old docs
        old_docs = [
            h for h in self.docs_history
            if datetime.fromisoformat(h["doc"]["metadata"]["timestamp"]).timestamp() <= cutoff
        ]
        
        # Remove old files
        for doc in old_docs:
            if os.path.exists(doc["file_path"]):
                try:
                    os.remove(doc["file_path"])
                except Exception:
                    continue
        
        # Clean up history
        self.docs_history = [
            h for h in self.docs_history
            if datetime.fromisoformat(h["doc"]["metadata"]["timestamp"]).timestamp() > cutoff
        ]

# Global instance
docs_engine = UltraDocsEngine() 