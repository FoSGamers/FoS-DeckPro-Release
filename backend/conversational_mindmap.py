import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import networkx as nx

class MindMapEngine:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.conversation_history = []
    
    def _compute_phase_vector(self, text: str, context: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{text}{str(context)}"
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
    
    def add_node(self, 
                text: str, 
                node_type: str = "concept",
                context: Optional[Dict[str, Any]] = None,
                parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Add a node to the mindmap with APTPT/HCE/REI analysis"""
        context = context or {}
        
        # Compute metrics
        phase_vector = self._compute_phase_vector(text, context)
        entropy = self._compute_entropy(text)
        rei_score = self._compute_rei_score(phase_vector)
        
        # Create node data
        node_id = hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()
        node_data = {
            "id": node_id,
            "text": text,
            "type": node_type,
            "context": context,
            "metadata": {
                "phase_vector": phase_vector,
                "entropy": entropy,
                "rei_score": rei_score,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add to graph
        self.graph.add_node(node_id, **node_data)
        if parent_id and parent_id in self.graph:
            self.graph.add_edge(parent_id, node_id)
        
        # Add to conversation history
        self.conversation_history.append({
            "action": "add_node",
            "node": node_data,
            "parent_id": parent_id
        })
        
        return node_data
    
    def add_connection(self, 
                      source_id: str, 
                      target_id: str, 
                      connection_type: str = "related",
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a connection between nodes with APTPT/HCE/REI analysis"""
        if source_id not in self.graph or target_id not in self.graph:
            raise ValueError("Source or target node not found")
        
        context = context or {}
        
        # Compute metrics
        source_text = self.graph.nodes[source_id]["text"]
        target_text = self.graph.nodes[target_id]["text"]
        phase_vector = self._compute_phase_vector(f"{source_text}->{target_text}", context)
        entropy = self._compute_entropy(f"{source_text}->{target_text}")
        rei_score = self._compute_rei_score(phase_vector)
        
        # Create connection data
        connection_data = {
            "type": connection_type,
            "context": context,
            "metadata": {
                "phase_vector": phase_vector,
                "entropy": entropy,
                "rei_score": rei_score,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add to graph
        self.graph.add_edge(source_id, target_id, **connection_data)
        
        # Add to conversation history
        self.conversation_history.append({
            "action": "add_connection",
            "connection": connection_data,
            "source_id": source_id,
            "target_id": target_id
        })
        
        return connection_data
    
    def get_mindmap(self) -> Dict[str, Any]:
        """Get complete mindmap with APTPT/HCE/REI metrics"""
        return {
            "nodes": [self.graph.nodes[n] for n in self.graph.nodes()],
            "edges": [self.graph.edges[e] for e in self.graph.edges()],
            "conversation_history": self.conversation_history
        }
    
    def analyze_mindmap_convergence(self) -> Dict[str, Any]:
        """Analyze mindmap convergence using APTPT/HCE/REI theory"""
        if not self.graph.nodes():
            return {
                "convergence": False,
                "reason": "No nodes in mindmap"
            }
        
        # Analyze phase vector convergence
        phase_vectors = [n["metadata"]["phase_vector"] for n in self.graph.nodes.values()]
        unique_phases = len(set(phase_vectors))
        
        # Analyze entropy stability
        entropies = [n["metadata"]["entropy"] for n in self.graph.nodes.values()]
        entropy_std = sum((e - sum(entropies)/len(entropies))**2 for e in entropies) / len(entropies)
        
        # Analyze REI score stability
        rei_scores = [n["metadata"]["rei_score"] for n in self.graph.nodes.values()]
        rei_std = sum((r - sum(rei_scores)/len(rei_scores))**2 for r in rei_scores) / len(rei_scores)
        
        # Analyze graph structure
        avg_degree = sum(dict(self.graph.degree()).values()) / len(self.graph)
        density = nx.density(self.graph)
        
        return {
            "convergence": unique_phases < len(phase_vectors) * 0.5,
            "phase_diversity": unique_phases / len(phase_vectors),
            "entropy_stability": 1.0 - min(entropy_std, 1.0),
            "rei_stability": 1.0 - min(rei_std, 1.0),
            "avg_node_degree": avg_degree,
            "graph_density": density,
            "total_nodes": len(self.graph.nodes()),
            "total_edges": len(self.graph.edges())
        }
    
    def cleanup_old_nodes(self, days: int = 30):
        """Clean up old nodes and connections"""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        # Find old nodes
        old_nodes = [
            n for n, data in self.graph.nodes(data=True)
            if datetime.fromisoformat(data["metadata"]["timestamp"]).timestamp() <= cutoff
        ]
        
        # Remove old nodes and their connections
        self.graph.remove_nodes_from(old_nodes)
        
        # Clean up conversation history
        self.conversation_history = [
            h for h in self.conversation_history
            if datetime.fromisoformat(h["node"]["metadata"]["timestamp"]).timestamp() > cutoff
        ]

# Global instance
mindmap_engine = MindMapEngine() 