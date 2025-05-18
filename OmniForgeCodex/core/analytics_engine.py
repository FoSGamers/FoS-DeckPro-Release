from typing import Dict, List, Optional, Any, Union, Callable, Tuple
import numpy as np
from datetime import datetime, timedelta
import json
import os
import pandas as pd
from pathlib import Path
import logging
from config import Config

class AnalyticsEngine:
    def __init__(self) -> None:
        self.history_file: str = os.path.join(Config.RESOURCES_DIR, "analytics_history.json")
        self.backup_dir: str = os.path.join(Config.RESOURCES_DIR, "analytics_backups")
        self.version: str = "1.0"
        self.history: Dict[str, Any] = self._load_history()
        self._setup_data_management()
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Setup logging for analytics operations"""
        self.logger: logging.Logger = logging.getLogger("AnalyticsEngine")
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        file_handler: logging.FileHandler = logging.FileHandler(
            os.path.join(Config.RESOURCES_DIR, "analytics.log")
        )
        console_handler: logging.StreamHandler = logging.StreamHandler()
        
        # Create formatters
        formatter: logging.Formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def _setup_data_management(self) -> None:
        """Setup data management handlers"""
        self.data_handlers: Dict[str, Callable] = {
            'persistence': self._handle_persistence,
            'backup': self._handle_backup,
            'versioning': self._handle_versioning,
            'migration': self._handle_migration,
            'cleanup': self._handle_cleanup,
            'export': self._handle_export,
            'validation': self._handle_validation
        }
        
    def _load_history(self) -> Dict[str, Any]:
        """Load analytics history with validation and error handling"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data: Dict[str, Any] = json.load(f)
                    if self._validate_history_data(data):
                        self.logger.info("Successfully loaded analytics history")
                        return data
                    else:
                        self.logger.warning("Invalid history data, attempting migration")
                        return self._handle_migration(data)
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
            self._handle_persistence(e)
        return {"version": self.version, "inventory": [], "decks": [], "simulations": []}
        
    def _validate_history_data(self, data: Dict[str, Any]) -> bool:
        """Validate history data structure and content"""
        try:
            required_fields: set = {'version', 'inventory', 'decks', 'simulations'}
            if not all(field in data for field in required_fields):
                return False
                
            # Validate data types
            if not isinstance(data['inventory'], list) or not isinstance(data['decks'], list):
                return False
                
            # Validate timestamps
            for entry in data['inventory']:
                if not self._validate_timestamp(entry.get('timestamp')):
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Error validating history data: {e}")
            return False
            
    def _validate_timestamp(self, timestamp: Optional[str]) -> bool:
        """Validate timestamp format"""
        try:
            if timestamp is None:
                return False
            datetime.fromisoformat(timestamp)
            return True
        except (ValueError, TypeError):
            return False
            
    def _handle_persistence(self, error: Optional[Exception] = None) -> None:
        """Handle data persistence errors"""
        if error:
            self.logger.error(f"Error persisting analytics data: {error}")
        self._create_backup()
        
    def _handle_backup(self) -> None:
        """Create backup of analytics data"""
        try:
            backup_path: str = os.path.join(
                self.backup_dir, 
                f"analytics_backup_{datetime.now().isoformat()}.json"
            )
            os.makedirs(self.backup_dir, exist_ok=True)
            
            with open(backup_path, 'w') as f:
                json.dump(self.history, f)
                
            self.logger.info(f"Created backup at {backup_path}")
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            
    def _handle_versioning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle data versioning and migration"""
        if data.get('version') != self.version:
            self.logger.info(f"Migrating data from version {data.get('version')} to {self.version}")
            return self._handle_migration(data)
        return data
        
    def _handle_migration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data to current version"""
        try:
            # Add missing fields
            if 'simulations' not in data:
                data['simulations'] = []
                
            # Update version
            data['version'] = self.version
            
            # Save migrated data
            self._save_history(data)
            
            self.logger.info("Successfully migrated analytics data")
            return data
        except Exception as e:
            self.logger.error(f"Error migrating data: {e}")
            return {"version": self.version, "inventory": [], "decks": [], "simulations": []}
            
    def _handle_cleanup(self) -> None:
        """Clean up old backups and temporary files"""
        try:
            if os.path.exists(self.backup_dir):
                # Remove old backups
                for file in os.listdir(self.backup_dir):
                    if file.endswith('.json'):
                        file_path: str = os.path.join(self.backup_dir, file)
                        if os.path.getmtime(file_path) < (datetime.now() - timedelta(days=30)).timestamp():
                            os.remove(file_path)
                            
            # Clean up temporary files
            temp_dir: str = os.path.join(Config.RESOURCES_DIR, "temp")
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, file))
                    
            self.logger.info("Successfully cleaned up old files")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
    def _handle_export(self, format: str = 'json') -> str:
        """Export analytics data in specified format"""
        try:
            if format == 'json':
                return json.dumps(self.history, indent=2)
            elif format == 'csv':
                return self._convert_to_csv()
            elif format == 'excel':
                return self._convert_to_excel()
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise
            
    def _convert_to_csv(self) -> str:
        """Convert analytics data to CSV format"""
        try:
            # Convert inventory data
            inventory_df: pd.DataFrame = pd.DataFrame(self.history['inventory'])
            
            # Convert deck data
            deck_df: pd.DataFrame = pd.DataFrame(self.history['decks'])
            
            # Convert simulation data
            sim_df: pd.DataFrame = pd.DataFrame(self.history['simulations'])
            
            # Combine all data
            combined_df: pd.DataFrame = pd.concat([inventory_df, deck_df, sim_df], axis=1)
            
            return combined_df.to_csv(index=False)
        except Exception as e:
            self.logger.error(f"Error converting to CSV: {e}")
            raise
            
    def _convert_to_excel(self) -> str:
        """Convert analytics data to Excel format"""
        try:
            # Create Excel writer
            excel_path = os.path.join(Config.RESOURCES_DIR, "analytics_export.xlsx")
            with pd.ExcelWriter(excel_path) as writer:
                # Write inventory data
                pd.DataFrame(self.history['inventory']).to_excel(writer, sheet_name='Inventory', index=False)
                
                # Write deck data
                pd.DataFrame(self.history['decks']).to_excel(writer, sheet_name='Decks', index=False)
                
                # Write simulation data
                pd.DataFrame(self.history['simulations']).to_excel(writer, sheet_name='Simulations', index=False)
                
            return excel_path
        except Exception as e:
            self.logger.error(f"Error converting to Excel: {e}")
            raise
            
    def analyze_inventory(self, inventory: List[Dict]) -> Dict:
        """Analyze inventory with enhanced metrics"""
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "total_cards": sum(card["quantity"] for card in inventory),
                "total_value": sum(card["purchase_price"] * card["quantity"] for card in inventory),
                "color_distribution": self._analyze_colors(inventory),
                "rarity_distribution": self._analyze_rarity(inventory),
                "format_distribution": self._analyze_formats(inventory),
                "price_distribution": self._analyze_prices(inventory),
                "trends": self._analyze_trends(inventory),
                "performance_metrics": self._analyze_performance(inventory),
                "collection_health": self._analyze_collection_health(inventory)
            }
            
            # Save to history
            self.history["inventory"].append(analysis)
            self._save_history()
            
            self.logger.info("Successfully analyzed inventory")
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing inventory: {e}")
            raise
            
    def _analyze_colors(self, inventory: List[Dict]) -> Dict:
        color_counts = {}
        for card in inventory:
            for color in card.get("colors", []):
                color_counts[color] = color_counts.get(color, 0) + card["quantity"]
        return color_counts
        
    def _analyze_rarity(self, inventory: List[Dict]) -> Dict:
        rarity_counts = {}
        for card in inventory:
            rarity = card.get("rarity", "unknown")
            rarity_counts[rarity] = rarity_counts.get(rarity, 0) + card["quantity"]
        return rarity_counts
        
    def _analyze_trends(self, inventory: List[Dict]) -> Dict:
        if len(self.history["inventory"]) < 2:
            return {}
            
        current = self.history["inventory"][-1]
        previous = self.history["inventory"][-2]
        
        return {
            "value_change": current["total_value"] - previous["total_value"],
            "card_count_change": current["total_cards"] - previous["total_cards"]
        }

    def analyze_deck(self, deck_obj: dict) -> dict:
        return {
            "mana_curve": deck_obj["stats"]["mana_curve"],
            "total_cost": deck_obj["stats"]["total_cost"],
            "card_count": sum(count for _, count in deck_obj["mainboard"])
        }
    def _analyze_performance(self, inventory: List[Dict]) -> Dict:
        """Analyze card performance metrics"""
        performance = {
            "win_rates": {},
            "play_rates": {},
            "synergy_scores": {}
        }
        
        for card in inventory:
            card_name = card["name"]
            # Get performance data from simulation knowledge base
            perf_data = self._get_performance_data(card_name)
            if perf_data:
                performance["win_rates"][card_name] = perf_data.get("win_rate", 0)
                performance["play_rates"][card_name] = perf_data.get("play_rate", 0)
                performance["synergy_scores"][card_name] = perf_data.get("synergy_score", 0)
                
        return performance
        
    def _analyze_collection_health(self, inventory: List[Dict]) -> Dict:
        """Analyze collection health metrics"""
        health = {
            "diversity_score": self._calculate_diversity_score(inventory),
            "balance_score": self._calculate_balance_score(inventory),
            "completion_score": self._calculate_completion_score(inventory),
            "investment_score": self._calculate_investment_score(inventory)
        }
        return health
        
    def _calculate_diversity_score(self, inventory: List[Dict]) -> float:
        """Calculate collection diversity score"""
        unique_cards = len(set(card["name"] for card in inventory))
        total_cards = sum(card["quantity"] for card in inventory)
        return unique_cards / total_cards if total_cards > 0 else 0
        
    def _calculate_balance_score(self, inventory: List[Dict]) -> float:
        """Calculate collection balance score"""
        color_counts = self._analyze_colors(inventory)
        if not color_counts:
            return 1.0  # Colorless collection is perfectly balanced
            
        total = sum(color_counts.values())
        expected = total / len(color_counts)
        variance = sum((count - expected) ** 2 for count in color_counts.values()) / len(color_counts)
        return 1.0 - (variance / total)
        
    def _calculate_completion_score(self, inventory: List[Dict]) -> float:
        """Calculate collection completion score"""
        # This would need to be implemented based on your completion criteria
        return 0.0
        
    def _calculate_investment_score(self, inventory: List[Dict]) -> float:
        """Calculate collection investment score"""
        total_value = sum(card["purchase_price"] * card["quantity"] for card in inventory)
        total_cards = sum(card["quantity"] for card in inventory)
        return total_value / total_cards if total_cards > 0 else 0

