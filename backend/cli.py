import argparse
import sys
import time
from autonomous_daemon import AutonomousDaemon

def main():
    parser = argparse.ArgumentParser(description='PhaseSynth Ultra+ Autonomous Daemon')
    parser.add_argument('--config', type=str, default='config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--start', action='store_true',
                      help='Start the daemon')
    parser.add_argument('--stop', action='store_true',
                      help='Stop the daemon')
    parser.add_argument('--status', action='store_true',
                      help='Get daemon status')
    parser.add_argument('--plot', action='store_true',
                      help='Plot healing history')
    parser.add_argument('--duration', type=int, default=0,
                      help='Run duration in seconds (0 for indefinite)')
    
    args = parser.parse_args()
    
    daemon = AutonomousDaemon(args.config)
    
    if args.start:
        print("Starting PhaseSynth Ultra+ daemon...")
        daemon.start()
        
        if args.duration > 0:
            print(f"Running for {args.duration} seconds...")
            time.sleep(args.duration)
            daemon.stop()
            print("Daemon stopped.")
    
    elif args.stop:
        print("Stopping PhaseSynth Ultra+ daemon...")
        daemon.stop()
        print("Daemon stopped.")
    
    elif args.status:
        status = daemon.get_healing_status()
        print("\nPhaseSynth Ultra+ Status:")
        print(f"Running: {status['is_running']}")
        print(f"State History Length: {status['state_history_length']}")
        print("\nRecent Healing Actions:")
        for action in status['healing_actions']:
            print(f"- {action['type']}: {action['action']}")
        print("\nCurrent Metrics:")
        print(f"APTPT: gain={status['current_metrics']['aptpt']['gain']:.3f}, "
              f"noise={status['current_metrics']['aptpt']['noise']:.3f}")
        print(f"HCE: entropy_drift={status['current_metrics']['hce']['entropy_drift']:.3f}")
        print(f"REI: xi={status['current_metrics']['rei']['xi']:.3f}")
    
    elif args.plot:
        print("Plotting healing history...")
        daemon.plot_healing_history()
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main() 