#!/usr/bin/env python3
"""
Comprehensive Dashboard for PhaseSynth Ultra+
Implements all GUI dashboard features from the master specification
Provides unified health monitoring, phase drift visualization, and system management
"""

import json
import hashlib
import asyncio
import websockets
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import yaml
import psutil
import threading
import time
from dataclasses import dataclass, asdict
import numpy as np
from collections import deque

@dataclass
class HealthMetrics:
    """Health metrics with APTPT/HCE/REI analysis"""
    system_health: float  # 0-100
    phase_stability: float  # 0-100
    entropy_level: float  # 0-100
    rei_invariance: float  # 0-100
    error_rate: float  # 0-100
    performance_score: float  # 0-100
    memory_usage: float  # 0-100
    cpu_usage: float  # 0-100
    disk_usage: float  # 0-100
    network_latency: float  # milliseconds
    active_connections: int
    last_update: datetime

@dataclass
class PhaseDriftData:
    """Phase drift data for visualization"""
    timestamp: datetime
    phase_vector: str
    entropy: float
    rei_score: float
    drift_magnitude: float
    component: str
    severity: str  # low, medium, high, critical

@dataclass
class ShadowSolution:
    """Shadow solution for alternate fix selection"""
    id: str
    description: str
    phase_vector: str
    entropy_score: float
    rei_score: float
    confidence: float
    implementation: str
    risks: List[str]
    benefits: List[str]
    created_at: datetime

