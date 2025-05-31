import os
import json
import requests
import hashlib
from PySide6.QtWidgets import QInputDialog, QMessageBox
import datetime

LICENSE_FILE = os.path.expanduser("~/.fosdeckpro_license.json")
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSbvtVQ8yxoc9GUBihv0LGLhgetHmQNfdGRo8VbXu-xSICNp2jKkZ3c91M5g-x5OkDD2ZlODcF5RH1X/pub?output=csv"

FEATURES = [
    'break_builder',
    'export_whatnot',
    'export_item_listings',
    'enrich_scryfall',
    'add_scryfall',
    'adjust_whatnot_pricing',
    'process_packing_slips',
    'all_features',
]

def hash_key(key):
    """Return the SHA256 hex digest of the normalized key string."""
    return hashlib.sha256(key.strip().upper().encode('utf-8')).hexdigest()

def prompt_for_license_key(parent=None, feature_name=None):
    msg = ("This feature requires a license.\n"
           "Please enter your license key to unlock paid features.\n\n"
           "To request access, contact: Thereal.FosGameres@gmail.com")
    if feature_name:
        msg = (f"This feature requires a license.\nPlease enter your license key to unlock: {feature_name.replace('_', ' ').title()}\n\n"
               "To request access, contact: Thereal.FosGameres@gmail.com")
    key, ok = QInputDialog.getText(parent, "Enter License Key", msg)
    if ok and key:
        valid = validate_license_key(key, feature_name=feature_name)
        if valid:
            store_license_key(key)
            QMessageBox.information(parent, "License Activated", "Thank you! Paid features are now unlocked.")
            return True
        else:
            # Check if expired for this feature
            try:
                resp = requests.get(GOOGLE_SHEET_CSV_URL, timeout=5)
                if resp.status_code == 200:
                    lines = resp.text.splitlines()
                    key_hash = hash_key(key)
                    header = None
                    for i, line in enumerate(lines):
                        parts = [p.strip() for p in line.split(',')]
                        if i == 0:
                            header = parts
                            continue
                        if key_hash == parts[0] and parts[1].lower() == 'active':
                            exp_col = f'{feature_name}_expiration'
                            type_col = f'{feature_name}_license_type'
                            exp_val = None
                            type_val = None
                            if header and exp_col in header:
                                idx = header.index(exp_col)
                                if idx < len(parts):
                                    exp_val = parts[idx].strip().lower()
                            if header and type_col in header:
                                idx = header.index(type_col)
                                if idx < len(parts):
                                    type_val = parts[idx].strip().lower()
                            if type_val == 'subscription' and exp_val and exp_val != 'lifetime':
                                try:
                                    today = datetime.date.today()
                                    exp_date = datetime.datetime.strptime(exp_val, '%Y-%m-%d').date()
                                    if exp_date < today:
                                        QMessageBox.warning(parent, "License Expired", f"Your license for {feature_name.replace('_', ' ').title()} has expired.\n\nPlease renew your subscription by contacting Thereal.FosGameres@gmail.com.")
                                        return False
                                except Exception:
                                    pass
            except Exception:
                pass
            QMessageBox.warning(parent, "Invalid Key", "The license key you entered is not valid or does not include this feature.\n\nTo request access or support, contact: Thereal.FosGameres@gmail.com")
    return False

def validate_license_key(key, feature_name=None):
    """
    Check the Google Sheet for a valid, active key hash. If feature_name is given, require that column to be 'yes' or 'true' or '1', or 'all_features' to be 'yes'.
    The sheet should store only SHA256 hashes of keys in the first column.
    Now also checks per-feature expiration and license type.
    """
    try:
        resp = requests.get(GOOGLE_SHEET_CSV_URL, timeout=5)
        if resp.status_code != 200:
            return False
        lines = resp.text.splitlines()
        key_hash = hash_key(key)
        header = None
        for i, line in enumerate(lines):
            parts = [p.strip() for p in line.split(',')]
            if i == 0:
                header = parts
                continue
            if len(parts) < 2:
                continue
            if key_hash == parts[0] and parts[1].lower() == 'active':
                # If no feature_name, any active key is valid
                if not feature_name:
                    return True
                # Check for feature column or all_features
                valid = False
                if header and feature_name in header:
                    idx = header.index(feature_name)
                    if idx < len(parts) and parts[idx].strip().lower() in ('yes', 'true', '1'):
                        valid = True
                if header and 'all_features' in header:
                    idx = header.index('all_features')
                    if idx < len(parts) and parts[idx].strip().lower() in ('yes', 'true', '1'):
                        valid = True
                if not valid:
                    return False
                # Per-feature expiration/license_type
                exp_col = f'{feature_name}_expiration'
                type_col = f'{feature_name}_license_type'
                exp_val = None
                type_val = None
                if header and exp_col in header:
                    idx = header.index(exp_col)
                    if idx < len(parts):
                        exp_val = parts[idx].strip().lower()
                if header and type_col in header:
                    idx = header.index(type_col)
                    if idx < len(parts):
                        type_val = parts[idx].strip().lower()
                # If lifetime, always valid
                if (type_val == 'lifetime') or (exp_val == 'lifetime'):
                    return True
                # If subscription, check expiration
                if type_val == 'subscription' and exp_val:
                    try:
                        today = datetime.date.today()
                        exp_date = datetime.datetime.strptime(exp_val, '%Y-%m-%d').date()
                        if exp_date >= today:
                            return True
                        else:
                            # Expired
                            return False
                    except Exception:
                        return False
                # If no type/expiration, fallback to valid
                return valid
        return False
    except Exception:
        pass
    return False

def is_license_valid(feature_name=None):
    """
    Check if a valid license key is stored locally and still valid for the given feature.
    The locally stored key is always hashed before checking.
    """
    if not os.path.exists(LICENSE_FILE):
        return False
    try:
        with open(LICENSE_FILE, "r") as f:
            data = json.load(f)
            key = data.get("key")
            if key and validate_license_key(key, feature_name=feature_name):
                return True
    except Exception:
        pass
    return False

def store_license_key(key):
    """
    Store the license key locally for future use (plain, but always checked as hash).
    """
    with open(LICENSE_FILE, "w") as f:
        json.dump({"key": key.strip()}, f) 