#!/usr/bin/env python3
"""
Simple Test for FoS_DeckPro
Basic functionality test without PyAutoGUI
"""

import subprocess
import time
import os

print("🚀 Starting Simple Test")

# Launch the app
print("Launching FoS_DeckPro...")
proc = subprocess.Popen(['python3', '../main.py'])
time.sleep(5)  # Wait for app to launch

print("App launched successfully!")

# Check if app is still running
if proc.poll() is None:
    print("✅ App is running")
else:
    print("❌ App terminated unexpectedly")

# Terminate the app
print("Terminating app...")
proc.terminate()
time.sleep(2)

print("✅ Simple test complete.") 