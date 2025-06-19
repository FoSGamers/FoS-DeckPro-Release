"""
Unified System Manager for FoS_DeckPro
Integrates APTPT, REI, and HCE theories for optimal performance and stability
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import threading
import queue

from .aptpt_control_system import aptpt_controller
from .rei_system import rei_system
from .hce_system import hce_system

class SystemMode(Enum):
    """Unified system operational modes"""
    OPTIMAL = "optimal"
    ADAPTING = "adapting"
    RECOVERING = "recovering"
    OPTIMIZING = "optimizing"
    STABILIZING = "stabilizing"

@dataclass
class UnifiedMetrics:
    """Unified system metrics combining all three theories"""
    aptpt_error_norm: float
    rei_constant: float
    hce_field_strength: float
    overall_stability: float
    performance_index: float
    convergence_rate: float

class UnifiedSystemManager:
    """
    Unified System Manager for FoS_DeckPro
    
    Integrates APTPT, REI, and HCE theories to ensure:
    - APTPT: Robust feedback control and convergence
    - REI: Universal proportionality and energy optimization
    - HCE: Harmonic convergence and biological stability
    """
    
    def __init__(self):
        self.current_mode = SystemMode.OPTIMAL
        self.operation_history = []
        self.optimization_history = []
        
        # Performance thresholds
        self.optimal_threshold = 0.95
        self.adapting_threshold = 0.85
        self.recovering_threshold = 0.70
        
        # Integration weights
        self.aptpt_weight = 0.4
        self.rei_weight = 0.3
        self.hce_weight = 0.3
        
        # Control loop
        self.control_thread = None
        self.running = False
        self.control_queue = queue.Queue()
        
    def start_unified_control(self):
        """Start the unified control system"""
        if self.control_thread is None or not self.control_thread.is_alive():
            self.running = True
            self.control_thread = threading.Thread(target=self._unified_control_loop, daemon=True)
            self.control_thread.start()
            
            # Start individual system controllers
            aptpt_controller.start_control_loop()
    
    def stop_unified_control(self):
        """Stop the unified control system"""
        self.running = False
        aptpt_controller.stop_control_loop()
        
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
    
    def _unified_control_loop(self):
        """Main unified control loop"""
        while self.running:
            try:
                # Get metrics from all three systems
                unified_metrics = self._get_unified_metrics()
                
                # Determine system mode
                self._determine_system_mode(unified_metrics)
                
                # Apply unified optimization
                self._apply_unified_optimization(unified_metrics)
                
                # Log unified state
                self._log_unified_state(unified_metrics)
                
                time.sleep(0.5)  # 2Hz control rate
                
            except Exception as e:
                self._log_error(f"Unified control error: {e}")
                time.sleep(1.0)
    
    def _get_unified_metrics(self) -> UnifiedMetrics:
        """Get unified metrics from all three systems"""
        # Get APTPT metrics
        aptpt_status = aptpt_controller.get_control_status()
        aptpt_error_norm = aptpt_status.get('error_norm', 0.0)
        
        # Get REI metrics
        rei_status = rei_system.get_system_status()
        rei_constant = rei_status.get('rei_constant', 1.618)
        
        # Get HCE metrics
        hce_status = hce_system.get_system_status()
        hce_field_strength = hce_status.get('field_strength', 1.0)
        
        # Calculate unified metrics
        overall_stability = self._calculate_overall_stability(aptpt_status, rei_status, hce_status)
        performance_index = self._calculate_performance_index(aptpt_status, rei_status, hce_status)
        convergence_rate = self._calculate_convergence_rate(aptpt_status, rei_status, hce_status)
        
        return UnifiedMetrics(
            aptpt_error_norm=aptpt_error_norm,
            rei_constant=rei_constant,
            hce_field_strength=hce_field_strength,
            overall_stability=overall_stability,
            performance_index=performance_index,
            convergence_rate=convergence_rate
        )
    
    def _calculate_overall_stability(self, aptpt_status: Dict, rei_status: Dict, hce_status: Dict) -> float:
        """Calculate overall system stability"""
        # Weighted combination of stability metrics
        aptpt_stability = 1.0 - aptpt_status.get('error_norm', 0.0)
        rei_stability = rei_status.get('stability_index', 0.0)
        hce_stability = hce_status.get('neural_stability', 0.0)
        
        overall_stability = (
            self.aptpt_weight * aptpt_stability +
            self.rei_weight * rei_stability +
            self.hce_weight * hce_stability
        )
        
        return min(overall_stability, 1.0)
    
    def _calculate_performance_index(self, aptpt_status: Dict, rei_status: Dict, hce_status: Dict) -> float:
        """Calculate overall performance index"""
        # Combine performance metrics from all systems
        aptpt_performance = 1.0 - aptpt_status.get('error_norm', 0.0)
        rei_performance = rei_status.get('stability_index', 0.0)
        hce_performance = hce_status.get('field_strength', 0.0)
        
        performance_index = (
            self.aptpt_weight * aptpt_performance +
            self.rei_weight * rei_performance +
            self.hce_weight * hce_performance
        )
        
        return min(performance_index, 1.0)
    
    def _calculate_convergence_rate(self, aptpt_status: Dict, rei_status: Dict, hce_status: Dict) -> float:
        """Calculate overall convergence rate"""
        # Combine convergence metrics from all systems
        aptpt_convergence = aptpt_status.get('convergence_rate', 0.0)
        rei_convergence = rei_status.get('energy_transition', 0.0)
        hce_convergence = hce_status.get('convergence_rate', 0.0)
        
        convergence_rate = (
            self.aptpt_weight * aptpt_convergence +
            self.rei_weight * rei_convergence +
            self.hce_weight * hce_convergence
        )
        
        return min(convergence_rate, 1.0)
    
    def _determine_system_mode(self, metrics: UnifiedMetrics):
        """Determine the current system mode based on unified metrics"""
        if metrics.overall_stability >= self.optimal_threshold:
            self.current_mode = SystemMode.OPTIMAL
        elif metrics.overall_stability >= self.adapting_threshold:
            self.current_mode = SystemMode.ADAPTING
        elif metrics.overall_stability >= self.recovering_threshold:
            self.current_mode = SystemMode.RECOVERING
        else:
            self.current_mode = SystemMode.STABILIZING
    
    def _apply_unified_optimization(self, metrics: UnifiedMetrics):
        """Apply unified optimization based on current metrics"""
        if self.current_mode == SystemMode.OPTIMAL:
            # System is optimal, maintain current state
            self._maintain_optimal_state()
        elif self.current_mode == SystemMode.ADAPTING:
            # System is adapting, apply gentle optimization
            self._apply_adaptive_optimization(metrics)
        elif self.current_mode == SystemMode.RECOVERING:
            # System is recovering, apply recovery optimization
            self._apply_recovery_optimization(metrics)
        else:
            # System needs stabilization
            self._apply_stabilization_optimization(metrics)
    
    def _maintain_optimal_state(self):
        """Maintain optimal system state"""
        # Fine-tune all systems for optimal performance
        aptpt_controller.optimize_for_operation("ui")
        rei_system.optimize_system("maintenance")
        hce_system.stabilize_system("maintenance")
    
    def _apply_adaptive_optimization(self, metrics: UnifiedMetrics):
        """Apply adaptive optimization"""
        # Optimize based on which system needs attention
        if metrics.aptpt_error_norm > 0.1:
            aptpt_controller.optimize_for_operation("recovery")
        
        if metrics.rei_constant > 2.0:
            rei_system.optimize_system("stabilization")
        
        if metrics.hce_field_strength < 0.8:
            hce_system.stabilize_system("strengthening")
    
    def _apply_recovery_optimization(self, metrics: UnifiedMetrics):
        """Apply recovery optimization"""
        # Apply more aggressive optimization for recovery
        aptpt_controller.optimize_for_operation("recovery")
        rei_system.optimize_system("recovery")
        hce_system.stabilize_system("recovery")
    
    def _apply_stabilization_optimization(self, metrics: UnifiedMetrics):
        """Apply stabilization optimization"""
        # Apply maximum optimization for stabilization
        aptpt_controller.optimize_for_operation("stabilization")
        rei_system.optimize_system("stabilization")
        hce_system.stabilize_system("stabilization")
    
    def optimize_for_operation(self, operation: str):
        """Optimize all systems for a specific operation"""
        # Optimize APTPT for the operation
        aptpt_controller.optimize_for_operation(operation)
        
        # Optimize REI for the operation
        rei_system.optimize_system(operation)
        
        # Optimize HCE for the operation
        hce_system.optimize_for_operation(operation)
        
        # Log operation optimization
        self._log_operation_optimization(operation)
    
    def get_unified_status(self) -> Dict[str, Any]:
        """Get unified system status"""
        metrics = self._get_unified_metrics()
        
        return {
            "mode": self.current_mode.value,
            "overall_stability": metrics.overall_stability,
            "performance_index": metrics.performance_index,
            "convergence_rate": metrics.convergence_rate,
            "aptpt_error_norm": metrics.aptpt_error_norm,
            "rei_constant": metrics.rei_constant,
            "hce_field_strength": metrics.hce_field_strength,
            "running": self.running
        }
    
    def _log_unified_state(self, metrics: UnifiedMetrics):
        """Log unified system state"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": self.current_mode.value,
            "overall_stability": metrics.overall_stability,
            "performance_index": metrics.performance_index,
            "convergence_rate": metrics.convergence_rate,
            "aptpt_error_norm": metrics.aptpt_error_norm,
            "rei_constant": metrics.rei_constant,
            "hce_field_strength": metrics.hce_field_strength,
            "system": "unified"
        }
        
        with open("aptpt_error_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _log_operation_optimization(self, operation: str):
        """Log operation optimization"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "optimization_type": "unified_operation",
            "system": "unified"
        }
        
        with open("aptpt_error_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _log_error(self, message: str):
        """Log error messages"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "message": message,
            "system": "unified"
        }
        with open("aptpt_error_log.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# Global unified system manager instance
unified_manager = UnifiedSystemManager() 