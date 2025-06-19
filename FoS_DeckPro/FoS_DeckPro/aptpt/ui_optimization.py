"""
UI Optimization System using APTPT/REI/HCE theories
"""
from typing import Dict, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer

from .unified_system import UnifiedSystemManager

class UIOptimizer:
    """
    UI optimization system using unified APTPT/REI/HCE control
    """
    def __init__(self):
        self.system_manager = UnifiedSystemManager()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_optimization)
        self.update_timer.setInterval(100)  # 10 Hz update rate
        
        self.monitored_widgets: Dict[str, QWidget] = {}
        self.performance_metrics: Dict[str, float] = {}
    
    def start_optimization(self):
        """Start UI optimization"""
        self.system_manager.start_optimization()
        self.update_timer.start()
    
    def stop_optimization(self):
        """Stop UI optimization"""
        self.update_timer.stop()
        self.system_manager.stop_optimization()
    
    def register_widget(self, widget_id: str, widget: QWidget):
        """Register a widget for optimization"""
        self.monitored_widgets[widget_id] = widget
        self.performance_metrics[widget_id] = 1.0  # Initial performance
    
    def unregister_widget(self, widget_id: str):
        """Unregister a widget"""
        self.monitored_widgets.pop(widget_id, None)
        self.performance_metrics.pop(widget_id, None)
    
    def _update_optimization(self):
        """Update optimization state"""
        try:
            # Get current system status
            status = self.system_manager.get_optimization_status()
            
            # Apply optimizations based on phase
            if status["phase"] == "recovering":
                self._apply_recovery_optimizations()
            elif status["phase"] == "adapting":
                self._apply_adaptive_optimizations()
            elif status["phase"] == "stable":
                self._apply_stability_optimizations()
            
            # Update widget states
            for widget_id, widget in self.monitored_widgets.items():
                if not widget or not widget.isVisible():
                    continue
                
                # Apply APTPT control
                self._optimize_widget_responsiveness(widget, status["adaptation_gain"])
                
                # Apply REI optimization
                self._optimize_widget_layout(widget, status["rei_constant"])
                
                # Apply HCE stabilization
                self._stabilize_widget_state(widget, status["hce_field_strength"])
        
        except Exception as e:
            print(f"UI optimization error: {e}")
    
    def _apply_recovery_optimizations(self):
        """Apply recovery phase optimizations"""
        for widget in self.monitored_widgets.values():
            if not widget or not widget.isVisible():
                continue
            
            # Reduce update frequency
            widget.setUpdatesEnabled(False)
            QTimer.singleShot(50, lambda w=widget: w.setUpdatesEnabled(True))
    
    def _apply_adaptive_optimizations(self):
        """Apply adaptive phase optimizations"""
        for widget in self.monitored_widgets.values():
            if not widget or not widget.isVisible():
                continue
            
            # Enable smooth updates
            widget.setUpdatesEnabled(True)
    
    def _apply_stability_optimizations(self):
        """Apply stability phase optimizations"""
        for widget in self.monitored_widgets.values():
            if not widget or not widget.isVisible():
                continue
            
            # Enable full optimization
            widget.setUpdatesEnabled(True)
    
    def _optimize_widget_responsiveness(self, widget: QWidget, gain: float):
        """Optimize widget responsiveness using APTPT"""
        # Adjust update rate based on gain
        update_interval = int(100 * (1.0 - gain))  # 0-100ms
        if hasattr(widget, 'updateTimer'):
            widget.updateTimer.setInterval(max(16, update_interval))  # Min 16ms (60 FPS)
    
    def _optimize_widget_layout(self, widget: QWidget, rei_constant: float):
        """Optimize widget layout using REI"""
        # Apply REI-based layout optimization
        if hasattr(widget, 'layout'):
            layout = widget.layout()
            if layout:
                # Adjust layout spacing
                layout.setSpacing(int(10 * rei_constant))
                layout.setContentsMargins(
                    int(10 * rei_constant),
                    int(10 * rei_constant),
                    int(10 * rei_constant),
                    int(10 * rei_constant)
                )
    
    def _stabilize_widget_state(self, widget: QWidget, field_strength: float):
        """Stabilize widget state using HCE"""
        # Apply HCE-based state stabilization
        if hasattr(widget, 'setProperty'):
            # Adjust widget properties based on field strength
            opacity = min(1.0, field_strength / 31.37528394793422)
            widget.setProperty('opacity', opacity)
            
            # Force style update
            widget.style().unpolish(widget)
            widget.style().polish(widget) 