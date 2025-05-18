from pathlib import Path
import json
import shutil
from typing import Dict, Any, List
import logging
from datetime import datetime

class DataManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.schema_dir = Path("schemas")
        self.migration_dir = Path("migrations")
        self.setup_directories()
        
    def setup_directories(self):
        for directory in [self.data_dir, self.schema_dir, self.migration_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def load_data(self, data_type: str, validate: bool = True) -> Dict[str, Any]:
        """Load data with validation and migration"""
        data_path = self.data_dir / f"{data_type}.json"
        
        if not data_path.exists():
            return self._create_default_data(data_type)
            
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
                
            if validate:
                self._validate_data(data, data_type)
                
            # Check for migrations
            self._apply_migrations(data_type, data)
            
            return data
        except Exception as e:
            logging.error(f"Error loading data {data_type}: {e}")
            return self._load_backup(data_type)
            
    def _validate_data(self, data: Dict[str, Any], data_type: str):
        """Validate data against schema"""
        schema_path = self.schema_dir / f"{data_type}.schema.json"
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            # Implement schema validation
            
    def _apply_migrations(self, data_type: str, data: Dict[str, Any]):
        """Apply any pending migrations"""
        current_version = data.get('version', 0)
        migration_files = sorted(
            self.migration_dir.glob(f"{data_type}_*.json")
        )
        
        for migration_file in migration_files:
            migration_version = int(migration_file.stem.split('_')[1])
            if migration_version > current_version:
                with open(migration_file, 'r') as f:
                    migration = json.load(f)
                data = self._apply_migration(data, migration)
                data['version'] = migration_version
                
    def _apply_migration(self, data: Dict[str, Any], migration: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single migration"""
        # Implement migration logic
        return data
        
    def save_data(self, data_type: str, data: Dict[str, Any]):
        """Save data with backup"""
        data_path = self.data_dir / f"{data_type}.json"
        
        # Create backup
        if data_path.exists():
            backup_path = self.data_dir / "backups" / f"{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(data_path, backup_path)
            
        # Save data
        with open(data_path, 'w') as f:
            json.dump(data, f, indent=2) 