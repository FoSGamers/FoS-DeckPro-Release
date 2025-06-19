import subprocess
import os
import glob
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(__file__))

from vision_analyzer import VisionAnalyzer

persona_scripts = [
    'test_normal_user.py',
    'test_dumb_user.py',
    'test_breaker_user.py',
    'test_power_user.py',
    'test_accessibility_user.py',
    'test_curiosity_user.py',
    'test_regression_user.py',
]

persona_names = [
    'normal_user',
    'dumb_user', 
    'breaker_user',
    'power_user',
    'accessibility_user',
    'curiosity_user',
    'regression_user',
]

def run_persona_tests():
    """Run all persona test scripts"""
    print("🚀 Starting FoS_DeckPro Human-Like GUI Testing Suite")
    print("=" * 60)
    
    results = []
    
    for script in persona_scripts:
        print(f'\n=== Running {script} ===')
        try:
            proc = subprocess.run(['python3', script], cwd=os.path.dirname(__file__), 
                                capture_output=True, text=True, timeout=300)
            results.append((script, proc.returncode, proc.stdout, proc.stderr))
            print(f"Exit code: {proc.returncode}")
            if proc.stdout:
                print("Output:", proc.stdout)
            if proc.stderr:
                print("Errors:", proc.stderr)
        except subprocess.TimeoutExpired:
            print(f"❌ {script} timed out after 5 minutes")
            results.append((script, -1, "", "Timeout"))
        except Exception as e:
            print(f"❌ {script} failed: {e}")
            results.append((script, -1, "", str(e)))
    
    return results

def analyze_screenshots_with_vision():
    """Analyze all screenshots using OpenAI Vision"""
    print("\n🔍 Starting OpenAI Vision Analysis")
    print("=" * 40)
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OpenAI API key not found. Skipping vision analysis.")
        print("To enable vision analysis, set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return None
    
    try:
        # Initialize vision analyzer
        analyzer = VisionAnalyzer()
        
        # Analyze screenshots for each persona
        all_results = []
        for persona_name in persona_names:
            print(f"\n--- Analyzing {persona_name} screenshots ---")
            results = analyzer.analyze_persona_screenshots(persona_name, ".")
            all_results.extend(results)
        
        # Save reports
        report_file = analyzer.save_report()
        results_file = analyzer.save_raw_results()
        
        print(f"\n✅ Vision analysis complete!")
        print(f"📄 Report: {report_file}")
        print(f"📊 Raw results: {results_file}")
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Vision analysis failed: {e}")
        return None

def generate_final_report(test_results, vision_analyzer=None):
    """Generate a comprehensive final report"""
    print("\n📋 Generating Final Report")
    print("=" * 30)
    
    # Count screenshots
    all_screenshots = []
    for folder in glob.glob('screenshots_*'):
        for img in glob.glob(os.path.join(folder, '*.png')):
            all_screenshots.append(img)
    
    # Generate report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"comprehensive_test_report_{timestamp}.md"
    
    with open(report_filename, 'w') as f:
        f.write(f"# FoS_DeckPro Comprehensive GUI Test Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Test Summary\n")
        f.write(f"- Total persona tests: {len(test_results)}\n")
        f.write(f"- Successful tests: {len([r for r in test_results if r[1] == 0])}\n")
        f.write(f"- Failed tests: {len([r for r in test_results if r[1] != 0])}\n")
        f.write(f"- Total screenshots: {len(all_screenshots)}\n")
        f.write(f"- Vision analysis: {'✅ Completed' if vision_analyzer else '❌ Skipped'}\n\n")
        
        f.write("## Test Results\n")
        for script, code, stdout, stderr in test_results:
            status = "✅ PASS" if code == 0 else "❌ FAIL"
            f.write(f"- {status} {script} (exit code: {code})\n")
            if stderr:
                f.write(f"  Error: {stderr}\n")
        
        f.write("\n## Screenshots\n")
        for screenshot in sorted(all_screenshots):
            f.write(f"- {screenshot}\n")
        
        if vision_analyzer:
            f.write("\n## Vision Analysis\n")
            f.write("OpenAI Vision analysis was performed on all screenshots.\n")
            f.write("See the detailed vision analysis report for UI/UX feedback.\n")
    
    print(f"📄 Final report saved: {report_filename}")
    return report_filename

def main():
    """Main test runner"""
    # Run all persona tests
    test_results = run_persona_tests()
    
    # Print test summary
    print(f"\n=== TEST SUMMARY ===")
    for script, code, stdout, stderr in test_results:
        status = '✅' if code == 0 else '❌'
        print(f'{status} {script} (exit code {code})')
    
    # Count screenshots
    all_screenshots = []
    for folder in glob.glob('screenshots_*'):
        for img in glob.glob(os.path.join(folder, '*.png')):
            all_screenshots.append(img)
    
    print(f'\nTotal screenshots taken: {len(all_screenshots)}')
    for img in sorted(all_screenshots):
        print(f'  {img}')
    
    # Run vision analysis
    vision_analyzer = analyze_screenshots_with_vision()
    
    # Generate final report
    final_report = generate_final_report(test_results, vision_analyzer)
    
    print(f"\n🎉 Comprehensive testing completed!")
    print(f"📊 Success Rate: {(len([r for r in test_results if r[1] == 0])/len(test_results)*100):.1f}%")
    print(f"📸 Screenshots: {len(all_screenshots)} taken")
    print(f"📄 Final Report: {final_report}")
    
    if vision_analyzer:
        print(f"🤖 Vision Analysis: Completed with detailed UI/UX feedback")
    else:
        print(f"🤖 Vision Analysis: Skipped (no API key)")

if __name__ == "__main__":
    from datetime import datetime
    main() 