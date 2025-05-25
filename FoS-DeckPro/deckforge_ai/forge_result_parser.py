# forge_result_parser.py

import os
import time
from typing import List, Dict
from deck_learning_engine import update_win_stats

# This parser assumes Forge logs to a result file (stdout redirected or written by Forge)
# Modify path below to wherever Forge writes simulation outcomes
FORGE_LOG_PATH = "forge_simulation_result.txt"

# Check for a win/loss indicator in Forge's output

def parse_forge_result_log(deck: List[Dict], log_path: str = FORGE_LOG_PATH):
    if not os.path.exists(log_path):
        print(f"[Forge Parser] No log file found at {log_path}")
        return

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read().lower()

    if "player wins" in content or "you win" in content:
        update_win_stats(deck, won=True)
        print("[Forge Parser] Win detected. Stats updated.")
    elif "opponent wins" in content or "you lose" in content:
        update_win_stats(deck, won=False)
        print("[Forge Parser] Loss detected. Stats updated.")
    else:
        print("[Forge Parser] No clear outcome found in log.")

# Optional: polling function to auto-run after Forge simulation

def wait_and_parse_forge_output(deck: List[Dict], log_path: str = FORGE_LOG_PATH, timeout: int = 20):
    print("[Forge Parser] Waiting for Forge to write results...")
    waited = 0
    while waited < timeout:
        if os.path.exists(log_path):
            time.sleep(2)
            parse_forge_result_log(deck, log_path)
            return
        time.sleep(2)
        waited += 2
    print("[Forge Parser] Timeout waiting for Forge output.")
