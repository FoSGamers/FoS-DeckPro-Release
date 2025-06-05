import os
import json
import hashlib
from flask import Request, jsonify
import gspread
from google.oauth2.service_account import Credentials
import datetime
import traceback

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
    If any required trial columns are missing from the header, they are appended at the end.
    This function preserves all existing columns and data, and guarantees that trial logic will always work.
    Uses worksheet.update('1:1', [new_header]) for robust header updates (delete_row/insert_row is unreliable).
    """
    required_cols = [
        'machine_id',
        'trial_start_1', 'trial_expiry_1',
        'trial_start_2', 'trial_expiry_2',
        'trial_start_3', 'trial_expiry_3',
    ]
    data = worksheet.get_all_values()
    print('[DEBUG] Current header:', data[0] if data else None)
    if not data:
        worksheet.append_row(required_cols)
        print('[TRIAL] Header created:', required_cols)
        return required_cols
    header = data[0]
    missing_cols = [col for col in required_cols if col not in header]
    if missing_cols:
        new_header = header + missing_cols
        worksheet.update('1:1', [new_header])
        print('[TRIAL] Header updated with missing columns:', missing_cols)
    return worksheet.get_all_values()[0]

def get_gsheet():
    """
    Get the worksheet object and ensure all required trial columns are present.
    This function is called before any trial or license logic to guarantee sheet structure.
    """
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        ensure_trial_columns(worksheet)
        print('[DEBUG] Worksheet loaded and trial columns ensured.')
        return worksheet
    except Exception as e:
        print('[ERROR] get_gsheet failed:', str(e))
        traceback.print_exc()
        raise

def check_license(key, feature_name=None, machine_id=None):
    print(f'[DEBUG] check_license called with key={key}, feature_name={feature_name}, machine_id={machine_id}')
    try:
        worksheet = get_gsheet()
        data = worksheet.get_all_values()
        if not data:
            print('[DEBUG] No data in sheet')
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
                    print('[DEBUG] License valid for all features')
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
                    print('[DEBUG] Feature not enabled')
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
                    print('[DEBUG] License is lifetime')
                    return {'valid': True, 'features': feature_name, 'expiration': 'lifetime'}
                if type_val == 'subscription' and exp_val:
                    try:
                        today = datetime.date.today()
                        exp_date = datetime.datetime.strptime(exp_val, '%Y-%m-%d').date()
                        if exp_date >= today:
                            print('[DEBUG] License is valid subscription')
                            return {'valid': True, 'features': feature_name, 'expiration': exp_val}
                        else:
                            print('[DEBUG] License expired')
                            return {'valid': False, 'reason': 'Expired', 'expiration': exp_val}
                    except Exception as e:
                        print('[ERROR] Invalid expiration format:', str(e))
                        traceback.print_exc()
                        return {'valid': False, 'reason': 'Invalid expiration format'}
                print('[DEBUG] License valid for feature')
                return {'valid': True, 'features': feature_name, 'expiration': exp_val}
        print('[DEBUG] Key not found or inactive')
        return {'valid': False, 'reason': 'Key not found or inactive'}
    except Exception as e:
        print('[ERROR] check_license failed:', str(e))
        traceback.print_exc()
        return {'valid': False, 'reason': str(e)}

# --- Trial Logic ---
def get_trial_status(machine_id):
    print(f'[DEBUG] get_trial_status called with machine_id={machine_id}')
    try:
        worksheet = get_gsheet()
        data = worksheet.get_all_values()
        if not data:
            print('[DEBUG] No data in sheet')
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
            print('[DEBUG] Found row for machine_id:', found_row)
            # Look for up to 3 trials
            for i in range(1, 4):
                try:
                    start_col = header.index(f'trial_start_{i}')
                    expiry_col = header.index(f'trial_expiry_{i}')
                    start_val = found_row[start_col] if start_col < len(found_row) else ''
                    expiry_val = found_row[expiry_col] if expiry_col < len(found_row) else ''
                    print(f'[DEBUG] Trial {i}: start={start_val}, expiry={expiry_val}')
                    if start_val and expiry_val:
                        trial_count += 1
                        exp_date = datetime.datetime.strptime(expiry_val, '%Y-%m-%d').date()
                        if exp_date >= today:
                            active_trial = True
                            expiry_date = exp_date
                except Exception as e:
                    print(f'[ERROR] Trial {i} check failed:', str(e))
                    traceback.print_exc()
                    continue
        else:
            print('[DEBUG] No row found for machine_id')
        return {
            'trial_count': trial_count,
            'active_trial': active_trial,
            'expiry_date': expiry_date.strftime('%Y-%m-%d') if expiry_date else None
        }
    except Exception as e:
        print('[ERROR] get_trial_status failed:', str(e))
        traceback.print_exc()
        return {'trial_count': 0, 'active_trial': False, 'expiry_date': None}

def start_new_trial(machine_id):
    print(f'[DEBUG] start_new_trial called with machine_id={machine_id}')
    try:
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
            print('[DEBUG] Found row for machine_id:', found_row)
            # Find next available trial slot
            for i in range(1, 4):
                try:
                    start_col = header.index(f'trial_start_{i}')
                    expiry_col = header.index(f'trial_expiry_{i}')
                    start_val = found_row[start_col] if start_col < len(found_row) else ''
                    expiry_val = found_row[expiry_col] if expiry_col < len(found_row) else ''
                    print(f'[DEBUG] Trial {i}: start={start_val}, expiry={expiry_val}')
                    if not start_val and not expiry_val:
                        worksheet.update_cell(found_row_idx, start_col + 1, today.strftime('%Y-%m-%d'))
                        worksheet.update_cell(found_row_idx, expiry_col + 1, expiry.strftime('%Y-%m-%d'))
                        print(f'[DEBUG] Started new trial {i} for machine_id={machine_id}')
                        return True
                except Exception as e:
                    print(f'[ERROR] Trial {i} start failed:', str(e))
                    traceback.print_exc()
                    continue
            print('[DEBUG] No trial slots left for machine_id')
            return False  # No slots left
        else:
            print('[DEBUG] No row found for machine_id, creating new row')
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
                except Exception as e:
                    print(f'[ERROR] Trial {i} new row failed:', str(e))
                    traceback.print_exc()
                    continue
            worksheet.append_row(new_row)
            print(f'[DEBUG] Appended new row for machine_id={machine_id}:', new_row)
            return True
        print('[DEBUG] Could not start new trial for machine_id')
        return False
    except Exception as e:
        print('[ERROR] start_new_trial failed:', str(e))
        traceback.print_exc()
        return False

# --- Cloud Function Entry Point ---
def license_check(request: Request):
    print('[DEBUG] license_check called')
    try:
        if request.method != 'POST':
            print('[ERROR] Method not allowed:', request.method)
            return jsonify({'error': 'POST required'}), 405
        data = request.get_json(force=True)
        print('[DEBUG] Request payload:', data)
        key = data.get('key')
        feature = data.get('feature')
        machine_id = data.get('machine_id')
        # Trial logic
        if data.get('trial_status'):
            if not machine_id:
                print('[ERROR] Missing machine_id for trial status')
                return jsonify({'error': 'Missing machine_id for trial status'}), 400
            status = get_trial_status(machine_id)
            print('[DEBUG] Trial status response:', status)
            return jsonify(status)
        if data.get('start_trial'):
            if not machine_id:
                print('[ERROR] Missing machine_id for start_trial')
                return jsonify({'error': 'Missing machine_id for start_trial'}), 400
            started = start_new_trial(machine_id)
            status = get_trial_status(machine_id)
            print('[DEBUG] Start trial response:', {'started': started, **status})
            return jsonify({'started': started, **status})
        # License check logic
        if not key:
            print('[ERROR] Missing license key')
            return jsonify({'error': 'Missing license key'}), 400
        result = check_license(key, feature_name=feature, machine_id=machine_id)
        print('[DEBUG] License check response:', result)
        return jsonify(result)
    except Exception as e:
        print('[ERROR] license_check failed:', str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500 