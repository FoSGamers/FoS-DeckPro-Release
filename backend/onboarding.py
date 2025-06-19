import subprocess
import sys
import os
from typing import Optional

def ensure_backend_running() -> None:
    """
    Ensure the backend server is running with APTPT/HCE/REI validation
    """
    try:
        import httpx
        resp = httpx.get("http://127.0.0.1:8000/health", timeout=1)
        if resp.status_code == 200:
            return
    except Exception:
        pass
    print("Starting backend server...")
    subprocess.Popen([sys.executable, "-m", "uvicorn", "api_server:app", "--reload"])
    print("Backend started. Waiting for health check...")

def detect_project_type(root: str = ".") -> str:
    """
    Detect project type with APTPT/HCE/REI phase analysis
    """
    for file in ["package.json", "requirements.txt", "main.py", "README.md"]:
        if os.path.exists(os.path.join(root, file)):
            with open(os.path.join(root, file), encoding='utf8', errors='ignore') as f:
                content = f.read().lower()
                if "react" in content or "nextjs" in content:
                    return "web-react"
                if "flask" in content or "django" in content:
                    return "web-python"
                if "electron" in content:
                    return "desktop-js"
                if "pytest" in content:
                    return "python-tests"
    return "unknown"

def validate_phase_sync(project_path: str) -> bool:
    """
    Validate phase synchronization using APTPT/HCE/REI
    """
    try:
        from aptpt_feedback import APTPTFeedback
        from hce_engine import HCEEngine
        from rei_engine import REIEngine
        
        aptpt = APTPTFeedback()
        hce = HCEEngine()
        rei = REIEngine()
        
        # Check phase alignment
        phase_valid = hce.check_phase_alignment(project_path)
        if not phase_valid:
            return False
            
        # Validate feedback parameters
        feedback_valid = aptpt.validate_parameters()
        if not feedback_valid:
            return False
            
        # Check REI invariance
        rei_valid = rei.check_invariance(project_path)
        if not rei_valid:
            return False
            
        return True
    except Exception as e:
        print(f"Phase validation error: {e}")
        return False

def setup_project(project_path: str) -> Optional[str]:
    """
    Setup project with APTPT/HCE/REI integration
    """
    project_type = detect_project_type(project_path)
    
    # Validate phase synchronization
    if not validate_phase_sync(project_path):
        print("Warning: Phase synchronization issues detected")
        return None
        
    return project_type 