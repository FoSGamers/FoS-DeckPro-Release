import os
import json
import requests
import hashlib
from PySide6.QtWidgets import QInputDialog, QMessageBox

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
        if validate_license_key(key, feature_name=feature_name):
            store_license_key(key)
            QMessageBox.information(parent, "License Activated", "Thank you! Paid features are now unlocked.")
            return True
        else:
            QMessageBox.warning(parent, "Invalid Key", "The license key you entered is not valid or does not include this feature.\n\nTo request access or support, contact: Thereal.FosGameres@gmail.com")
    return False

def validate_license_key(key, feature_name=None):
    """
    Check the Google Sheet for a valid, active key hash. If feature_name is given, require that column to be 'yes' or 'true' or '1', or 'all_features' to be 'yes'.
    The sheet should store only SHA256 hashes of keys in the first column.
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
                if header and feature_name in header:
                    idx = header.index(feature_name)
                    if idx < len(parts) and parts[idx].strip().lower() in ('yes', 'true', '1'):
                        return True
                if header and 'all_features' in header:
                    idx = header.index('all_features')
                    if idx < len(parts) and parts[idx].strip().lower() in ('yes', 'true', '1'):
                        return True
                return False
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