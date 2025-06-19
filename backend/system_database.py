"""
APTPT System Database - Comprehensive File and Configuration Tracking
Based on APTPT theory for robust, version-controlled system management
"""

import sqlite3
import hashlib
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import yaml
import shutil

class APTPTSystemDatabase:
    """
    APTPT-powered system database for tracking files, versions, and configurations
    Implements phase-aware versioning and convergence tracking
    """
    
    def __init__(self, db_path: str = "aptpt_system.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the database with APTPT-optimized schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Files table - tracks all files in the system
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    aptpt_phase TEXT DEFAULT 'stable'
                )
            """)
            
            # Configurations table - tracks system configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE NOT NULL,
                    config_type TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    aptpt_gain REAL DEFAULT 0.16,
                    aptpt_noise REAL DEFAULT 0.005
                )
            """)
            
            # Build artifacts table - tracks build outputs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS build_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artifact_name TEXT NOT NULL,
                    artifact_path TEXT UNIQUE NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    artifact_size INTEGER NOT NULL,
                    build_config TEXT NOT NULL,
                    build_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    aptpt_convergence REAL DEFAULT 1.0
                )
            """)
            
            # System states table - tracks system state history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_name TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    state_hash TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    aptpt_phase TEXT DEFAULT 'stable',
                    aptpt_error REAL DEFAULT 0.0
                )
            """)
            
            # Dependencies table - tracks file dependencies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    target_file TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_file) REFERENCES files (file_path),
                    FOREIGN KEY (target_file) REFERENCES files (file_path)
                )
            """)
            
            # Version history table - tracks all version changes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS version_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    old_version INTEGER NOT NULL,
                    new_version INTEGER NOT NULL,
                    change_type TEXT NOT NULL,
                    change_hash TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    aptpt_impact REAL DEFAULT 0.0,
                    FOREIGN KEY (file_path) REFERENCES files (file_path)
                )
            """)
            
            # Build audits table - tracks build audit results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS build_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file content"""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content string"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def scan_and_register_files(self, base_path: str = ".") -> Dict[str, Any]:
        """
        Scan directory and register all files in the database
        Returns APTPT convergence metrics
        """
        registered_files = []
        updated_files = []
        new_files = []
        
        for root, dirs, files in os.walk(base_path):
            # Skip virtual environments and build directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__', 'dist', 'build']]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, base_path)
                
                try:
                    file_size = os.path.getsize(file_path)
                    file_hash = self.calculate_file_hash(file_path)
                    
                    # Determine file type
                    if file.endswith('.py'):
                        file_type = 'python'
                    elif file.endswith('.ts') or file.endswith('.tsx'):
                        file_type = 'typescript'
                    elif file.endswith('.js') or file.endswith('.jsx'):
                        file_type = 'javascript'
                    elif file.endswith('.html'):
                        file_type = 'html'
                    elif file.endswith('.css'):
                        file_type = 'css'
                    elif file.endswith('.json'):
                        file_type = 'json'
                    elif file.endswith('.yaml') or file.endswith('.yml'):
                        file_type = 'yaml'
                    else:
                        file_type = 'other'
                    
                    # Read content for content hash
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    content_hash = self.calculate_content_hash(content)
                    
                    # Check if file exists in database
                    existing = self.get_file_info(relative_path)
                    
                    if existing is None:
                        # New file
                        self.register_file(relative_path, file_hash, file_size, file_type, content_hash)
                        new_files.append(relative_path)
                    elif existing['file_hash'] != file_hash:
                        # Updated file
                        self.update_file(relative_path, file_hash, file_size, content_hash)
                        updated_files.append(relative_path)
                    
                    registered_files.append(relative_path)
                    
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
        
        # Calculate APTPT convergence metrics
        total_files = len(registered_files)
        changed_files = len(updated_files) + len(new_files)
        convergence_ratio = 1.0 - (changed_files / total_files) if total_files > 0 else 1.0
        
        return {
            'total_files': total_files,
            'new_files': len(new_files),
            'updated_files': len(updated_files),
            'unchanged_files': total_files - changed_files,
            'convergence_ratio': convergence_ratio,
            'aptpt_phase': 'stable' if convergence_ratio > 0.95 else 'converging' if convergence_ratio > 0.8 else 'unstable'
        }
    
    def register_file(self, file_path: str, file_hash: str, file_size: int, file_type: str, content_hash: str):
        """Register a new file in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO files (file_path, file_hash, file_size, file_type, content_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (file_path, file_hash, file_size, file_type, content_hash))
            conn.commit()
    
    def update_file(self, file_path: str, file_hash: str, file_size: int, content_hash: str):
        """Update an existing file in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current version
            cursor.execute("SELECT version FROM files WHERE file_path = ?", (file_path,))
            result = cursor.fetchone()
            if result:
                current_version = result[0]
                new_version = current_version + 1
                
                # Update file
                cursor.execute("""
                    UPDATE files 
                    SET file_hash = ?, file_size = ?, content_hash = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE file_path = ?
                """, (file_hash, file_size, content_hash, new_version, file_path))
                
                # Record version history
                cursor.execute("""
                    INSERT INTO version_history (file_path, old_version, new_version, change_type, change_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (file_path, current_version, new_version, 'update', content_hash))
                
                conn.commit()
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get file information from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT file_path, file_hash, file_size, file_type, content_hash, version, created_at, updated_at, status, aptpt_phase
                FROM files WHERE file_path = ?
            """, (file_path,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'file_path': result[0],
                    'file_hash': result[1],
                    'file_size': result[2],
                    'file_type': result[3],
                    'content_hash': result[4],
                    'version': result[5],
                    'created_at': result[6],
                    'updated_at': result[7],
                    'status': result[8],
                    'aptpt_phase': result[9]
                }
            return None
    
    def register_configuration(self, config_name: str, config_type: str, config_data: Dict[str, Any]):
        """Register a configuration in the database"""
        config_json = json.dumps(config_data, sort_keys=True)
        config_hash = self.calculate_content_hash(config_json)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if configuration exists
            cursor.execute("SELECT version FROM configurations WHERE config_name = ?", (config_name,))
            result = cursor.fetchone()
            
            if result:
                # Update existing configuration
                current_version = result[0]
                new_version = current_version + 1
                
                cursor.execute("""
                    UPDATE configurations 
                    SET config_data = ?, config_hash = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE config_name = ?
                """, (config_json, config_hash, new_version, config_name))
            else:
                # Insert new configuration
                cursor.execute("""
                    INSERT INTO configurations (config_name, config_type, config_data, config_hash)
                    VALUES (?, ?, ?, ?)
                """, (config_name, config_type, config_json, config_hash))
            
            conn.commit()
    
    def get_configuration(self, config_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT config_name, config_type, config_data, config_hash, version, created_at, updated_at, status
                FROM configurations WHERE config_name = ?
            """, (config_name,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'config_name': result[0],
                    'config_type': result[1],
                    'config_data': json.loads(result[2]),
                    'config_hash': result[3],
                    'version': result[4],
                    'created_at': result[5],
                    'updated_at': result[6],
                    'status': result[7]
                }
            return None
    
    def register_build_artifact(self, artifact_name: str, artifact_path: str, build_config: Dict[str, Any]):
        """Register a build artifact in the database"""
        if os.path.exists(artifact_path):
            artifact_size = os.path.getsize(artifact_path)
            artifact_hash = self.calculate_file_hash(artifact_path)
            build_config_json = json.dumps(build_config, sort_keys=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO build_artifacts 
                    (artifact_name, artifact_path, artifact_hash, artifact_size, build_config)
                    VALUES (?, ?, ?, ?, ?)
                """, (artifact_name, artifact_path, artifact_hash, artifact_size, build_config_json))
                conn.commit()
    
    def register_build_audit(self, audit_result: dict):
        """Register a build audit result in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS build_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute(
                """
                INSERT INTO build_audits (audit_json, status)
                VALUES (?, ?)
                """,
                (json.dumps(audit_result, sort_keys=True), audit_result.get('status', 'unknown'))
            )
            conn.commit()
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system summary with APTPT metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # File statistics
            cursor.execute("SELECT COUNT(*) FROM files")
            total_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files WHERE aptpt_phase = 'stable'")
            stable_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files WHERE aptpt_phase = 'converging'")
            converging_files = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM files WHERE aptpt_phase = 'unstable'")
            unstable_files = cursor.fetchone()[0]
            
            # Configuration statistics
            cursor.execute("SELECT COUNT(*) FROM configurations")
            total_configs = cursor.fetchone()[0]
            
            # Build artifact statistics
            cursor.execute("SELECT COUNT(*) FROM build_artifacts")
            total_artifacts = cursor.fetchone()[0]
            
            # Recent changes
            cursor.execute("""
                SELECT COUNT(*) FROM version_history 
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            recent_changes = cursor.fetchone()[0]
            
            # Calculate APTPT convergence metrics
            convergence_ratio = stable_files / total_files if total_files > 0 else 1.0
            
            return {
                'total_files': total_files,
                'stable_files': stable_files,
                'converging_files': converging_files,
                'unstable_files': unstable_files,
                'total_configurations': total_configs,
                'total_build_artifacts': total_artifacts,
                'recent_changes_1h': recent_changes,
                'aptpt_convergence_ratio': convergence_ratio,
                'aptpt_phase': 'stable' if convergence_ratio > 0.95 else 'converging' if convergence_ratio > 0.8 else 'unstable',
                'database_created': datetime.now().isoformat()
            }
    
    def cleanup_old_versions(self, max_versions: int = 10):
        """Clean up old file versions to maintain database efficiency"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get files with too many versions
            cursor.execute("""
                SELECT file_path, COUNT(*) as version_count
                FROM version_history
                GROUP BY file_path
                HAVING version_count > ?
            """, (max_versions,))
            
            for file_path, version_count in cursor.fetchall():
                # Keep only the most recent versions
                cursor.execute("""
                    DELETE FROM version_history 
                    WHERE file_path = ? AND id NOT IN (
                        SELECT id FROM version_history 
                        WHERE file_path = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    )
                """, (file_path, file_path, max_versions))
            
            conn.commit()

# Global database instance
system_db = APTPTSystemDatabase()

def initialize_system_database():
    """Initialize the system database with current project state"""
    print("[APTPT] Initializing system database...")
    
    # Scan and register all files
    scan_results = system_db.scan_and_register_files()
    print(f"[APTPT] Registered {scan_results['total_files']} files")
    print(f"[APTPT] Convergence ratio: {scan_results['convergence_ratio']:.3f}")
    print(f"[APTPT] Phase: {scan_results['aptpt_phase']}")
    
    # Register key configurations
    configs_to_register = [
        ('webpack_config', 'webpack', {
            'mode': 'development',
            'entry': './src/webview/index.tsx',
            'output': {'path': './dist', 'filename': '[name].bundle.js'},
            'externals': {},
            'optimization': {'splitChunks': {'chunks': 'all'}}
        }),
        ('package_config', 'package', {
            'name': 'phasesynth-ultra-plus',
            'version': '1.0.0',
            'scripts': {'build': 'node scripts/build.js build'},
            'dependencies': {'react': '^18.0.0', 'react-dom': '^18.0.0'}
        }),
        ('api_config', 'api', {
            'host': 'localhost',
            'port': 8000,
            'cors': True,
            'endpoints': ['/health', '/api/health', '/dashboard']
        })
    ]
    
    for config_name, config_type, config_data in configs_to_register:
        system_db.register_configuration(config_name, config_type, config_data)
    
    # Register build artifacts
    build_artifacts = [
        ('main_bundle', 'cursor-extension/dist/main.bundle.js', {'type': 'webpack_bundle'}),
        ('index_html', 'cursor-extension/dist/index.html', {'type': 'html_template'}),
        ('api_server', 'backend/api_server.py', {'type': 'python_server'})
    ]
    
    for artifact_name, artifact_path, build_config in build_artifacts:
        if os.path.exists(artifact_path):
            system_db.register_build_artifact(artifact_name, artifact_path, build_config)
    
    # Get and display system summary
    summary = system_db.get_system_summary()
    print(f"[APTPT] System database initialized successfully")
    print(f"[APTPT] System phase: {summary['aptpt_phase']}")
    print(f"[APTPT] Convergence ratio: {summary['aptpt_convergence_ratio']:.3f}")
    
    return summary

if __name__ == "__main__":
    initialize_system_database() 