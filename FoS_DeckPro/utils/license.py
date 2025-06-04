import os
import json
import requests
import hashlib
from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
import datetime
import uuid
import glob

LICENSE_FILE = os.path.expanduser("~/.fosdeckpro_license.json")
LICENSE_API_URL = "https://us-central1-fosbot-456712.cloudfunctions.net/license_check"
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSbvtVQ8yxoc9GUBihv0LGLhgetHmQNfdGRo8VbXu-xSICNp2jKkZ3c91M5g-x5OkDD2ZlODcF5RH1X/pub?output=csv"

# Google Sheet trial config (legacy, not used in new API)
SHEET_ID = '1hvOb_2fADbCs3DSLg0CMOdCAOVAy2Is_ok0JIvqAZEY'
WORKSHEET_NAME = 'Sheet1'

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
    """
    Return the SHA256 hex digest of the normalized key string.
    """
    return hashlib.sha256(key.strip().upper().encode('utf-8')).hexdigest()

def get_machine_id():
    """
    Return a hashed unique machine identifier (MAC address) for privacy-safe tracking.
    """
    mac = uuid.getnode()
    return hashlib.sha256(str(mac).encode('utf-8')).hexdigest()

# --- New: License API Integration ---
def check_license_api(key, feature_name=None, machine_id=None):
    """
    Call the secure license check API to validate a license key for a given feature and machine.
    Returns the API response as a dict.
    """
    payload = {
        "key": key,
        "feature": feature_name,
        "machine_id": machine_id
    }
    try:
        resp = requests.post(LICENSE_API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"valid": False, "reason": f"API error: {resp.status_code}"}
    except Exception as e:
        return {"valid": False, "reason": str(e)}

def validate_license_key(key, feature_name=None):
    """
    Validate the license key for a specific feature using the secure backend API.
    Returns True if valid, False otherwise.
    """
    machine_id = get_machine_id()
    result = check_license_api(key, feature_name=feature_name, machine_id=machine_id)
    return result.get("valid", False)

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

def prompt_for_license_key(parent=None, feature_name=None):
    """
    Prompt the user for a license key and validate it using the API. Store if valid.
    """
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
            QMessageBox.warning(parent, "Invalid Key", "The license key you entered is not valid or does not include this feature.\n\nTo request access or support, contact: Thereal.FosGameres@gmail.com")
    return False

# --- Trial logic and legacy Google Sheet code is now deprecated and not used ---

def is_trial_active():
    """
    Check with the backend API if a trial is currently active for this machine.
    Returns True if a trial is active, False otherwise.
    """
    machine_id = get_machine_id()
    payload = {"trial_status": True, "machine_id": machine_id}
    try:
        resp = requests.post(LICENSE_API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("active_trial", False)
    except Exception:
        pass
    return False

def is_trial_expired():
    """
    Check with the backend API if all trials are expired for this machine.
    Returns True if no trial is active and all trials are used, False otherwise.
    """
    machine_id = get_machine_id()
    payload = {"trial_status": True, "machine_id": machine_id}
    try:
        resp = requests.post(LICENSE_API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Expired if not active and trial_count >= 3
            return not data.get("active_trial", False) and data.get("trial_count", 0) >= 3
    except Exception:
        pass
    return True

def get_trial_status():
    """
    Get the trial status for this machine from the backend API.
    Returns a dict with trial_count, active_trial, and expiry_date.
    """
    machine_id = get_machine_id()
    payload = {"trial_status": True, "machine_id": machine_id}
    try:
        resp = requests.post(LICENSE_API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {'trial_count': 0, 'active_trial': False, 'expiry_date': None}

def start_new_trial():
    """
    Request the backend API to start a new trial for this machine.
    Returns True if a new trial was started, False otherwise.
    """
    machine_id = get_machine_id()
    payload = {"start_trial": True, "machine_id": machine_id}
    try:
        resp = requests.post(LICENSE_API_URL, json=payload, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("started", False)
    except Exception:
        pass
    return False

# --- Documentation ---
"""
FoS-DeckPro License Validation Module
------------------------------------

This module now uses a secure backend API (Google Cloud Function) for all license and feature checks.

- All license validation is performed by POSTing to the LICENSE_API_URL.
- No Google service account credentials are ever distributed to users.
- All legacy direct Google Sheet access is deprecated and removed.
- All functions are documented with clear docstrings per project rules.
- To update the API endpoint, change LICENSE_API_URL at the top of this file.

See the cloud_functions/license_check/README.md for backend deployment and security details.
""" 