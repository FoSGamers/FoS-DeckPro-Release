#!/usr/bin/env python3
"""
Automated Test Monitor for PhaseSynth Ultra+
Continuously runs human-mimicking tests and reports issues
"""

import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from human_mimicking_tester import HumanMimickingTester

class AutomatedTestMonitor:
    """Continuous test monitoring with APTPT/REI/HCE compliance"""
    
    def __init__(self, test_interval: int = 300):  # 5 minutes default
        self.test_interval = test_interval
        self.running = True
        self.test_history = []
        self.issue_history = []
        self.monitor_start_time = datetime.now()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n[APTPT] Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def run_single_test_cycle(self) -> Dict:
        """Run one complete test cycle"""
        print(f"\n[APTPT] Starting test cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            tester = HumanMimickingTester()
            report = await tester.run_full_test_suite()
            
            # Store in history
            self.test_history.append({
                "timestamp": datetime.now().isoformat(),
                "report": report
            })
            
            # Track issues
            if report["issues"]:
                self.issue_history.extend(report["issues"])
                await self.report_issues_to_chat(report["issues"])
            
            return report
            
        except Exception as e:
            error_report = {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "type": "test_cycle_error"
            }
            self.issue_history.append(error_report)
            await self.report_issues_to_chat([error_report])
            return {"error": str(e)}
    
    async def report_issues_to_chat(self, issues: List[Dict]):
        """Report issues back through the chat system"""
        print("\n" + "="*60)
        print("🚨 ISSUES DETECTED - REPORTING TO CHAT SYSTEM")
        print("="*60)
        
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            error_msg = issue.get("error", issue.get("description", "Unknown issue"))
            
            print(f"ISSUE TYPE: {issue_type}")
            print(f"ERROR: {error_msg}")
            
            # Generate actionable message for chat
            if issue_type == "backend_health_error":
                print("ACTION REQUIRED: Backend server is not responding")
                print("SUGGESTED FIX: Check if backend is running on port 8000")
                
            elif issue_type == "frontend_health_error":
                print("ACTION REQUIRED: Frontend is not accessible")
                print("SUGGESTED FIX: Check if frontend is running on port 3000")
                
            elif issue_type == "click_error":
                print("ACTION REQUIRED: UI element not clickable")
                print(f"ELEMENT: {issue.get('selector', 'Unknown')}")
                print("SUGGESTED FIX: Check if element exists and is visible")
                
            elif issue_type == "type_error":
                print("ACTION REQUIRED: Input field not accessible")
                print(f"FIELD: {issue.get('selector', 'Unknown')}")
                print("SUGGESTED FIX: Check if input field exists and is enabled")
                
            elif issue_type == "missing_heading":
                print("ACTION REQUIRED: Page structure issue")
                print("SUGGESTED FIX: Check if page is loading correctly")
                
            else:
                print("ACTION REQUIRED: General system issue detected")
                print("SUGGESTED FIX: Review system logs and restart services")
            
            print("-" * 40)
        
        print("="*60)
        print("📋 These issues have been automatically detected by the APTPT test suite")
        print("🔧 The system will attempt to continue monitoring while issues are resolved")
        print("="*60)
    
    async def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        uptime = datetime.now() - self.monitor_start_time
        
        report = {
            "monitor_start_time": self.monitor_start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds(),
            "total_test_cycles": len(self.test_history),
            "total_issues_found": len(self.issue_history),
            "test_interval_seconds": self.test_interval,
            "recent_tests": self.test_history[-5:] if self.test_history else [],
            "recent_issues": self.issue_history[-10:] if self.issue_history else [],
            "system_status": {
                "monitoring_active": self.running,
                "last_test_time": self.test_history[-1]["timestamp"] if self.test_history else None
            }
        }
        
        # Save monitoring report
        report_file = Path("monitoring_report.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        print("[APTPT] Starting automated test monitoring...")
        print(f"[APTPT] Test interval: {self.test_interval} seconds")
        print(f"[APTPT] Monitor start time: {self.monitor_start_time}")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                print(f"\n[APTPT] Test cycle #{cycle_count}")
                
                # Run test cycle
                report = await self.run_single_test_cycle()
                
                # Print summary
                if "error" not in report:
                    summary = report.get("summary", {})
                    print(f"[APTPT] Cycle #{cycle_count} Summary:")
                    print(f"  Backend: {'✅' if summary.get('backend_healthy') else '❌'}")
                    print(f"  Frontend: {'✅' if summary.get('frontend_healthy') else '❌'}")
                    print(f"  Issues: {report.get('issues_found', 0)}")
                
                # Wait for next cycle
                if self.running:
                    print(f"[APTPT] Waiting {self.test_interval} seconds until next test cycle...")
                    await asyncio.sleep(self.test_interval)
                
            except KeyboardInterrupt:
                print("\n[APTPT] Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                print(f"[REI] Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        # Generate final report
        print("\n[APTPT] Generating final monitoring report...")
        final_report = await self.generate_monitoring_report()
        
        print(f"\n[APTPT] Monitoring completed:")
        print(f"  Total cycles: {final_report['total_test_cycles']}")
        print(f"  Total issues: {final_report['total_issues_found']}")
        print(f"  Uptime: {final_report['uptime_seconds']:.1f} seconds")
        print(f"  Report saved to: monitoring_report.json")

async def main():
    """Main monitoring entry point"""
    # Parse command line arguments
    test_interval = 300  # 5 minutes default
    
    if len(sys.argv) > 1:
        try:
            test_interval = int(sys.argv[1])
        except ValueError:
            print("Usage: python automated_test_monitor.py [test_interval_seconds]")
            sys.exit(1)
    
    monitor = AutomatedTestMonitor(test_interval)
    await monitor.run_continuous_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 