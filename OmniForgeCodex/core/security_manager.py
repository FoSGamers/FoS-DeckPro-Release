from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from pathlib import Path
import json
import os
import logging
import threading
import time
from datetime import datetime, timedelta
import hashlib
import base64
import secrets
from typing import Dict, Any, List, Optional, Union, Tuple
import jwt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import psutil
import socket
import platform
import shutil

class SecurityManager:
    def __init__(self):
        self.security_dir = Path("security")
        self.key_dir = self.security_dir / "keys"
        self.audit_dir = self.security_dir / "audit"
        self.policy_dir = self.security_dir / "policies"
        self.cert_dir = self.security_dir / "certs"
        
        # Security state
        self._encryption_keys: Dict[str, Fernet] = {}
        self._access_tokens: Dict[str, Dict[str, Any]] = {}
        self._security_policies: Dict[str, Dict[str, Any]] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._threat_detection: Dict[str, Any] = {}
        
        # Security settings
        self.key_rotation_interval = timedelta(days=30)
        self.token_expiry = timedelta(hours=24)
        self.max_failed_attempts = 3
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 12
        self.require_special_chars = True
        self.require_numbers = True
        self.require_uppercase = True
        
        # Monitoring
        self.monitor_thread = None
        self.monitor_interval = 60  # 1 minute
        self.security_metrics: Dict[str, Any] = {}
        
        # Setup
        self.setup_directories()
        self.load_policies()
        self.start_monitoring()
        
    def setup_directories(self):
        """Setup security directories"""
        for directory in [self.security_dir, self.key_dir, self.audit_dir, 
                         self.policy_dir, self.cert_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
    def load_policies(self):
        """Load security policies"""
        policy_file = self.policy_dir / "security_policies.json"
        if policy_file.exists():
            with open(policy_file, 'r') as f:
                self._security_policies = json.load(f)
        else:
            self._create_default_policies()
            
    def _create_default_policies(self):
        """Create default security policies"""
        self._security_policies = {
            'password': {
                'min_length': 12,
                'require_special_chars': True,
                'require_numbers': True,
                'require_uppercase': True,
                'max_age_days': 90
            },
            'encryption': {
                'algorithm': 'AES-256-GCM',
                'key_rotation_days': 30,
                'min_key_length': 32
            },
            'access_control': {
                'max_failed_attempts': 3,
                'lockout_duration_minutes': 30,
                'session_timeout_minutes': 60
            },
            'audit': {
                'retention_days': 365,
                'log_level': 'INFO',
                'sensitive_operations': ['password_change', 'key_rotation']
            }
        }
        self._save_policies()
        
    def _save_policies(self):
        """Save security policies"""
        with open(self.policy_dir / "security_policies.json", 'w') as f:
            json.dump(self._security_policies, f, indent=2)
            
    def initialize(self):
        """Initialize security manager"""
        self._setup_encryption()
        self._setup_access_control()
        self._setup_audit_logging()
        self._setup_threat_detection()
        
    def _setup_encryption(self):
        """Setup encryption keys"""
        # Generate or load master key
        master_key_file = self.key_dir / "master.key"
        if not master_key_file.exists():
            master_key = Fernet.generate_key()
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
        else:
            with open(master_key_file, 'rb') as f:
                master_key = f.read()
                
        self._encryption_keys['master'] = Fernet(master_key)
        
        # Generate or load application keys
        for key_name in ['config', 'data', 'cache']:
            key_file = self.key_dir / f"{key_name}.key"
            if not key_file.exists():
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
            else:
                with open(key_file, 'rb') as f:
                    key = f.read()
            self._encryption_keys[key_name] = Fernet(key)
            
    def _setup_access_control(self):
        """Setup access control"""
        self._access_tokens = {}
        self._failed_attempts = {}
        self._locked_accounts = {}
        
    def _setup_audit_logging(self):
        """Setup audit logging"""
        self._audit_log = []
        self._load_audit_log()
        
    def _setup_threat_detection(self):
        """Setup threat detection"""
        self._threat_detection = {
            'failed_attempts': {},
            'suspicious_activities': [],
            'blocked_ips': set(),
            'last_scan': datetime.now()
        }
        
    def start_monitoring(self):
        """Start security monitoring"""
        def monitor():
            while True:
                self._check_security_metrics()
                self._detect_threats()
                self._rotate_keys_if_needed()
                time.sleep(self.monitor_interval)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def _check_security_metrics(self):
        """Check security metrics"""
        self.security_metrics = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self._get_system_info(),
            'security_status': self._get_security_status(),
            'threat_level': self._calculate_threat_level()
        }
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'platform': platform.platform(),
            'hostname': socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'memory_usage': psutil.virtual_memory().percent,
            'cpu_usage': psutil.cpu_percent(),
            'disk_usage': psutil.disk_usage('/').percent
        }
        
    def _get_security_status(self) -> Dict[str, Any]:
        """Get security status"""
        return {
            'encryption_status': self._check_encryption_status(),
            'access_control_status': self._check_access_control_status(),
            'audit_status': self._check_audit_status(),
            'threat_detection_status': self._check_threat_detection_status()
        }
        
    def _calculate_threat_level(self) -> str:
        """Calculate current threat level"""
        threat_indicators = [
            len(self._threat_detection['suspicious_activities']),
            len(self._threat_detection['blocked_ips']),
            sum(self._failed_attempts.values())
        ]
        
        if any(indicator > 10 for indicator in threat_indicators):
            return 'HIGH'
        elif any(indicator > 5 for indicator in threat_indicators):
            return 'MEDIUM'
        return 'LOW'
        
    def encrypt_data(self, data: Union[dict, str], key_name: str = 'master') -> bytes:
        """Encrypt data using specified key"""
        if key_name not in self._encryption_keys:
            raise ValueError(f"Unknown key: {key_name}")
            
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode()
            
        return self._encryption_keys[key_name].encrypt(data)
        
    def decrypt_data(self, encrypted_data: bytes, key_name: str = 'master') -> Union[dict, str]:
        """Decrypt data using specified key"""
        if key_name not in self._encryption_keys:
            raise ValueError(f"Unknown key: {key_name}")
            
        decrypted = self._encryption_keys[key_name].decrypt(encrypted_data)
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted.decode()
            
    def secure_store(self, key: str, data: dict, key_name: str = 'data'):
        """Store data securely"""
        encrypted = self.encrypt_data(data, key_name)
        store_path = self.security_dir / "secure" / f"{key}.enc"
        store_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(store_path, 'wb') as f:
            f.write(encrypted)
            
        self._audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': 'secure_store',
            'key': key,
            'status': 'success'
        })
        
    def secure_retrieve(self, key: str, key_name: str = 'data') -> dict:
        """Retrieve securely stored data"""
        store_path = self.security_dir / "secure" / f"{key}.enc"
        if not store_path.exists():
            return {}
            
        with open(store_path, 'rb') as f:
            encrypted = f.read()
            
        self._audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': 'secure_retrieve',
            'key': key,
            'status': 'success'
        })
        
        return self.decrypt_data(encrypted, key_name)
        
    def generate_access_token(self, user_id: str, permissions: List[str]) -> str:
        """Generate access token"""
        if self._is_account_locked(user_id):
            raise SecurityError("Account is locked")
            
        token_data = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + self.token_expiry
        }
        
        token = jwt.encode(token_data, self._encryption_keys['master']._encryption_key,
                         algorithm='HS256')
        
        self._access_tokens[token] = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.now().isoformat()
        }
        
        return token
        
    def validate_access_token(self, token: str) -> bool:
        """Validate access token"""
        try:
            jwt.decode(token, self._encryption_keys['master']._encryption_key,
                      algorithms=['HS256'])
            return token in self._access_tokens
        except jwt.InvalidTokenError:
            return False
            
    def check_permission(self, token: str, required_permission: str) -> bool:
        """Check if token has required permission"""
        if not self.validate_access_token(token):
            return False
            
        token_data = self._access_tokens[token]
        return required_permission in token_data['permissions']
        
    def _is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked"""
        if user_id in self._locked_accounts:
            lock_time = self._locked_accounts[user_id]
            if datetime.now() - lock_time < self.lockout_duration:
                return True
            else:
                del self._locked_accounts[user_id]
        return False
        
    def record_failed_attempt(self, user_id: str):
        """Record failed login attempt"""
        self._failed_attempts[user_id] = self._failed_attempts.get(user_id, 0) + 1
        
        if self._failed_attempts[user_id] >= self.max_failed_attempts:
            self._locked_accounts[user_id] = datetime.now()
            
        self._audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': 'failed_attempt',
            'user_id': user_id,
            'attempts': self._failed_attempts[user_id]
        })
        
    def _rotate_keys_if_needed(self):
        """Rotate encryption keys if needed"""
        for key_name, key in self._encryption_keys.items():
            key_file = self.key_dir / f"{key_name}.key"
            if key_file.exists():
                key_age = datetime.now() - datetime.fromtimestamp(key_file.stat().st_mtime)
                if key_age > self.key_rotation_interval:
                    self._rotate_key(key_name)
                    
    def _rotate_key(self, key_name: str):
        """Rotate encryption key"""
        new_key = Fernet.generate_key()
        key_file = self.key_dir / f"{key_name}.key"
        
        # Backup old key
        backup_file = self.key_dir / "backups" / f"{key_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.key"
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(key_file, backup_file)
        
        # Save new key
        with open(key_file, 'wb') as f:
            f.write(new_key)
            
        self._encryption_keys[key_name] = Fernet(new_key)
        
        self._audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': 'key_rotation',
            'key_name': key_name,
            'status': 'success'
        })
        
    def _detect_threats(self):
        """Detect security threats"""
        # Check for suspicious activities
        self._check_suspicious_activities()
        
        # Check for brute force attempts
        self._check_brute_force_attempts()
        
        # Check for unusual access patterns
        self._check_access_patterns()
        
    def _check_suspicious_activities(self):
        """Check for suspicious activities"""
        # Implement suspicious activity detection
        pass
        
    def _check_brute_force_attempts(self):
        """Check for brute force attempts"""
        # Implement brute force detection
        pass
        
    def _check_access_patterns(self):
        """Check for unusual access patterns"""
        # Implement access pattern analysis
        pass
        
    def cleanup(self):
        """Clean up security resources"""
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
        # Save audit log
        self._save_audit_log()
        
        # Clear sensitive data
        self._encryption_keys.clear()
        self._access_tokens.clear()
        self._failed_attempts.clear()
        self._locked_accounts.clear()
        
    def _load_audit_log(self):
        """Load audit log from file"""
        audit_file = self.audit_dir / "audit.log"
        if audit_file.exists():
            try:
                with open(audit_file, 'r') as f:
                    self._audit_log = json.load(f)
            except Exception as e:
                logging.error(f"Error loading audit log: {e}")
                self._audit_log = []
        else:
            self._audit_log = []
            self._save_audit_log()

    def _save_audit_log(self):
        """Save audit log to file"""
        audit_file = self.audit_dir / "audit.log"
        try:
            with open(audit_file, 'w') as f:
                json.dump(self._audit_log, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving audit log: {e}")
        
class SecurityError(Exception):
    """Security-related error"""
    pass 