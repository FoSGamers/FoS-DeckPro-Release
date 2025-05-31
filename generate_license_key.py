import gspread
from google.oauth2.service_account import Credentials
import secrets
import string
import sys
import hashlib

# --- CONFIGURATION ---
SHEET_ID = '1hvOb_2fADbCs3DSLg0CMOdCAOVAy2Is_ok0JIvqAZEY'
WORKSHEET_NAME = 'Sheet1'
CREDENTIALS_FILE = 'fosbot-456712-d8da65f7bfc9.json'

# List of all supported features (update as needed)
ALL_FEATURES = [
    'break_builder',
    'export_whatnot',
    'export_item_listings',
    'enrich_scryfall',
    'add_scryfall',
    'adjust_whatnot_pricing',
    'process_packing_slips',
    'all_features',
]

def generate_key():
    alphabet = string.ascii_uppercase + string.digits
    return '-'.join(
        ''.join(secrets.choice(alphabet) for _ in range(4))
        for _ in range(3)
    )

def hash_key(key):
    return hashlib.sha256(key.strip().upper().encode('utf-8')).hexdigest()

def add_hash_to_sheet(key_hash, features_to_unlock, user='', notes=''):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(WORKSHEET_NAME)
    # Read and update header if needed
    header = worksheet.row_values(1)
    needed_cols = ['hash', 'status'] + ALL_FEATURES + ['user', 'notes']
    # Add any missing feature columns
    for col in needed_cols:
        if col not in header:
            header.append(col)
    if header != worksheet.row_values(1):
        worksheet.delete_row(1)
        worksheet.insert_row(header, 1)
    # Build row
    row = [''] * len(header)
    row[0] = key_hash
    row[1] = 'active'
    # Set features
    if 'all_features' in features_to_unlock:
        for feat in ALL_FEATURES:
            idx = header.index(feat)
            row[idx] = 'yes'
    else:
        for feat in ALL_FEATURES:
            idx = header.index(feat)
            row[idx] = 'yes' if feat in features_to_unlock else 'no'
    # Set user/notes
    if 'user' in header:
        row[header.index('user')] = user
    if 'notes' in header:
        row[header.index('notes')] = notes
    worksheet.append_row(row)
    print(f"Added key hash: {key_hash}")
    print(f"Features unlocked: {', '.join(features_to_unlock)}")

if __name__ == '__main__':
    user = sys.argv[1] if len(sys.argv) > 1 else ''
    notes = sys.argv[2] if len(sys.argv) > 2 else ''
    features_arg = sys.argv[3] if len(sys.argv) > 3 else 'all_features'
    features_to_unlock = [f.strip() for f in features_arg.split(',') if f.strip()]
    key = generate_key()
    key_hash = hash_key(key)
    add_hash_to_sheet(key_hash, features_to_unlock, user=user, notes=notes)
    print(f"Distribute this license key to user: {key}")
    print(f"(Hash stored in sheet: {key_hash})") 