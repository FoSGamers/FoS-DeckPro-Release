import os
import json
import hashlib
from flask import Request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import datetime

# Environment variable for credentials file path (set in Cloud Function config)
CREDENTIALS_FILE = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
SHEET_ID = os.environ.get('SHEET_ID', '1hvOb_2fADbCs3DSLg0CMOdCAOVAy2Is_ok0JIvqAZEY')
WORKSHEET_NAME = os.environ.get('WORKSHEET_NAME', 'Sheet1')

# --- Utility Functions ---
def hash_key(key):
    return hashlib.sha256(key.strip().upper().encode('utf-8')).hexdigest()

def check_license(key, feature_name=None, machine_id=None):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(WORKSHEET_NAME)
    data = worksheet.get_all_values()
    if not data:
        return {'valid': False, 'reason': 'No data in sheet'}
    header = data[0]
    rows = data[1:]
    key_hash = hash_key(key)
    for row in rows:
        if len(row) < 2:
            continue
        if row[0] == key_hash and row[1].lower() == 'active':
            # Check feature
            if not feature_name:
                return {'valid': True, 'features': 'all', 'expiration': None}
            valid = False
            if feature_name in header:
                idx = header.index(feature_name)
                if idx < len(row) and row[idx].strip().lower() in ('yes', 'true', '1'):
                    valid = True
            if 'all_features' in header:
                idx = header.index('all_features')
                if idx < len(row) and row[idx].strip().lower() in ('yes', 'true', '1'):
                    valid = True
            if not valid:
                return {'valid': False, 'reason': 'Feature not enabled'}
            # Check expiration/type
            exp_col = f'{feature_name}_expiration'
            type_col = f'{feature_name}_license_type'
            exp_val = None
            type_val = None
            if exp_col in header:
                idx = header.index(exp_col)
                if idx < len(row):
                    exp_val = row[idx].strip().lower()
            if type_col in header:
                idx = header.index(type_col)
                if idx < len(row):
                    type_val = row[idx].strip().lower()
            if (type_val == 'lifetime') or (exp_val == 'lifetime'):
                return {'valid': True, 'features': feature_name, 'expiration': 'lifetime'}
            if type_val == 'subscription' and exp_val:
                try:
                    today = datetime.date.today()
                    exp_date = datetime.datetime.strptime(exp_val, '%Y-%m-%d').date()
                    if exp_date >= today:
                        return {'valid': True, 'features': feature_name, 'expiration': exp_val}
                    else:
                        return {'valid': False, 'reason': 'Expired', 'expiration': exp_val}
                except Exception:
                    return {'valid': False, 'reason': 'Invalid expiration format'}
            return {'valid': True, 'features': feature_name, 'expiration': exp_val}
    return {'valid': False, 'reason': 'Key not found or inactive'}

# --- Cloud Function Entry Point ---
def license_check(request: Request):
    if request.method != 'POST':
        return jsonify({'error': 'POST required'}), 405
    try:
        data = request.get_json(force=True)
        key = data.get('key')
        feature = data.get('feature')
        machine_id = data.get('machine_id')
        if not key:
            return jsonify({'error': 'Missing license key'}), 400
        result = check_license(key, feature_name=feature, machine_id=machine_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 