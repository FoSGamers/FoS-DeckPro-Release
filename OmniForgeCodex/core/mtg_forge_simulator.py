from PySide6.QtCore import QObject, Signal
import subprocess
import os
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config import Config

class MTGForgeSimulator(QObject):
    progress = Signal(str)
    simulation_complete = Signal(dict)
    simulation_error = Signal(str)

    def __init__(self):
        super().__init__()
        self.forge_path = Config.FORGE_EXECUTABLE
        self.user_data = Config.FORGE_USER_DATA
        self.simulation_timeout = 300  # 5 minutes
        self.result_cache = {}
        self.cache_expiry = 3600  # 1 hour
        self.max_retries = 3
        self._setup_error_handling()
        self._load_cache()

    def _setup_error_handling(self):
        self.error_handlers = {
            'timeout': self._handle_timeout,
            'process_error': self._handle_process_error,
            'log_error': self._handle_log_error,
            'validation_error': self._handle_validation_error,
            'cache_error': self._handle_cache_error,
            'configuration_error': self._handle_configuration_error
        }

    def _load_cache(self):
        """Load simulation results cache from disk"""
        cache_file = os.path.join(self.user_data, "simulation_cache.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    if self._validate_cache_data(data):
                        self.result_cache = data['results']
                        self._clean_expired_cache()
        except Exception as e:
            self.error_handlers['cache_error'](e)

    def _save_cache(self):
        """Save simulation results cache to disk"""
        cache_file = os.path.join(self.user_data, "simulation_cache.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': self.result_cache
                }, f)
        except Exception as e:
            self.error_handlers['cache_error'](e)

    def _validate_cache_data(self, data: dict) -> bool:
        """Validate cache data structure"""
        required_fields = {'timestamp', 'results'}
        return all(field in data for field in required_fields)

    def _clean_expired_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        self.result_cache = {
            key: value for key, value in self.result_cache.items()
            if current_time - value['timestamp'] < self.cache_expiry
        }

    def _generate_cache_key(self, deck_path: str, opponent_paths: list, game_format: str) -> str:
        """Generate a unique cache key for simulation results"""
        key_data = f"{deck_path}:{','.join(opponent_paths)}:{game_format}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def run_batch_simulations(self, deck_to_test_dck_path: str, opponent_deck_dck_paths: list, 
                            game_format: str, num_runs: int) -> List[Dict]:
        """Run multiple simulations and aggregate results"""
        results = []
        cache_key = self._generate_cache_key(deck_to_test_dck_path, opponent_deck_dck_paths, game_format)
        
        # Check cache
        if cache_key in self.result_cache:
            cached_data = self.result_cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_expiry:
                return cached_data['results']

        # Run simulations
        successful_runs = 0
        for i in range(num_runs):
            self.progress.emit(f"Running simulation {i+1}/{num_runs}")
            
            for retry in range(self.max_retries):
                try:
                    result = self._run_single_simulation(deck_to_test_dck_path, opponent_deck_dck_paths[0])
                    if result:
                        results.append(result)
                        successful_runs += 1
                        break
                except Exception as e:
                    if retry == self.max_retries - 1:
                        self.simulation_error.emit(f"Failed to run simulation after {self.max_retries} attempts")
                    time.sleep(1)  # Wait before retry

        # Cache results
        if results:
            self.result_cache[cache_key] = {
                'timestamp': time.time(),
                'results': results
            }
            self._save_cache()

        # Emit completion signal
        self.simulation_complete.emit({
            'total_runs': num_runs,
            'successful_runs': successful_runs,
            'results': results
        })

        return results

    def _run_single_simulation(self, deck_path: str, opponent_path: str) -> Optional[Dict]:
        """Run a single simulation with error handling and validation"""
        try:
            # Validate paths
            if not self._validate_deck_paths(deck_path, opponent_path):
                return None

            # Run simulation
            process = subprocess.Popen(
                [self.forge_path, "--ai", "--deck", deck_path, "--opponent", opponent_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.simulation_timeout)
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, process.args)
                    
                log_data = self.parse_forge_log()
                return self._validate_simulation_result(log_data)
            except subprocess.TimeoutExpired:
                process.kill()
                self.error_handlers['timeout']()
                return None
                
        except Exception as e:
            self.error_handlers['process_error'](e)
            return None

    def _validate_deck_paths(self, deck_path: str, opponent_path: str) -> bool:
        """Validate deck file paths"""
        if not os.path.exists(deck_path):
            self.error_handlers['configuration_error'](f"Deck file not found: {deck_path}")
            return False
        if not os.path.exists(opponent_path):
            self.error_handlers['configuration_error'](f"Opponent deck file not found: {opponent_path}")
            return False
        return True

    def parse_forge_log(self) -> Dict:
        """Parse Forge log file with enhanced error handling"""
        log_path = os.path.join(self.user_data, "forge.log")
        try:
            if not os.path.exists(log_path):
                raise FileNotFoundError(f"Log file not found: {log_path}")

            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Parse game events
            events = self._parse_game_events(lines)
            
            # Calculate metrics
            metrics = self._calculate_game_metrics(events)

            return {
                "win": events.get("win", False),
                "turns": events.get("turns", 0),
                "cards_played": events.get("cards_played", []),
                "events": events,
                "metrics": metrics
            }
        except Exception as e:
            self.error_handlers['log_error'](e)
            return {}

    def _parse_game_events(self, lines: List[str]) -> Dict:
        """Parse game events from log lines"""
        events = {
            "win": False,
            "turns": 0,
            "cards_played": [],
            "life_changes": [],
            "mana_used": [],
            "combat_damage": []
        }

        for line in lines:
            if "Player 1 wins" in line:
                events["win"] = True
            elif "Turn" in line:
                events["turns"] += 1
            elif "casts" in line:
                card_name = line.split("casts")[1].strip()
                events["cards_played"].append(card_name)
            elif "life" in line.lower():
                events["life_changes"].append(line.strip())
            elif "mana" in line.lower():
                events["mana_used"].append(line.strip())
            elif "combat" in line.lower():
                events["combat_damage"].append(line.strip())

        return events

    def _calculate_game_metrics(self, events: Dict) -> Dict:
        """Calculate game performance metrics"""
        return {
            "win_rate": 1.0 if events.get("win", False) else 0.0,
            "turns_to_win": events.get("turns", 0),
            "cards_played_count": len(events.get("cards_played", [])),
            "life_changes": len(events.get("life_changes", [])),
            "mana_used_count": len(events.get("mana_used", [])),
            "combat_damage_count": len(events.get("combat_damage", []))
        }

    def _handle_timeout(self):
        """Handle simulation timeout"""
        self.progress.emit("Simulation timed out")
        self.simulation_error.emit("Simulation exceeded maximum time limit")

    def _handle_process_error(self, error):
        """Handle process execution errors"""
        self.progress.emit(f"Simulation process error: {error}")
        self.simulation_error.emit(f"Failed to execute simulation: {error}")

    def _handle_log_error(self, error):
        """Handle log parsing errors"""
        self.progress.emit(f"Error parsing simulation log: {error}")
        self.simulation_error.emit(f"Failed to parse simulation log: {error}")

    def _handle_validation_error(self):
        """Handle result validation errors"""
        self.progress.emit("Invalid simulation result")
        self.simulation_error.emit("Simulation produced invalid results")

    def _handle_cache_error(self, error):
        """Handle cache operation errors"""
        self.progress.emit(f"Cache operation error: {error}")
        self.simulation_error.emit(f"Failed to manage simulation cache: {error}")

    def _handle_configuration_error(self, error):
        """Handle configuration errors"""
        self.progress.emit(f"Configuration error: {error}")
        self.simulation_error.emit(f"Invalid simulation configuration: {error}")

    def _validate_simulation_result(self, result: dict) -> dict:
        required_fields = {'win', 'turns', 'cards_played'}
        if not all(field in result for field in required_fields):
            self.error_handlers['validation_error']()
            return None
        return result
