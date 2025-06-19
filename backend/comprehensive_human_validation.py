#!/usr/bin/env python3
"""
PhaseSynth Ultra+ Comprehensive Human Validation Suite
Tests every feature as a human would interact with them
Applying APTPT, HCE, and REI theories for 10000% correctness
"""

import requests
import json
import time
import numpy as np
from typing import Dict, List, Any
import random
from datetime import datetime

class HumanValidationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Log test results with APTPT phase tracking"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"[{status}] {test_name}: {details} ({duration:.3f}s)")
        
    def test_health_check(self) -> bool:
        """Test 1: Human checks system health"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # APTPT validation: Check phase stability metrics
                phase_metrics = data.get("phase_metrics", {})
                entropy = phase_metrics.get("entropy", 1.0)
                stability = phase_metrics.get("stability", 0.0)
                confidence = phase_metrics.get("confidence", 0.0)
                
                # APTPT theory: Low entropy (< 0.1) and high stability (> 0.8) indicate healthy system
                is_healthy = (entropy < 0.1 and stability > 0.8 and confidence > 0.9)
                
                self.log_test("Health Check", is_healthy, 
                             f"Entropy: {entropy:.3f}, Stability: {stability:.3f}, Confidence: {confidence:.3f}", 
                             duration)
                return is_healthy
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            self.log_test("Health Check", False, str(e), time.time() - start_time)
            return False
    
    def test_dashboard_access(self) -> bool:
        """Test 2: Human accesses dashboard"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                # HCE validation: Check phase and entropy history
                has_aptpt = "aptpt" in data
                has_phase = "phase" in data
                has_entropy = "entropy" in data
                has_rei = "rei" in data
                
                self.log_test("Dashboard Access", all([has_aptpt, has_phase, has_entropy, has_rei]),
                             f"APTPT: {has_aptpt}, HCE: {has_phase}/{has_entropy}, REI: {has_rei}", duration)
                return all([has_aptpt, has_phase, has_entropy, has_rei])
            else:
                self.log_test("Dashboard Access", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            self.log_test("Dashboard Access", False, str(e), time.time() - start_time)
            return False
    
    def test_state_update_workflow(self) -> bool:
        """Test 3: Human updates system state using APTPT feedback"""
        start_time = time.time()
        try:
            # Simulate human providing current and target states
            current_state = [0.1, 0.2, 0.3, 0.4]
            target_state = [0.8, 0.9, 1.0, 0.7]
            
            payload = {
                "current_state": current_state,
                "target_state": target_state
            }
            
            response = self.session.post(f"{self.base_url}/update-state", 
                                       json=payload, 
                                       headers={"Content-Type": "application/json"})
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # APTPT validation: Check feedback response
                new_state = data.get("new_state", [])
                aptpt_metrics = data.get("aptpt_metrics", {})
                hce_metrics = data.get("hce_metrics", {})
                rei_valid = data.get("rei_valid", False)
                
                # APTPT theory: New state should be different from current (feedback applied)
                state_changed = len(new_state) == len(current_state) and new_state != current_state
                has_aptpt_metrics = "error" in aptpt_metrics and "gain" in aptpt_metrics
                has_hce_metrics = "phase" in hce_metrics and "entropy" in hce_metrics
                
                success = state_changed and has_aptpt_metrics and has_hce_metrics and rei_valid
                
                self.log_test("State Update Workflow", success,
                             f"State changed: {state_changed}, APTPT: {has_aptpt_metrics}, HCE: {has_hce_metrics}, REI: {rei_valid}", 
                             duration)
                return success
            else:
                self.log_test("State Update Workflow", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            self.log_test("State Update Workflow", False, str(e), time.time() - start_time)
            return False
    
    def test_sequence_analysis(self) -> bool:
        """Test 4: Human analyzes state sequence for theory compliance"""
        start_time = time.time()
        try:
            # Simulate human providing a sequence of states
            states = [
                [0.1, 0.2, 0.3],
                [0.2, 0.3, 0.4],
                [0.3, 0.4, 0.5],
                [0.4, 0.5, 0.6],
                [0.5, 0.6, 0.7]
            ]
            
            payload = {
                "states": states,
                "description": "Human-generated state sequence for analysis"
            }
            
            response = self.session.post(f"{self.base_url}/analyze-sequence", 
                                       json=payload, 
                                       headers={"Content-Type": "application/json"})
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # REI validation: Check transformation analysis
                aptpt_analysis = data.get("aptpt_analysis", {})
                hce_analysis = data.get("hce_analysis", {})
                rei_analysis = data.get("rei_analysis", {})
                
                has_aptpt = "success_rate" in aptpt_analysis
                has_hce = "phase_stability" in hce_analysis
                has_rei = "transformations" in rei_analysis
                
                success = has_aptpt and has_hce and has_rei
                
                self.log_test("Sequence Analysis", success,
                             f"APTPT: {has_aptpt}, HCE: {has_hce}, REI: {has_rei}", duration)
                return success
            else:
                self.log_test("Sequence Analysis", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            self.log_test("Sequence Analysis", False, str(e), time.time() - start_time)
            return False
    
    def test_phase_diagram_visualization(self) -> bool:
        """Test 5: Human views phase diagram for HCE analysis"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/phase-diagram")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # HCE validation: Check phase diagram data
                hce_diagram = data.get("hce_diagram", {})
                rei_diagram = data.get("rei_diagram", {})
                
                has_hce_phases = "phases" in hce_diagram
                has_hce_entropy = "entropy" in hce_diagram
                has_rei_history = "equivalence_history" in rei_diagram
                
                success = has_hce_phases and has_hce_entropy and has_rei_history
                
                self.log_test("Phase Diagram Visualization", success,
                             f"HCE phases: {has_hce_phases}, HCE entropy: {has_hce_entropy}, REI history: {has_rei_history}", 
                             duration)
                return success
            else:
                self.log_test("Phase Diagram Visualization", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            self.log_test("Phase Diagram Visualization", False, str(e), time.time() - start_time)
            return False
    
    def test_metrics_monitoring(self) -> bool:
        """Test 6: Human monitors system metrics"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/metrics")
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # System validation: Check performance metrics
                has_cpu = "cpu" in data
                has_memory = "memory" in data
                has_response_time = "responseTime" in data
                has_timestamp = "timestamp" in data
                
                success = all([has_cpu, has_memory, has_response_time, has_timestamp])
                
                self.log_test("Metrics Monitoring", success,
                             f"CPU: {has_cpu}, Memory: {has_memory}, Response: {has_response_time}, Timestamp: {has_timestamp}", 
                             duration)
                return success
            else:
                self.log_test("Metrics Monitoring", False, f"HTTP {response.status_code}", duration)
                return False
        except Exception as e:
            self.log_test("Metrics Monitoring", False, str(e), time.time() - start_time)
            return False
    
    def test_input_validation(self) -> bool:
        """Test 7: Human provides various inputs and validates responses"""
        start_time = time.time()
        test_cases = [
            ("normal_input", "Hello World", 200, True),
            ("large_input", "A" * 1001, 413, False),  # Too large
            ("malicious_input", "<script>alert('xss')</script>", 400, False),  # Malicious
            ("empty_input", "", 200, True),
        ]
        
        all_passed = True
        for test_name, input_data, expected_status, should_succeed in test_cases:
            try:
                payload = {"input": input_data}
                response = self.session.post(f"{self.base_url}/api/test-input", 
                                           json=payload, 
                                           headers={"Content-Type": "application/json"})
                
                if response.status_code == expected_status:
                    self.log_test(f"Input Validation - {test_name}", True, f"Status: {response.status_code}", 0)
                else:
                    self.log_test(f"Input Validation - {test_name}", False, 
                                 f"Expected {expected_status}, got {response.status_code}", 0)
                    all_passed = False
            except Exception as e:
                self.log_test(f"Input Validation - {test_name}", False, str(e), 0)
                all_passed = False
        
        duration = time.time() - start_time
        self.log_test("Input Validation Suite", all_passed, f"{len(test_cases)} test cases", duration)
        return all_passed
    
    def test_error_handling(self) -> bool:
        """Test 8: Human tests error handling and edge cases"""
        start_time = time.time()
        test_cases = [
            ("invalid_json", "invalid json", 422, "Invalid JSON"),
            ("missing_fields", '{"current_state": [1,2,3]}', 422, "Missing target_state"),
            ("wrong_types", '{"current_state": "not_array", "target_state": [1,2,3]}', 422, "Wrong types"),
            ("nonexistent_endpoint", "/nonexistent", 404, "Not found"),
        ]
        
        all_passed = True
        for test_name, payload, expected_status, description in test_cases:
            try:
                if test_name == "nonexistent_endpoint":
                    response = self.session.get(f"{self.base_url}{payload}")
                else:
                    response = self.session.post(f"{self.base_url}/update-state", 
                                               data=payload, 
                                               headers={"Content-Type": "application/json"})
                
                if response.status_code == expected_status:
                    self.log_test(f"Error Handling - {test_name}", True, description, 0)
                else:
                    self.log_test(f"Error Handling - {test_name}", False, 
                                 f"Expected {expected_status}, got {response.status_code}", 0)
                    all_passed = False
            except Exception as e:
                self.log_test(f"Error Handling - {test_name}", False, str(e), 0)
                all_passed = False
        
        duration = time.time() - start_time
        self.log_test("Error Handling Suite", all_passed, f"{len(test_cases)} test cases", duration)
        return all_passed
    
    def test_concurrent_operations(self) -> bool:
        """Test 9: Human performs concurrent operations"""
        start_time = time.time()
        try:
            import threading
            
            results = []
            def make_request():
                try:
                    response = self.session.get(f"{self.base_url}/health")
                    results.append(response.status_code == 200)
                except:
                    results.append(False)
            
            # Start 5 concurrent requests
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            duration = time.time() - start_time
            success_rate = sum(results) / len(results) if results else 0
            success = success_rate >= 0.8  # 80% success rate threshold
            
            self.log_test("Concurrent Operations", success,
                         f"Success rate: {success_rate:.1%} ({sum(results)}/{len(results)})", duration)
            return success
        except Exception as e:
            self.log_test("Concurrent Operations", False, str(e), time.time() - start_time)
            return False
    
    def test_theory_compliance_validation(self) -> bool:
        """Test 10: Human validates theory compliance across all operations"""
        start_time = time.time()
        try:
            # APTPT Theory Validation: Test adaptive feedback
            current = np.array([0.1, 0.2, 0.3])
            target = np.array([0.8, 0.9, 1.0])
            
            # Multiple iterations to test convergence
            states = []
            for i in range(5):
                payload = {
                    "current_state": current.tolist(),
                    "target_state": target.tolist()
                }
                response = self.session.post(f"{self.base_url}/update-state", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    new_state = np.array(data["new_state"])
                    states.append(new_state)
                    current = new_state  # Use new state as current for next iteration
            
            # APTPT theory: States should converge toward target
            if len(states) >= 2:
                initial_error = np.linalg.norm(np.array([0.1, 0.2, 0.3]) - target)
                final_error = np.linalg.norm(states[-1] - target)
                convergence_improvement = initial_error > final_error
            else:
                convergence_improvement = False
            
            # HCE Theory Validation: Check phase stability
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                phase_metrics = data.get("phase_metrics", {})
                entropy = phase_metrics.get("entropy", 1.0)
                stability = phase_metrics.get("stability", 0.0)
                hce_stable = entropy < 0.1 and stability > 0.8
            else:
                hce_stable = False
            
            # REI Theory Validation: Check invariance
            response = self.session.get(f"{self.base_url}/phase-diagram")
            if response.status_code == 200:
                data = response.json()
                rei_diagram = data.get("rei_diagram", {})
                has_equivalence = "equivalence_history" in rei_diagram
                rei_valid = has_equivalence
            else:
                rei_valid = False
            
            duration = time.time() - start_time
            all_theories_valid = convergence_improvement and hce_stable and rei_valid
            
            self.log_test("Theory Compliance Validation", all_theories_valid,
                         f"APTPT convergence: {convergence_improvement}, HCE stable: {hce_stable}, REI valid: {rei_valid}", 
                         duration)
            return all_theories_valid
        except Exception as e:
            self.log_test("Theory Compliance Validation", False, str(e), time.time() - start_time)
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all human validation tests"""
        print("🚀 PhaseSynth Ultra+ Comprehensive Human Validation Suite")
        print("🔍 Testing every feature as a human would interact with them")
        print("📊 Applying APTPT, HCE, and REI theories for 10000% correctness")
        print("=" * 80)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Dashboard Access", self.test_dashboard_access),
            ("State Update Workflow", self.test_state_update_workflow),
            ("Sequence Analysis", self.test_sequence_analysis),
            ("Phase Diagram Visualization", self.test_phase_diagram_visualization),
            ("Metrics Monitoring", self.test_metrics_monitoring),
            ("Input Validation", self.test_input_validation),
            ("Error Handling", self.test_error_handling),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Theory Compliance Validation", self.test_theory_compliance_validation),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ ERROR in {test_name}: {e}")
                results.append(False)
        
        # Calculate final statistics
        total_tests = len(results)
        passed_tests = sum(results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE HUMAN VALIDATION RESULTS")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {total_tests - passed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! PhaseSynth Ultra+ is ready for human use!")
        elif success_rate >= 80:
            print("✅ GOOD! PhaseSynth Ultra+ is mostly ready for human use.")
        elif success_rate >= 70:
            print("⚠️  ACCEPTABLE! Some issues need attention.")
        else:
            print("❌ NEEDS WORK! Significant issues must be addressed.")
        
        # Save detailed results
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }
        
        with open(f"human_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report

if __name__ == "__main__":
    tester = HumanValidationTester()
    results = tester.run_all_tests() 