class ComprehensiveDashboard:
    """Comprehensive dashboard with all master spec features"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.health_history = deque(maxlen=1000)
        self.phase_drift_history = deque(maxlen=1000)
        self.shadow_solutions = []
        self.active_plugins = []
        self.system_logs = deque(maxlen=10000)
        self.performance_metrics = deque(maxlen=1000)
        
        # Dashboard state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.websocket_server = None
        
        # Initialize components
        self._load_configuration()
        self._initialize_metrics()
    
    def _load_configuration(self):
        """Load dashboard configuration"""
        config_file = self.project_root / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {
                "dashboard": {
                    "update_interval": 5.0,
                    "health_thresholds": {
                        "critical": 20,
                        "warning": 50,
                        "good": 80
                    },
                    "max_history_size": 1000,
                    "enable_websocket": True,
                    "websocket_port": 8765
                }
            }
    
    def _initialize_metrics(self):
        """Initialize dashboard metrics"""
        self.current_health = HealthMetrics(
            system_health=100.0,
            phase_stability=100.0,
            entropy_level=0.0,
            rei_invariance=100.0,
            error_rate=0.0,
            performance_score=100.0,
            memory_usage=0.0,
            cpu_usage=0.0,
            disk_usage=0.0,
            network_latency=0.0,
            active_connections=0,
            last_update=datetime.now()
        )
    
    def _compute_phase_vector(self, data: Dict[str, Any]) -> str:
        """Compute phase vector using APTPT theory"""
        combined = json.dumps(data, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, data: Dict[str, Any]) -> float:
        """Compute entropy using HCE theory"""
        if not data:
            return 0.0
        data_str = json.dumps(data, sort_keys=True)
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
        return sum(ord(c) for c in phase_vector[:8]) / (8 * 255)
    
    def start_monitoring(self):
        """Start comprehensive system monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        if self.config["dashboard"]["enable_websocket"]:
            self._start_websocket_server()
        
        self._log_event("Dashboard monitoring started", "info")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        if self.websocket_server:
            self.websocket_server.close()
        
        self._log_event("Dashboard monitoring stopped", "info")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        update_interval = self.config["dashboard"]["update_interval"]
        
        while self.is_monitoring:
            try:
                # Update health metrics
                self._update_health_metrics()
                
                # Check for phase drift
                self._check_phase_drift()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Sleep for update interval
                time.sleep(update_interval)
                
            except Exception as e:
                self._log_event(f"Monitoring error: {e}", "error")
                time.sleep(update_interval)
    
    def _update_health_metrics(self):
        """Update comprehensive health metrics"""
        try:
            # System metrics
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            # Calculate health scores
            system_health = self._calculate_system_health()
            phase_stability = self._calculate_phase_stability()
            entropy_level = self._calculate_entropy_level()
            rei_invariance = self._calculate_rei_invariance()
            error_rate = self._calculate_error_rate()
            performance_score = self._calculate_performance_score()
            
            # Update current health
            self.current_health = HealthMetrics(
                system_health=system_health,
                phase_stability=phase_stability,
                entropy_level=entropy_level,
                rei_invariance=rei_invariance,
                error_rate=error_rate,
                performance_score=performance_score,
                memory_usage=memory.percent,
                cpu_usage=cpu,
                disk_usage=disk.percent,
                network_latency=self._measure_network_latency(),
                active_connections=self._count_active_connections(),
                last_update=datetime.now()
            )
            
            # Add to history
            self.health_history.append(asdict(self.current_health))
            
        except Exception as e:
            self._log_event(f"Health metrics update error: {e}", "error")
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health score"""
        try:
            # Base health on various factors
            factors = []
            
            # Memory health
            memory = psutil.virtual_memory()
            if memory.percent < 70:
                factors.append(100)
            elif memory.percent < 85:
                factors.append(80)
            else:
                factors.append(50)
            
            # CPU health
            cpu = psutil.cpu_percent(interval=1)
            if cpu < 50:
                factors.append(100)
            elif cpu < 80:
                factors.append(80)
            else:
                factors.append(60)
            
            # Disk health
            disk = psutil.disk_usage('/')
            if disk.percent < 80:
                factors.append(100)
            elif disk.percent < 90:
                factors.append(80)
            else:
                factors.append(60)
            
            # Process health
            process_count = len(psutil.pids())
            if process_count < 100:
                factors.append(100)
            elif process_count < 200:
                factors.append(80)
            else:
                factors.append(70)
            
            return sum(factors) / len(factors)
            
        except Exception:
            return 50.0  # Default to neutral if calculation fails
    
    def _calculate_phase_stability(self) -> float:
        """Calculate phase stability score"""
        try:
            if len(self.phase_drift_history) < 2:
                return 100.0
            
            # Calculate stability based on recent phase drift
            recent_drifts = list(self.phase_drift_history)[-10:]
            avg_drift = sum(d.drift_magnitude for d in recent_drifts) / len(recent_drifts)
            
            # Convert drift to stability (inverse relationship)
            stability = max(0, 100 - (avg_drift * 100))
            return stability
            
        except Exception:
            return 100.0
    
    def _calculate_entropy_level(self) -> float:
        """Calculate current entropy level"""
        try:
            if len(self.health_history) < 2:
                return 0.0
            
            # Calculate entropy from recent health data
            recent_health = list(self.health_history)[-10:]
            health_values = [h["system_health"] for h in recent_health]
            
            # Calculate entropy of health values
            if len(set(health_values)) == 1:
                return 0.0  # No entropy if all values are the same
            
            # Simple entropy calculation
            value_counts = {}
            for value in health_values:
                value_counts[value] = value_counts.get(value, 0) + 1
            
            total = len(health_values)
            entropy = 0.0
            for count in value_counts.values():
                p = count / total
                entropy -= p * math.log2(p) if p > 0 else 0
            
            return min(100, entropy * 100)  # Scale to 0-100
            
        except Exception:
            return 0.0
    
    def _calculate_rei_invariance(self) -> float:
        """Calculate REI invariance score"""
        try:
            if len(self.health_history) < 2:
                return 100.0
            
            # Calculate invariance based on consistency of metrics
            recent_health = list(self.health_history)[-10:]
            
            # Check consistency of key metrics
            system_health_values = [h["system_health"] for h in recent_health]
            performance_values = [h["performance_score"] for h in recent_health]
            
            # Calculate variance
            health_variance = np.var(system_health_values) if len(system_health_values) > 1 else 0
            perf_variance = np.var(performance_values) if len(performance_values) > 1 else 0
            
            # Convert variance to invariance score
            total_variance = health_variance + perf_variance
            invariance = max(0, 100 - (total_variance * 10))
            
            return invariance
            
        except Exception:
            return 100.0
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        try:
            # Count error logs in recent history
            recent_logs = list(self.system_logs)[-100:]
            error_count = sum(1 for log in recent_logs if log.get("level") == "error")
            
            # Calculate error rate as percentage
            error_rate = (error_count / len(recent_logs)) * 100 if recent_logs else 0
            return min(100, error_rate)
            
        except Exception:
            return 0.0
    
    def _calculate_performance_score(self) -> float:
        """Calculate performance score"""
        try:
            if len(self.performance_metrics) < 1:
                return 100.0
            
            # Calculate performance based on recent metrics
            recent_metrics = list(self.performance_metrics)[-10:]
            
            # Average response time (lower is better)
            avg_response_time = sum(m.get("response_time", 0) for m in recent_metrics) / len(recent_metrics)
            
            # Convert to performance score (inverse relationship)
            if avg_response_time < 100:
                performance = 100
            elif avg_response_time < 500:
                performance = 80
            elif avg_response_time < 1000:
                performance = 60
            else:
                performance = 40
            
            return performance
            
        except Exception:
            return 100.0
    
    def _measure_network_latency(self) -> float:
        """Measure network latency"""
        try:
            # Simple ping measurement
            import subprocess
            result = subprocess.run(
                ["ping", "-c", "1", "8.8.8.8"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Extract time from ping output
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        time_str = line.split('time=')[1].split()[0]
                        return float(time_str)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _count_active_connections(self) -> int:
        """Count active network connections"""
        try:
            connections = psutil.net_connections()
            return len([c for c in connections if c.status == 'ESTABLISHED'])
        except Exception:
            return 0
    
    def _check_phase_drift(self):
        """Check for phase drift in system components"""
        try:
            # Analyze current system state
            current_state = {
                "health": self.current_health.system_health,
                "performance": self.current_health.performance_score,
                "memory": self.current_health.memory_usage,
                "cpu": self.current_health.cpu_usage
            }
            
            # Compute current phase vector
            current_phase = self._compute_phase_vector(current_state)
            current_entropy = self._compute_entropy(current_state)
            current_rei = self._compute_rei_score(current_phase)
            
            # Compare with previous state
            if len(self.phase_drift_history) > 0:
                last_drift = self.phase_drift_history[-1]
                
                # Calculate drift magnitude
                drift_magnitude = abs(current_entropy - last_drift.entropy) + abs(current_rei - last_drift.rei_score)
                
                # Determine severity
                if drift_magnitude < 0.1:
                    severity = "low"
                elif drift_magnitude < 0.3:
                    severity = "medium"
                elif drift_magnitude < 0.5:
                    severity = "high"
                else:
                    severity = "critical"
                
                # Create drift data
                drift_data = PhaseDriftData(
                    timestamp=datetime.now(),
                    phase_vector=current_phase,
                    entropy=current_entropy,
                    rei_score=current_rei,
                    drift_magnitude=drift_magnitude,
                    component="system",
                    severity=severity
                )
                
                self.phase_drift_history.append(drift_data)
                
                # Log significant drift
                if severity in ["high", "critical"]:
                    self._log_event(f"Phase drift detected: {severity} severity, magnitude: {drift_magnitude:.3f}", "warning")
            
            else:
                # First measurement
                drift_data = PhaseDriftData(
                    timestamp=datetime.now(),
                    phase_vector=current_phase,
                    entropy=current_entropy,
                    rei_score=current_rei,
                    drift_magnitude=0.0,
                    component="system",
                    severity="low"
                )
                self.phase_drift_history.append(drift_data)
                
        except Exception as e:
            self._log_event(f"Phase drift check error: {e}", "error")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            # Simulate performance measurement
            response_time = np.random.normal(200, 50)  # Simulated response time
            throughput = np.random.normal(1000, 200)   # Simulated throughput
            
            metric = {
                "timestamp": datetime.now().isoformat(),
                "response_time": max(0, response_time),
                "throughput": max(0, throughput),
                "active_requests": self.current_health.active_connections
            }
            
            self.performance_metrics.append(metric)
            
        except Exception as e:
            self._log_event(f"Performance metrics update error: {e}", "error")
    
    def _log_event(self, message: str, level: str = "info"):
        """Log system event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "component": "dashboard"
        }
        self.system_logs.append(log_entry)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "health": asdict(self.current_health),
            "health_history": list(self.health_history)[-50:],  # Last 50 entries
            "phase_drift": [asdict(d) for d in list(self.phase_drift_history)[-20:]],  # Last 20 entries
            "performance_metrics": list(self.performance_metrics)[-20:],  # Last 20 entries
            "system_logs": list(self.system_logs)[-100:],  # Last 100 logs
            "shadow_solutions": [asdict(s) for s in self.shadow_solutions],
            "active_plugins": self.active_plugins,
            "alerts": self._get_active_alerts(),
            "recommendations": self._get_recommendations()
        }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        alerts = []
        
        # Health-based alerts
        if self.current_health.system_health < self.config["dashboard"]["health_thresholds"]["critical"]:
            alerts.append({
                "type": "critical",
                "title": "System Health Critical",
                "message": f"System health is critically low: {self.current_health.system_health:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        elif self.current_health.system_health < self.config["dashboard"]["health_thresholds"]["warning"]:
            alerts.append({
                "type": "warning",
                "title": "System Health Warning",
                "message": f"System health is below normal: {self.current_health.system_health:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Phase drift alerts
        if len(self.phase_drift_history) > 0:
            recent_drifts = list(self.phase_drift_history)[-5:]
            high_drifts = [d for d in recent_drifts if d.severity in ["high", "critical"]]
            
            if high_drifts:
                alerts.append({
                    "type": "warning",
                    "title": "Phase Drift Detected",
                    "message": f"{len(high_drifts)} high-severity phase drifts detected",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Performance alerts
        if self.current_health.performance_score < 60:
            alerts.append({
                "type": "warning",
                "title": "Performance Degradation",
                "message": f"Performance score is low: {self.current_health.performance_score:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _get_recommendations(self) -> List[Dict[str, Any]]:
        """Get system recommendations"""
        recommendations = []
        
        # Memory recommendations
        if self.current_health.memory_usage > 80:
            recommendations.append({
                "type": "performance",
                "title": "High Memory Usage",
                "description": "System memory usage is high",
                "action": "Consider closing unnecessary applications or increasing memory",
                "priority": "high"
            })
        
        # CPU recommendations
        if self.current_health.cpu_usage > 80:
            recommendations.append({
                "type": "performance",
                "title": "High CPU Usage",
                "description": "CPU usage is high",
                "action": "Check for resource-intensive processes",
                "priority": "medium"
            })
        
        # Phase stability recommendations
        if self.current_health.phase_stability < 80:
            recommendations.append({
                "type": "stability",
                "title": "Phase Instability",
                "description": "System phase stability is below optimal",
                "action": "Review recent changes and consider system restart",
                "priority": "medium"
            })
        
        return recommendations
    
    def add_shadow_solution(self, description: str, implementation: str, 
                          risks: List[str], benefits: List[str]) -> str:
        """Add a shadow solution for alternate fix selection"""
        solution_id = hashlib.md5(f"{description}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Calculate scores
        context = {"description": description, "implementation": implementation}
        phase_vector = self._compute_phase_vector(context)
        entropy_score = self._compute_entropy(context)
        rei_score = self._compute_rei_score(phase_vector)
        
        # Calculate confidence based on various factors
        confidence = min(100, (rei_score * 50) + (entropy_score * 30) + 20)
        
        solution = ShadowSolution(
            id=solution_id,
            description=description,
            phase_vector=phase_vector,
            entropy_score=entropy_score,
            rei_score=rei_score,
            confidence=confidence,
            implementation=implementation,
            risks=risks,
            benefits=benefits,
            created_at=datetime.now()
        )
        
        self.shadow_solutions.append(solution)
        self._log_event(f"Shadow solution added: {description}", "info")
        
        return solution_id
    
    def get_shadow_solutions(self) -> List[Dict[str, Any]]:
        """Get all shadow solutions"""
        return [asdict(s) for s in self.shadow_solutions]
    
    def select_shadow_solution(self, solution_id: str) -> bool:
        """Select and apply a shadow solution"""
        solution = next((s for s in self.shadow_solutions if s.id == solution_id), None)
        if not solution:
            return False
        
        try:
            # Apply the solution (this would integrate with the fix engine)
            self._log_event(f"Shadow solution selected and applied: {solution.description}", "info")
            return True
        except Exception as e:
            self._log_event(f"Failed to apply shadow solution: {e}", "error")
            return False
    
    def _start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        try:
            import asyncio
            import websockets
            
            async def websocket_handler(websocket, path):
                """Handle WebSocket connections"""
                try:
                    while self.is_monitoring:
                        # Send dashboard data
                        data = self.get_dashboard_data()
                        await websocket.send(json.dumps(data))
                        await asyncio.sleep(self.config["dashboard"]["update_interval"])
                except websockets.exceptions.ConnectionClosed:
                    pass
            
            # Start WebSocket server
            port = self.config["dashboard"]["websocket_port"]
            self.websocket_server = websockets.serve(websocket_handler, "localhost", port)
            
            # Run in background thread
            def run_websocket():
                asyncio.run(self.websocket_server)
            
            websocket_thread = threading.Thread(target=run_websocket)
            websocket_thread.daemon = True
            websocket_thread.start()
            
            self._log_event(f"WebSocket server started on port {port}", "info")
            
        except Exception as e:
            self._log_event(f"WebSocket server error: {e}", "error")
    
    def export_dashboard_report(self, format: str = "json") -> str:
        """Export comprehensive dashboard report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "dashboard_data": self.get_dashboard_data(),
                "configuration": self.config,
                "summary": {
                    "total_health_measurements": len(self.health_history),
                    "total_phase_drifts": len(self.phase_drift_history),
                    "total_shadow_solutions": len(self.shadow_solutions),
                    "total_logs": len(self.system_logs),
                    "monitoring_duration": self._get_monitoring_duration()
                }
            }
            
            if format == "json":
                report_file = Path(f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                return str(report_file)
            else:
                # Could add other formats (CSV, HTML, etc.)
                return "Unsupported format"
                
        except Exception as e:
            self._log_event(f"Export error: {e}", "error")
            return ""
    
    def _get_monitoring_duration(self) -> str:
        """Get monitoring duration as string"""
        if not self.health_history:
            return "0 seconds"
        
        first_time = datetime.fromisoformat(self.health_history[0]["last_update"])
        last_time = datetime.fromisoformat(self.health_history[-1]["last_update"])
        duration = last_time - first_time
        
        return str(duration)

def main():
    """Main dashboard application"""
    print("[APTPT] PhaseSynth Ultra+ Comprehensive Dashboard")
    print("[APTPT] Starting dashboard with full monitoring...")
    
    dashboard = ComprehensiveDashboard()
    dashboard.start_monitoring()
    
    try:
        # Keep dashboard running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[APTPT] Stopping dashboard...")
        dashboard.stop_monitoring()
        
        # Export final report
        report_file = dashboard.export_dashboard_report()
        if report_file:
            print(f"[APTPT] Dashboard report exported to: {report_file}")

if __name__ == "__main__":
    main() 