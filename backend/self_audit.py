import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import ast
import os

class SelfAuditEngine:
    def __init__(self):
        self.audit_history = []
    
    def _compute_phase_vector(self, code: str, context: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{code}{str(context)}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, code: str) -> float:
        """Compute entropy using HCE theory"""
        if not code:
            return 0.0
        char_freq = {}
        for char in code:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(code)
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
    
    def _analyze_code_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity using AST"""
        try:
            tree = ast.parse(code)
            
            # Count nodes by type
            node_counts = {}
            for node in ast.walk(tree):
                node_type = type(node).__name__
                node_counts[node_type] = node_counts.get(node_type, 0) + 1
            
            # Calculate complexity metrics
            total_nodes = sum(node_counts.values())
            unique_nodes = len(node_counts)
            
            # Calculate cyclomatic complexity
            cyclomatic = sum(1 for node in ast.walk(tree) if isinstance(node, (
                ast.If, ast.While, ast.For, ast.Try, ast.ExceptHandler,
                ast.With, ast.FunctionDef, ast.ClassDef
            )))
            
            return {
                "total_nodes": total_nodes,
                "unique_nodes": unique_nodes,
                "cyclomatic_complexity": cyclomatic,
                "node_distribution": node_counts
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_nodes": 0,
                "unique_nodes": 0,
                "cyclomatic_complexity": 0,
                "node_distribution": {}
            }
    
    def audit_file(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Audit a file with APTPT/HCE/REI analysis"""
        context = context or {}
        
        try:
            # Read file
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Compute metrics
            phase_vector = self._compute_phase_vector(code, context)
            entropy = self._compute_entropy(code)
            rei_score = self._compute_rei_score(phase_vector)
            
            # Analyze code complexity
            complexity = self._compute_code_complexity(code)
            
            # Create audit data
            audit_data = {
                "file_path": file_path,
                "context": context,
                "metadata": {
                    "phase_vector": phase_vector,
                    "entropy": entropy,
                    "rei_score": rei_score,
                    "timestamp": datetime.now().isoformat()
                },
                "complexity": complexity
            }
            
            # Add to history
            self.audit_history.append(audit_data)
            
            return audit_data
            
        except Exception as e:
            raise ValueError(f"Failed to audit file {file_path}: {str(e)}")
    
    def audit_directory(self, dir_path: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Audit a directory with APTPT/HCE/REI analysis"""
        context = context or {}
        results = []
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        audit_data = self.audit_file(file_path, context)
                        results.append(audit_data)
                    except Exception:
                        continue
        
        return results
    
    def get_audit_history(self) -> List[Dict[str, Any]]:
        """Get audit history with APTPT/HCE/REI metrics"""
        return self.audit_history
    
    def analyze_audit_convergence(self) -> Dict[str, Any]:
        """Analyze audit convergence using APTPT/HCE/REI theory"""
        if not self.audit_history:
            return {
                "convergence": False,
                "reason": "No audit history available"
            }
        
        # Analyze phase vector convergence
        phase_vectors = [h["metadata"]["phase_vector"] for h in self.audit_history]
        unique_phases = len(set(phase_vectors))
        
        # Analyze entropy stability
        entropies = [h["metadata"]["entropy"] for h in self.audit_history]
        entropy_std = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        
        # Analyze REI score stability
        rei_scores = [h["metadata"]["rei_score"] for h in self.audit_history]
        rei_std = sum((r - sum(rei_scores)/len(rei_scores))**2 for r in rei_scores) / len(rei_scores)
        
        # Analyze complexity trends
        complexities = [h["complexity"]["cyclomatic_complexity"] for h in self.audit_history]
        avg_complexity = sum(complexities) / len(complexities)
        
        return {
            "convergence": unique_phases < len(phase_vectors) * 0.5,
            "phase_diversity": unique_phases / len(phase_vectors),
            "entropy_stability": 1.0 - min(entropy_std, 1.0),
            "rei_stability": 1.0 - min(rei_std, 1.0),
            "avg_complexity": avg_complexity,
            "total_audits": len(self.audit_history)
        }
    
    def cleanup_old_history(self, days: int = 30):
        """Clean up old audit history"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        self.audit_history = [
            h for h in self.audit_history
            if datetime.fromisoformat(h["metadata"]["timestamp"]).timestamp() > cutoff
        ]
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit statistics using APTPT/HCE/REI theory"""
        if not self.audit_history:
            return {
                "error": "No audit history available"
            }
        
        return {
            "phase_vector": {
                "unique_count": len(set(h["metadata"]["phase_vector"] for h in self.audit_history)),
                "total_count": len(self.audit_history),
                "diversity": len(set(h["metadata"]["phase_vector"] for h in self.audit_history)) / len(self.audit_history)
            },
            "entropy": {
                "mean": sum(h["metadata"]["entropy"] for h in self.audit_history) / len(self.audit_history),
                "std": sum((h["metadata"]["entropy"] - sum(h["metadata"]["entropy"] for h in self.audit_history) / len(self.audit_history))**2 for h in self.audit_history) / len(self.audit_history),
                "min": min(h["metadata"]["entropy"] for h in self.audit_history),
                "max": max(h["metadata"]["entropy"] for h in self.audit_history)
            },
            "rei_score": {
                "mean": sum(h["metadata"]["rei_score"] for h in self.audit_history) / len(self.audit_history),
                "std": sum((h["metadata"]["rei_score"] - sum(h["metadata"]["rei_score"] for h in self.audit_history) / len(self.audit_history))**2 for h in self.audit_history) / len(self.audit_history),
                "min": min(h["metadata"]["rei_score"] for h in self.audit_history),
                "max": max(h["metadata"]["rei_score"] for h in self.audit_history)
            },
            "complexity": {
                "mean": sum(h["complexity"]["cyclomatic_complexity"] for h in self.audit_history) / len(self.audit_history),
                "std": sum((h["complexity"]["cyclomatic_complexity"] - sum(h["complexity"]["cyclomatic_complexity"] for h in self.audit_history) / len(self.audit_history))**2 for h in self.audit_history) / len(self.audit_history),
                "min": min(h["complexity"]["cyclomatic_complexity"] for h in self.audit_history),
                "max": max(h["complexity"]["cyclomatic_complexity"] for h in self.audit_history)
            }
        }

# Global instance
audit_engine = SelfAuditEngine() 