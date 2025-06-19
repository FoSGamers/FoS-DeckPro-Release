import pickle
import os
import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

SNAP_DIR = "phase_snapshots"
os.makedirs(SNAP_DIR, exist_ok=True)

class TimeTravel:
    def __init__(self):
        self._init_snap_dir()
    
    def _init_snap_dir(self):
        """Initialize snapshot directory with APTPT/HCE/REI metadata"""
        if not os.path.exists(SNAP_DIR):
            os.makedirs(SNAP_DIR)
            # Create metadata file
            with open(os.path.join(SNAP_DIR, "metadata.json"), "w") as f:
                f.write('{"phase_vectors": {}, "entropy_history": [], "rei_scores": []}')
    
    def _compute_phase_vector(self, state: Dict[str, Any], context: Dict[str, Any], phase: str) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{str(state)}{str(context)}{phase}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, data: Dict[str, Any]) -> float:
        """Compute entropy using HCE theory"""
        if not data:
            return 0.0
        # Convert dict to string for entropy calculation
        text = str(data)
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
    
    def save_snapshot(self, state: Dict[str, Any], context: Dict[str, Any], phase: str) -> str:
        """Save snapshot with APTPT/HCE/REI metadata"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        phase_vector = self._compute_phase_vector(state, context, phase)
        entropy = self._compute_entropy(state)
        rei_score = self._compute_rei_score(phase_vector)
        
        # Create snapshot data
        snapshot = {
            "state": state,
            "context": context,
            "phase": phase,
            "metadata": {
                "timestamp": timestamp,
                "phase_vector": phase_vector,
                "entropy": entropy,
                "rei_score": rei_score
            }
        }
        
        # Save snapshot
        filename = f"snapshot_{timestamp}_{phase_vector[:12]}.bin"
        filepath = os.path.join(SNAP_DIR, filename)
        with open(filepath, "wb") as f:
            pickle.dump(snapshot, f)
        
        # Update metadata
        self._update_metadata(phase_vector, entropy, rei_score)
        
        return filename
    
    def _update_metadata(self, phase_vector: str, entropy: float, rei_score: float):
        """Update snapshot metadata with APTPT/HCE/REI metrics"""
        metadata_path = os.path.join(SNAP_DIR, "metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"phase_vectors": {}, "entropy_history": [], "rei_scores": []}
        
        # Update metadata
        metadata["phase_vectors"][phase_vector] = time.time()
        metadata["entropy_history"].append(entropy)
        metadata["rei_scores"].append(rei_score)
        
        # Keep only last 1000 entries
        metadata["entropy_history"] = metadata["entropy_history"][-1000:]
        metadata["rei_scores"] = metadata["rei_scores"][-1000:]
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)
    
    def restore_snapshot(self, moment: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        """Restore snapshot with APTPT/HCE/REI validation"""
        files = sorted(os.listdir(SNAP_DIR))
        if not files:
            raise ValueError("No snapshots available")
        
        if moment is None:
            # Get latest snapshot
            target = files[-1]
        else:
            # Find snapshot matching moment
            matching = [f for f in files if moment in f]
            if not matching:
                raise ValueError(f"No snapshot found for moment: {moment}")
            target = matching[0]
        
        # Load and validate snapshot
        with open(os.path.join(SNAP_DIR, target), "rb") as f:
            snapshot = pickle.load(f)
        
        # Validate phase vector
        current_phase_vector = self._compute_phase_vector(
            snapshot["state"],
            snapshot["context"],
            snapshot["phase"]
        )
        
        if current_phase_vector != snapshot["metadata"]["phase_vector"]:
            raise ValueError("Snapshot phase vector mismatch - possible corruption")
        
        return snapshot["state"], snapshot["context"], snapshot["phase"]
    
    def list_snapshots(self) -> list:
        """List available snapshots with APTPT/HCE/REI metadata"""
        snapshots = []
        for filename in sorted(os.listdir(SNAP_DIR)):
            if filename.endswith(".bin"):
                filepath = os.path.join(SNAP_DIR, filename)
                with open(filepath, "rb") as f:
                    snapshot = pickle.load(f)
                    snapshots.append({
                        "timestamp": snapshot["metadata"]["timestamp"],
                        "phase_vector": snapshot["metadata"]["phase_vector"],
                        "entropy": snapshot["metadata"]["entropy"],
                        "rei_score": snapshot["metadata"]["rei_score"]
                    })
        return snapshots
    
    def cleanup_old_snapshots(self, days: int = 30):
        """Clean up old snapshots while preserving APTPT/HCE/REI history"""
        cutoff = time.time() - (days * 24 * 60 * 60)
        metadata_path = os.path.join(SNAP_DIR, "metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            # Remove old phase vectors
            metadata["phase_vectors"] = {
                pv: ts for pv, ts in metadata["phase_vectors"].items()
                if ts > cutoff
            }
            
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)
        
        # Remove old snapshot files
        for filename in os.listdir(SNAP_DIR):
            if filename.endswith(".bin"):
                filepath = os.path.join(SNAP_DIR, filename)
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)

# Global instance
time_travel = TimeTravel() 