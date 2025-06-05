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

def ensure_trial_columns(worksheet):
    """
    Ensure the Google Sheet has all required columns for trial logic.
    If any required columns are missing from the header, they are added in place.
    This function guarantees that trial logic will always work, even if the sheet is new or missing columns.
    """
    required_cols = [
        'machine_id',
        'trial_start_1', 'trial_expiry_1',
        'trial_start_2', 'trial_expiry_2',
        'trial_start_3', 'trial_expiry_3',
    ]
    data = worksheet.get_all_values()
    if not data:
        worksheet.append_row(required_cols)
        return required_cols
    header = data[0]
    updated = False
    for col in required_cols:
        if col not in header:
            header.append(col)
            updated = True
    if updated:
        worksheet.delete_row(1)
        worksheet.insert_row(header, 1)
    return header

def get_gsheet():
    """
    Get the worksheet object and ensure all required trial columns are present.
    This function is called before any trial or license logic to guarantee sheet structure.
    """
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(WORKSHEET_NAME)
    ensure_trial_columns(worksheet)
    return worksheet

def check_license(key, feature_name=None, machine_id=None):
    worksheet = get_gsheet()
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

# --- Trial Logic ---
def get_trial_status(machine_id):
    worksheet = get_gsheet()
    data = worksheet.get_all_values()
    if not data:
        return {'trial_count': 0, 'active_trial': False, 'expiry_date': None}
    header = data[0]
    rows = data[1:]
    trial_count = 0
    active_trial = False
    expiry_date = None
    today = datetime.date.today()
    found_row = None
    for row in rows:
        if len(row) < 1:
            continue
        if row[0] == machine_id:
            found_row = row
            break
    if found_row:
        # Look for up to 3 trials
        for i in range(1, 4):
            try:
                start_col = header.index(f'trial_start_{i}')
                expiry_col = header.index(f'trial_expiry_{i}')
                start_val = found_row[start_col] if start_col < len(found_row) else ''
                expiry_val = found_row[expiry_col] if expiry_col < len(found_row) else ''
                if start_val and expiry_val:
                    trial_count += 1
                    exp_date = datetime.datetime.strptime(expiry_val, '%Y-%m-%d').date()
                    if exp_date >= today:
                        active_trial = True
                        expiry_date = exp_date
            except Exception:
                continue
    return {
        'trial_count': trial_count,
        'active_trial': active_trial,
        'expiry_date': expiry_date.strftime('%Y-%m-%d') if expiry_date else None
    }

def start_new_trial(machine_id):
    worksheet = get_gsheet()
    data = worksheet.get_all_values()
    header = data[0]
    rows = data[1:]
    today = datetime.date.today()
    expiry = today + datetime.timedelta(days=3)
    found_row_idx = None
    found_row = None
    for idx, row in enumerate(rows):
        if len(row) < 1:
            continue
        if row[0] == machine_id:
            found_row = row
            found_row_idx = idx + 2  # 1-based, plus header
            break
    if found_row:
        # Find next available trial slot
        for i in range(1, 4):
            try:
                start_col = header.index(f'trial_start_{i}')
                expiry_col = header.index(f'trial_expiry_{i}')
                start_val = found_row[start_col] if start_col < len(found_row) else ''
                expiry_val = found_row[expiry_col] if expiry_col < len(found_row) else ''
                if not start_val and not expiry_val:
                    worksheet.update_cell(found_row_idx, start_col + 1, today.strftime('%Y-%m-%d'))
                    worksheet.update_cell(found_row_idx, expiry_col + 1, expiry.strftime('%Y-%m-%d'))
                    return True
            except Exception:
                continue
        return False  # No slots left
    else:
        # Add new row for this machine
        new_row = [''] * len(header)
        new_row[0] = machine_id
        for i in range(1, 4):
            try:
                start_col = header.index(f'trial_start_{i}')
                expiry_col = header.index(f'trial_expiry_{i}')
                if i == 1:
                    new_row[start_col] = today.strftime('%Y-%m-%d')
                    new_row[expiry_col] = expiry.strftime('%Y-%m-%d')
            except Exception:
                continue
        worksheet.append_row(new_row)
        return True
    return False

# --- Cloud Function Entry Point ---
def license_check(request: Request):
    if request.method != 'POST':
        return jsonify({'error': 'POST required'}), 405
    try:
        data = request.get_json(force=True)
        key = data.get('key')
        feature = data.get('feature')
        machine_id = data.get('machine_id')
        # Trial logic
        if data.get('trial_status'):
            if not machine_id:
                return jsonify({'error': 'Missing machine_id for trial status'}), 400
            status = get_trial_status(machine_id)
            return jsonify(status)
        if data.get('start_trial'):
            if not machine_id:
                return jsonify({'error': 'Missing machine_id for start_trial'}), 400
            started = start_new_trial(machine_id)
            return jsonify({'started': started, **get_trial_status(machine_id)})
        # License check logic
        if not key:
            return jsonify({'error': 'Missing license key'}), 400
        result = check_license(key, feature_name=feature, machine_id=machine_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500 