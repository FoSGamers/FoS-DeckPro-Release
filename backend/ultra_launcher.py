from onboarding import ensure_backend_running, detect_project_type, validate_phase_sync
from aptpt_feedback import APTPTFeedback
from hce_engine import HCEEngine
from rei_engine import REIEngine
from visualizer import PhaseSynthVisualizer
import os
import sys

class UltraLauncher:
    def __init__(self):
        self.aptpt = APTPTFeedback()
        self.hce = HCEEngine()
        self.rei = REIEngine()
        self.visualizer = PhaseSynthVisualizer()
        
    def launch(self, project_path: str = None) -> bool:
        """
        Launch PhaseSynth Ultra+ with APTPT/HCE/REI validation
        """
        try:
            # Ensure backend is running
            ensure_backend_running()
            
            # Detect project type
            if project_path:
                project_type = detect_project_type(project_path)
                print(f"Detected project type: {project_type}")
                
                # Validate phase synchronization
                if not validate_phase_sync(project_path):
                    print("Warning: Phase synchronization issues detected")
                    return False
            
            # Initialize APTPT feedback
            self.aptpt.initialize()
            
            # Start HCE phase tracking
            self.hce.start_phase_tracking()
            
            # Initialize REI invariance
            self.rei.initialize()
            
            # Start visualization
            self.visualizer.start()
            
            return True
            
        except Exception as e:
            print(f"Launch error: {e}")
            return False
    
    def shutdown(self):
        """
        Graceful shutdown with APTPT/HCE/REI cleanup
        """
        try:
            # Stop phase tracking
            self.hce.stop_phase_tracking()
            
            # Save final state
            self.aptpt.save_state()
            self.rei.save_state()
            
            # Stop visualization
            self.visualizer.stop()
            
        except Exception as e:
            print(f"Shutdown error: {e}")

def main():
    launcher = UltraLauncher()
    
    # Get project path from command line or use current directory
    project_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    if launcher.launch(project_path):
        print("PhaseSynth Ultra+ launched successfully")
        
        try:
            # Keep running until interrupted
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            launcher.shutdown()
    else:
        print("Launch failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 