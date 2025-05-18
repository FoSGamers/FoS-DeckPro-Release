from typing import Dict, Any, List, Optional, Union, Tuple, Type
from pathlib import Path
import sqlite3
import json
import yaml
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
import base64
import io
import tempfile
import shutil
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"

class DatabaseOperation(Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    ALTER = "alter"

@dataclass
class DatabaseConfig:
    type: DatabaseType
    host: str = "localhost"
    port: int = None
    database: str = "database"
    username: str = None
    password: str = None
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

class DatabaseManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = None
        self.Session = None
        self.Base = declarative_base()
        self._setup_logging()
        self._setup_database()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("database")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "database.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_database(self):
        """Setup database connection"""
        try:
            # Create database URL
            if self.config.type == DatabaseType.SQLITE:
                db_url = f"sqlite:///{self.config.database}.db"
            elif self.config.type == DatabaseType.POSTGRESQL:
                db_url = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            elif self.config.type == DatabaseType.MYSQL:
                db_url = f"mysql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            else:
                raise ValueError(f"Unsupported database type: {self.config.type}")
                
            # Create engine
            self.engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo
            )
            
            # Create session factory
            self.Session = sessionmaker(bind=self.engine)
            
            # Create tables
            self.Base.metadata.create_all(self.engine)
            
        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            raise
            
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
            
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a raw SQL query"""
        try:
            with self.session_scope() as session:
                result = session.execute(query, params or {})
                return [dict(row) for row in result]
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return []
            
    def insert_data(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert data into a table"""
        try:
            with self.session_scope() as session:
                query = f"INSERT INTO {table} ({', '.join(data.keys())}) VALUES ({', '.join([':' + k for k in data.keys()])})"
                session.execute(query, data)
                return True
        except Exception as e:
            self.logger.error(f"Error inserting data: {e}")
            return False
            
    def update_data(self, table: str, data: Dict[str, Any], condition: str) -> bool:
        """Update data in a table"""
        try:
            with self.session_scope() as session:
                set_clause = ', '.join([f"{k} = :{k}" for k in data.keys()])
                query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
                session.execute(query, data)
                return True
        except Exception as e:
            self.logger.error(f"Error updating data: {e}")
            return False
            
    def delete_data(self, table: str, condition: str) -> bool:
        """Delete data from a table"""
        try:
            with self.session_scope() as session:
                query = f"DELETE FROM {table} WHERE {condition}"
                session.execute(query)
                return True
        except Exception as e:
            self.logger.error(f"Error deleting data: {e}")
            return False
            
    def get_data(self, table: str, columns: List[str] = None, condition: str = None) -> List[Dict]:
        """Get data from a table"""
        try:
            with self.session_scope() as session:
                cols = '*' if not columns else ', '.join(columns)
                query = f"SELECT {cols} FROM {table}"
                if condition:
                    query += f" WHERE {condition}"
                result = session.execute(query)
                return [dict(row) for row in result]
        except Exception as e:
            self.logger.error(f"Error getting data: {e}")
            return []
            
    def create_table(self, table: str, columns: Dict[str, str]) -> bool:
        """Create a new table"""
        try:
            with self.session_scope() as session:
                col_defs = ', '.join([f"{k} {v}" for k, v in columns.items()])
                query = f"CREATE TABLE {table} ({col_defs})"
                session.execute(query)
                return True
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            return False
            
    def drop_table(self, table: str) -> bool:
        """Drop a table"""
        try:
            with self.session_scope() as session:
                query = f"DROP TABLE {table}"
                session.execute(query)
                return True
        except Exception as e:
            self.logger.error(f"Error dropping table: {e}")
            return False
            
    def backup_database(self, backup_path: Union[str, Path]) -> bool:
        """Create a backup of the database"""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.config.type == DatabaseType.SQLITE:
                shutil.copy2(f"{self.config.database}.db", backup_path)
            else:
                # Implement backup for other database types
                pass
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error backing up database: {e}")
            return False
            
    def restore_database(self, backup_path: Union[str, Path]) -> bool:
        """Restore database from backup"""
        try:
            backup_path = Path(backup_path)
            
            if self.config.type == DatabaseType.SQLITE:
                shutil.copy2(backup_path, f"{self.config.database}.db")
            else:
                # Implement restore for other database types
                pass
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring database: {e}")
            return False
            
    def optimize_database(self) -> bool:
        """Optimize database performance"""
        try:
            if self.config.type == DatabaseType.SQLITE:
                with self.session_scope() as session:
                    session.execute("VACUUM")
                    session.execute("ANALYZE")
            else:
                # Implement optimization for other database types
                pass
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}")
            return False
            
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {
                "type": self.config.type.value,
                "tables": [],
                "size": 0,
                "last_optimized": None,
                "connection_count": 0
            }
            
            # Get table information
            with self.session_scope() as session:
                if self.config.type == DatabaseType.SQLITE:
                    result = session.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    stats["tables"] = [row[0] for row in result]
                    
                    # Get database size
                    db_path = Path(f"{self.config.database}.db")
                    if db_path.exists():
                        stats["size"] = db_path.stat().st_size
                        
                else:
                    # Implement stats for other database types
                    pass
                    
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {} 