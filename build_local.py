#!/usr/bin/env python3
"""
Local build script for FoS DeckPro
Run this to test the PyInstaller build locally before pushing to GitHub Actions
"""

import os
import sys
import subprocess
import platform

def main():
    print("Building FoS DeckPro executable...")
    
    # Install PyInstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    print("Running PyInstaller...")
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller", "FoS-DeckPro.spec"
    ], check=True)
    
    if result.returncode == 0:
        print("✅ Build successful!")
        print(f"Executable created in: {os.path.join('dist', 'FoS-DeckPro')}")
        
        # Make executable on Unix systems
        if platform.system() != "Windows":
            exe_path = os.path.join("dist", "FoS-DeckPro")
            os.chmod(exe_path, 0o755)
            print(f"Made executable: {exe_path}")
    else:
        print("❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
