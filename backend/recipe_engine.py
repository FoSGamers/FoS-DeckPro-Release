import sqlite3
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class RecipeEngine:
    def __init__(self, dbfile: str = "phasesynth_recipes.db"):
        self.dbfile = dbfile
        self._init_db()
    
    def _init_db(self):
        """Initialize recipe database with APTPT/HCE/REI tracking"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Core recipe table
        c.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY,
                context TEXT,
                code_diff TEXT,
                phase_vector TEXT,
                entropy REAL,
                rei_score REAL,
                aptpt_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Recipe execution history
        c.execute('''
            CREATE TABLE IF NOT EXISTS recipe_history (
                id INTEGER PRIMARY KEY,
                recipe_id INTEGER,
                success BOOLEAN,
                phase_vector TEXT,
                entropy REAL,
                rei_score REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.dbfile)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _compute_phase_vector(self, context: str, code_diff: str) -> str:
        """Compute phase vector using APTPT theory"""
        combined = f"{context}{code_diff}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _compute_entropy(self, text: str) -> float:
        """Compute entropy using HCE theory"""
        if not text:
            return 0.0
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1
        total = len(text)
        entropy = 0.0
        for count in char_freq.values():
            p = count / total
            entropy -= p * math.log2(p) if p > 0 else 0
        return entropy
    
    def _compute_rei_score(self, phase_vector: str) -> float:
        """Compute REI score using REI theory"""
        if not phase_vector:
            return 0.0
        # REI score based on phase vector properties
        return sum(ord(c) for c in phase_vector[:8]) / (8 * 255)
    
    def store_recipe(self, context: str, code_diff: str, aptpt_score: float = 0.0):
        """Store recipe with APTPT/HCE/REI metadata"""
        phase_vector = self._compute_phase_vector(context, code_diff)
        entropy = self._compute_entropy(code_diff)
        rei_score = self._compute_rei_score(phase_vector)
        
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO recipes (context, code_diff, phase_vector, entropy, rei_score, aptpt_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (context, code_diff, phase_vector, entropy, rei_score, aptpt_score))
        
        recipe_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return recipe_id
    
    def fetch_best_recipe(self, context: str) -> Optional[Dict[str, Any]]:
        """Fetch best matching recipe using APTPT/HCE/REI scoring"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Search by context similarity and scores
        c.execute('''
            SELECT id, context, code_diff, phase_vector, entropy, rei_score, aptpt_score
            FROM recipes
            WHERE context LIKE ?
            ORDER BY (entropy + rei_score + aptpt_score) DESC
            LIMIT 1
        ''', (f'%{context}%',))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def record_execution(self, recipe_id: int, success: bool):
        """Record recipe execution with APTPT/HCE/REI tracking"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Get recipe details
        c.execute('''
            SELECT phase_vector, entropy, rei_score
            FROM recipes
            WHERE id = ?
        ''', (recipe_id,))
        
        recipe = c.fetchone()
        if recipe:
            c.execute('''
                INSERT INTO recipe_history (recipe_id, success, phase_vector, entropy, rei_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (recipe_id, success, recipe['phase_vector'], recipe['entropy'], recipe['rei_score']))
            
            conn.commit()
        
        conn.close()
    
    def get_execution_history(self, recipe_id: int) -> List[Dict[str, Any]]:
        """Get execution history with APTPT/HCE/REI metrics"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT success, phase_vector, entropy, rei_score, timestamp
            FROM recipe_history
            WHERE recipe_id = ?
            ORDER BY timestamp DESC
        ''', (recipe_id,))
        
        history = [dict(row) for row in c.fetchall()]
        conn.close()
        return history
    
    def cleanup_old_recipes(self, days: int = 30):
        """Clean up old recipes and history"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''
            DELETE FROM recipe_history
            WHERE timestamp < datetime('now', ?)
        ''', (f'-{days} days',))
        
        conn.commit()
        conn.close()

# Global instance
recipe_engine = RecipeEngine() 