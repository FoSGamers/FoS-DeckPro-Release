#!/usr/bin/env python3
"""
Build script for FoS-DeckPro
Creates standalone executables for different platforms
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def build_app():
    """Build the FoS-DeckPro application"""
    
    # Change to the FoS_DeckPro directory
    os.chdir('FoS_DeckPro')
    
    # Install PyInstaller if not already installed
    if not run_command([sys.executable, '-m', 'pip', 'install', 'pyinstaller']):
        return False
    
    # Build the application using the spec file
    if not run_command([sys.executable, '-m', 'PyInstaller', 'FoS-DeckPro.spec']):
        return False
    
    # Create distribution packages
    dist_dir = Path('dist')
    if dist_dir.exists():
        if platform.system() == 'Darwin':  # macOS
            # Create macOS app bundle
            app_path = dist_dir / 'FoS-DeckPro'
            if app_path.exists():
                zip_path = dist_dir / 'FoS-DeckPro-macOS.zip'
                if run_command(['zip', '-r', str(zip_path), str(app_path)], cwd=dist_dir):
                    print(f"✅ macOS app created: {zip_path}")
                    
        elif platform.system() == 'Windows':
            # Windows executable is already created
            exe_path = dist_dir / 'FoS-DeckPro.exe'
            if exe_path.exists():
                print(f"✅ Windows executable created: {exe_path}")
                
        elif platform.system() == 'Linux':
            # Linux executable is already created
            linux_path = dist_dir / 'FoS-DeckPro'
            if linux_path.exists():
                print(f"✅ Linux executable created: {linux_path}")
    
    print("🎉 Build completed successfully!")
    return True

if __name__ == '__main__':
    if build_app():
        print("✅ Build successful!")
        sys.exit(0)
    else:
        print("❌ Build failed!")
        sys.exit(1) 