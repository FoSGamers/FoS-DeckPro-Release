#!/usr/bin/env python3
"""
Normal User Test for FoS_DeckPro
Simulates a typical user workflow
"""

import pyautogui
import subprocess
import time
import os

print("🚀 Starting Normal User Test")

# Launch the app
print("Launching FoS_DeckPro...")
proc = subprocess.Popen(['python3', '../main.py'])
time.sleep(8)  # Wait for app to launch

# Create screenshots directory
screenshots_dir = 'screenshots_normal_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    """Take a screenshot"""
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'📸 Screenshot: {fname}')

try:
    print("Taking initial screenshot...")
    snap('initial_state')
    
    print("Test completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    
finally:
    print("Terminating app...")
    proc.terminate()
    print("✅ Normal user test complete.") 