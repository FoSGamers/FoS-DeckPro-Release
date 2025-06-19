#!/usr/bin/env python3
"""
Human-Mimicking GUI Tester for PhaseSynth Ultra+
Implements APTPT, HCE, and REI principles for automated testing
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
import psutil
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

class HumanMimickingTester:
    """APTPT-compliant human-mimicking GUI tester with automatic issue reporting"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.backend_url = "http://localhost:8000"
        self.screenshot_dir = Path("test_screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
        self.test_results = []
        self.issues_found = []
        
    async def setup_browser(self) -> Tuple[Browser, BrowserContext, Page]:
        """Setup browser with human-like settings"""
        playwright = await async_playwright().start()
        
        # Use Chromium with human-like settings
        browser = await playwright.chromium.launch(
            headless=False,  # Visible for debugging
            slow_mo=100,     # Human-like delays
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        # Create context with human-like viewport and user agent
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add human-like behavior
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        page = await context.new_page()
        return browser, context, page
    
    async def take_screenshot(self, page: Page, name: str, description: str = "") -> str:
        """Take screenshot with timestamp and description"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshot_dir / filename
        
        await page.screenshot(path=str(filepath), full_page=True)
        
        result = {
            "timestamp": timestamp,
            "filename": filename,
            "description": description,
            "filepath": str(filepath)
        }
        
        self.test_results.append({
            "type": "screenshot",
            "data": result
        })
        
        return str(filepath)
    
    async def human_click(self, page: Page, selector: str, description: str = "") -> bool:
        """Simulate human-like clicking with error handling"""
        try:
            # Wait for element to be visible and clickable
            await page.wait_for_selector(selector, timeout=10000)
            
            # Add human-like delay
            await page.wait_for_timeout(500 + (time.time() % 1000))
            
            # Click with human-like behavior
            await page.click(selector, delay=100)
            
            self.test_results.append({
                "type": "click",
                "selector": selector,
                "description": description,
                "success": True
            })
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to click {selector}: {str(e)}"
            self.issues_found.append({
                "type": "click_error",
                "selector": selector,
                "description": description,
                "error": str(e)
            })
            
            self.test_results.append({
                "type": "click",
                "selector": selector,
                "description": description,
                "success": False,
                "error": str(e)
            })
            
            return False
    
    async def human_type(self, page: Page, selector: str, text: str, description: str = "") -> bool:
        """Simulate human-like typing with delays"""
        try:
            await page.wait_for_selector(selector, timeout=10000)
            await page.click(selector)
            
            # Clear existing text
            await page.fill(selector, "")
            
            # Type with human-like delays
            for char in text:
                await page.type(selector, char, delay=50 + (time.time() % 100))
                await page.wait_for_timeout(10)
            
            self.test_results.append({
                "type": "type",
                "selector": selector,
                "text": text,
                "description": description,
                "success": True
            })
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to type in {selector}: {str(e)}"
            self.issues_found.append({
                "type": "type_error",
                "selector": selector,
                "text": text,
                "description": description,
                "error": str(e)
            })
            
            return False
    
    async def check_backend_health(self) -> bool:
        """Check if backend is healthy"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/health", timeout=10)
                return response.status_code == 200
        except Exception as e:
            self.issues_found.append({
                "type": "backend_health_error",
                "error": str(e)
            })
            return False
    
    async def check_frontend_health(self) -> bool:
        """Check if frontend is accessible"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, timeout=10)
                return response.status_code == 200
        except Exception as e:
            self.issues_found.append({
                "type": "frontend_health_error",
                "error": str(e)
            })
            return False
    
    async def test_home_page(self, page: Page) -> bool:
        """Test the home page functionality"""
        try:
            # Navigate to home page
            await page.goto(self.base_url)
            await page.wait_for_load_state("networkidle")
            
            # Take screenshot of home page
            await self.take_screenshot(page, "home_page", "Initial home page load")
            
            # Check for main heading
            heading = await page.query_selector("h1")
            if not heading:
                self.issues_found.append({
                    "type": "missing_heading",
                    "page": "home",
                    "description": "No h1 heading found on home page"
                })
                return False
            
            # Test navigation to testing page
            await self.human_click(page, "a[href='/testing']", "Navigate to testing page")
            await page.wait_for_load_state("networkidle")
            
            await self.take_screenshot(page, "testing_page", "Testing page after navigation")
            
            return True
            
        except Exception as e:
            self.issues_found.append({
                "type": "home_page_error",
                "error": str(e)
            })
            return False
    
    async def test_human_interface(self, page: Page) -> bool:
        """Test the human-mimicking interface"""
        try:
            # Navigate to testing page
            await page.goto(f"{self.base_url}/testing")
            await page.wait_for_load_state("networkidle")
            
            await self.take_screenshot(page, "human_interface_initial", "Human interface initial load")
            
            # Test form interactions
            await self.human_type(page, "input[name='testInput']", "Hello APTPT World!", "Type test input")
            await self.human_click(page, "button[type='submit']", "Submit test form")
            
            await page.wait_for_timeout(2000)  # Wait for response
            await self.take_screenshot(page, "human_interface_after_submit", "After form submission")
            
            # Test API calls
            await self.human_click(page, "button[data-testid='test-api']", "Test API endpoint")
            await page.wait_for_timeout(2000)
            
            await self.take_screenshot(page, "human_interface_api_test", "After API test")
            
            return True
            
        except Exception as e:
            self.issues_found.append({
                "type": "human_interface_error",
                "error": str(e)
            })
            return False
    
    async def test_health_page(self, page: Page) -> bool:
        """Test the health monitoring page"""
        try:
            await page.goto(f"{self.base_url}/health")
            await page.wait_for_load_state("networkidle")
            
            await self.take_screenshot(page, "health_page", "Health monitoring page")
            
            # Check for health metrics
            metrics = await page.query_selector("[data-testid='health-metrics']")
            if not metrics:
                self.issues_found.append({
                    "type": "missing_health_metrics",
                    "description": "Health metrics not found on health page"
                })
            
            return True
            
        except Exception as e:
            self.issues_found.append({
                "type": "health_page_error",
                "error": str(e)
            })
            return False
    
    async def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "issues_found": len(self.issues_found),
            "screenshots_taken": len([r for r in self.test_results if r["type"] == "screenshot"]),
            "test_results": self.test_results,
            "issues": self.issues_found,
            "summary": {
                "backend_healthy": await self.check_backend_health(),
                "frontend_healthy": await self.check_frontend_health(),
                "all_tests_passed": len(self.issues_found) == 0
            }
        }
        
        # Save report to file
        report_file = self.screenshot_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    async def run_full_test_suite(self) -> Dict:
        """Run complete human-mimicking test suite"""
        print("[APTPT] Starting human-mimicking GUI test suite...")
        
        browser, context, page = await self.setup_browser()
        
        try:
            # Check system health
            print("[APTPT] Checking system health...")
            backend_healthy = await self.check_backend_health()
            frontend_healthy = await self.check_frontend_health()
            
            if not backend_healthy:
                print("[REI] Backend health check failed - system may not be running")
                self.issues_found.append({
                    "type": "system_health",
                    "severity": "critical",
                    "message": "Backend is not responding"
                })
            
            if not frontend_healthy:
                print("[REI] Frontend health check failed")
                self.issues_found.append({
                    "type": "system_health",
                    "severity": "critical", 
                    "message": "Frontend is not accessible"
                })
            
            # Run GUI tests
            print("[APTPT] Testing home page...")
            await self.test_home_page(page)
            
            print("[APTPT] Testing human interface...")
            await self.test_human_interface(page)
            
            print("[APTPT] Testing health page...")
            await self.test_health_page(page)
            
            # Generate final report
            print("[APTPT] Generating test report...")
            report = await self.generate_report()
            
            return report
            
        finally:
            await browser.close()
    
    def print_summary(self, report: Dict):
        """Print human-readable test summary"""
        print("\n" + "="*60)
        print("APTPT HUMAN-MIMICKING TEST SUMMARY")
        print("="*60)
        
        summary = report["summary"]
        print(f"Backend Healthy: {'✅' if summary['backend_healthy'] else '❌'}")
        print(f"Frontend Healthy: {'✅' if summary['frontend_healthy'] else '❌'}")
        print(f"All Tests Passed: {'✅' if summary['all_tests_passed'] else '❌'}")
        print(f"Total Tests: {report['total_tests']}")
        print(f"Issues Found: {report['issues_found']}")
        print(f"Screenshots Taken: {report['screenshots_taken']}")
        
        if report["issues"]:
            print("\nISSUES DETECTED:")
            for issue in report["issues"]:
                print(f"  - {issue['type']}: {issue.get('error', issue.get('description', 'Unknown issue'))}")
        
        print(f"\nDetailed report saved to: {self.screenshot_dir}")
        print("="*60)

async def main():
    """Main test runner"""
    tester = HumanMimickingTester()
    report = await tester.run_full_test_suite()
    tester.print_summary(report)
    
    # Exit with error code if issues found
    if report["issues"]:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 