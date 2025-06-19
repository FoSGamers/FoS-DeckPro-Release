"""
APTPT System Manager - Comprehensive System Orchestration
Uses APTPT theory and database tracking to ensure system stability
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import requests
from system_database import system_db, initialize_system_database

class APTPTSystemManager:
    """
    APTPT-powered system manager for orchestrating all components
    Implements phase-aware system control and convergence monitoring
    """
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.frontend_path = self.base_path / "cursor-extension"
        self.backend_path = self.base_path / "backend"
        self.dist_path = self.frontend_path / "dist"
        
        # Initialize database
        initialize_system_database()
        
        # System state tracking
        self.frontend_server = None
        self.backend_server = None
        self.system_status = {
            'frontend': 'stopped',
            'backend': 'stopped',
            'database': 'active',
            'aptpt_phase': 'unknown'
        }
    
    def check_system_health(self) -> Dict[str, Any]:
        """Check the health of all system components"""
        health_status = {
            'timestamp': time.time(),
            'components': {},
            'overall_status': 'unknown',
            'aptpt_phase': 'unknown'
        }
        
        # Check frontend
        try:
            response = requests.get('http://localhost:3000/', timeout=5)
            health_status['components']['frontend'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            health_status['components']['frontend'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check backend
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            health_status['components']['backend'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            health_status['components']['backend'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check database
        try:
            summary = system_db.get_system_summary()
            health_status['components']['database'] = {
                'status': 'healthy',
                'total_files': summary['total_files'],
                'convergence_ratio': summary['aptpt_convergence_ratio'],
                'phase': summary['aptpt_phase']
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Determine overall status
        healthy_components = sum(1 for comp in health_status['components'].values() 
                               if comp['status'] == 'healthy')
        total_components = len(health_status['components'])
        
        if healthy_components == total_components:
            health_status['overall_status'] = 'healthy'
            health_status['aptpt_phase'] = 'stable'
        elif healthy_components >= total_components * 0.7:
            health_status['overall_status'] = 'degraded'
            health_status['aptpt_phase'] = 'converging'
        else:
            health_status['overall_status'] = 'unhealthy'
            health_status['aptpt_phase'] = 'unstable'
        
        return health_status
    
    def start_frontend_server(self) -> bool:
        """Start the frontend server"""
        try:
            if not self.dist_path.exists():
                print("[APTPT] Building frontend...")
                self.build_frontend()
            
            # Start HTTP server
            cmd = f"cd {self.dist_path} && python3 -m http.server 3000"
            self.frontend_server = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(3)
            
            # Verify server is running
            try:
                response = requests.get('http://localhost:3000/', timeout=5)
                if response.status_code == 200:
                    print("[APTPT] Frontend server started successfully")
                    self.system_status['frontend'] = 'running'
                    return True
                else:
                    print(f"[APTPT] Frontend server returned status code: {response.status_code}")
                    return False
            except Exception as e:
                print(f"[APTPT] Frontend server failed to respond: {e}")
                return False
                
        except Exception as e:
            print(f"[APTPT] Failed to start frontend server: {e}")
            return False
    
    def start_backend_server(self) -> bool:
        """Start the backend server"""
        try:
            cmd = f"cd {self.backend_path} && python api_server.py"
            self.backend_server = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(3)
            
            # Verify server is running
            try:
                response = requests.get('http://localhost:8000/health', timeout=5)
                if response.status_code == 200:
                    print("[APTPT] Backend server started successfully")
                    self.system_status['backend'] = 'running'
                    return True
                else:
                    print(f"[APTPT] Backend server returned status code: {response.status_code}")
                    return False
            except Exception as e:
                print(f"[APTPT] Backend server failed to respond: {e}")
                return False
                
        except Exception as e:
            print(f"[APTPT] Failed to start backend server: {e}")
            return False
    
    def build_frontend(self) -> bool:
        """Build the frontend application"""
        try:
            print("[APTPT] Building frontend application...")
            
            # Check if package.json exists
            package_json = self.frontend_path / "package.json"
            if not package_json.exists():
                print("[APTPT] package.json not found, creating basic configuration...")
                self.create_basic_package_json()
            
            # Run build command
            cmd = f"cd {self.frontend_path} && npm run build"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[APTPT] Frontend build completed successfully")
                
                # Register build artifacts in database
                self.register_build_artifacts()
                
                return True
            else:
                print(f"[APTPT] Frontend build failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[APTPT] Failed to build frontend: {e}")
            return False
    
    def create_basic_package_json(self):
        """Create a basic package.json if it doesn't exist"""
        package_data = {
            "name": "phasesynth-ultra-plus",
            "version": "1.0.0",
            "description": "APTPT-powered Universal App Builder/Enhancer",
            "main": "src/webview/index.tsx",
            "scripts": {
                "build": "node scripts/build.js build",
                "dev": "node scripts/build.js dev",
                "test": "echo \"Error: no test specified\" && exit 1"
            },
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "axios": "^1.0.0"
            },
            "devDependencies": {
                "typescript": "^4.9.0",
                "webpack": "^5.0.0",
                "webpack-cli": "^5.0.0",
                "ts-loader": "^9.0.0",
                "html-webpack-plugin": "^5.0.0",
                "clean-webpack-plugin": "^4.0.0",
                "copy-webpack-plugin": "^11.0.0"
            }
        }
        
        package_json_path = self.frontend_path / "package.json"
        with open(package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        print("[APTPT] Created basic package.json")
    
    def register_build_artifacts(self):
        """Register build artifacts in the database"""
        artifacts = [
            ('main_bundle', self.dist_path / "main.bundle.js"),
            ('index_html', self.dist_path / "index.html"),
            ('vendor_bundle', self.dist_path / "885.bundle.js")
        ]
        
        for artifact_name, artifact_path in artifacts:
            if artifact_path.exists():
                system_db.register_build_artifact(
                    artifact_name, 
                    str(artifact_path), 
                    {'type': 'webpack_bundle', 'timestamp': time.time()}
                )
    
    def run_system_test(self) -> Dict[str, Any]:
        """Run comprehensive system test"""
        print("[APTPT] Running comprehensive system test...")
        
        test_results = {
            'timestamp': time.time(),
            'tests': {},
            'overall_result': 'unknown'
        }
        
        # Test 1: Database connectivity
        try:
            summary = system_db.get_system_summary()
            test_results['tests']['database'] = {
                'status': 'passed',
                'total_files': summary['total_files'],
                'convergence_ratio': summary['aptpt_convergence_ratio']
            }
        except Exception as e:
            test_results['tests']['database'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 2: Frontend accessibility
        try:
            response = requests.get('http://localhost:3000/', timeout=10)
            test_results['tests']['frontend'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'status_code': response.status_code,
                'content_length': len(response.content)
            }
        except Exception as e:
            test_results['tests']['frontend'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 3: Backend API
        try:
            response = requests.get('http://localhost:8000/health', timeout=10)
            test_results['tests']['backend'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['tests']['backend'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Test 4: API communication
        try:
            response = requests.get('http://localhost:8000/api/health', timeout=10)
            test_results['tests']['api_communication'] = {
                'status': 'passed' if response.status_code == 200 else 'failed',
                'status_code': response.status_code,
                'data': response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            test_results['tests']['api_communication'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        # Determine overall result
        passed_tests = sum(1 for test in test_results['tests'].values() 
                          if test['status'] == 'passed')
        total_tests = len(test_results['tests'])
        
        if passed_tests == total_tests:
            test_results['overall_result'] = 'passed'
        elif passed_tests >= total_tests * 0.7:
            test_results['overall_result'] = 'partial'
        else:
            test_results['overall_result'] = 'failed'
        
        print(f"[APTPT] System test completed: {test_results['overall_result']}")
        print(f"[APTPT] Tests passed: {passed_tests}/{total_tests}")
        
        return test_results
    
    def start_system(self) -> bool:
        """Start the complete system"""
        print("[APTPT] Starting complete system...")
        
        # Initialize database
        initialize_system_database()
        
        # Start backend
        if not self.start_backend_server():
            print("[APTPT] Failed to start backend server")
            return False
        
        # Start frontend
        if not self.start_frontend_server():
            print("[APTPT] Failed to start frontend server")
            return False
        
        # Wait for system to stabilize
        print("[APTPT] Waiting for system to stabilize...")
        time.sleep(5)
        
        # Run system test
        test_results = self.run_system_test()
        
        if test_results['overall_result'] == 'passed':
            print("[APTPT] System started successfully!")
            return True
        else:
            print("[APTPT] System started with issues")
            return False
    
    def stop_system(self):
        """Stop the complete system"""
        print("[APTPT] Stopping system...")
        
        if self.frontend_server:
            self.frontend_server.terminate()
            self.frontend_server = None
            self.system_status['frontend'] = 'stopped'
        
        if self.backend_server:
            self.backend_server.terminate()
            self.backend_server = None
            self.system_status['backend'] = 'stopped'
        
        print("[APTPT] System stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        health = self.check_system_health()
        summary = system_db.get_system_summary()
        
        return {
            'timestamp': time.time(),
            'system_status': self.system_status,
            'health_status': health,
            'database_summary': summary,
            'aptpt_phase': health['aptpt_phase']
        }

# Global system manager instance
system_manager = APTPTSystemManager()

def main():
    """Main function for system management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='APTPT System Manager')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'test', 'build'], 
                       help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        success = system_manager.start_system()
        sys.exit(0 if success else 1)
    
    elif args.action == 'stop':
        system_manager.stop_system()
    
    elif args.action == 'status':
        status = system_manager.get_system_status()
        print(json.dumps(status, indent=2))
    
    elif args.action == 'test':
        results = system_manager.run_system_test()
        print(json.dumps(results, indent=2))
    
    elif args.action == 'build':
        success = system_manager.build_frontend()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 