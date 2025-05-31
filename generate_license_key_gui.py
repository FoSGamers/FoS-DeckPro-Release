import sys
import hashlib
import secrets
import string
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QMessageBox, QScrollArea, QGroupBox, QComboBox, QDateEdit
)
import gspread
from google.oauth2.service_account import Credentials
import datetime
from PySide6.QtCore import QDate

# --- CONFIGURATION ---
SHEET_ID = '1hvOb_2fADbCs3DSLg0CMOdCAOVAy2Is_ok0JIvqAZEY'
WORKSHEET_NAME = 'Sheet1'
CREDENTIALS_FILE = 'fosbot-456712-d8da65f7bfc9.json'
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

# --- License Key Logic ---
def generate_key():
    alphabet = string.ascii_uppercase + string.digits
    return '-'.join(
        ''.join(secrets.choice(alphabet) for _ in range(4))
        for _ in range(3)
    )

def hash_key(key):
    return hashlib.sha256(key.strip().upper().encode('utf-8')).hexdigest()

def add_hash_to_sheet(key_hash, features_to_unlock, feature_expirations, feature_types, user='', notes=''):
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(WORKSHEET_NAME)
    # Read and update header if needed
    header = worksheet.row_values(1)
    needed_cols = ['hash', 'status'] + ALL_FEATURES + ['user', 'notes']
    # Add per-feature expiration/type columns
    for feat in ALL_FEATURES:
        if feat == 'all_features':
            continue
        needed_cols.append(f'{feat}_expiration')
        needed_cols.append(f'{feat}_license_type')
    # If header is missing any needed columns, update it
    header_set = set(header)
    for col in needed_cols:
        if col not in header_set:
            header.append(col)
    # If header order is wrong or missing columns, rewrite header
    if header != worksheet.row_values(1):
        # Remove any extra columns from header that are not needed
        header = [col for col in header if col in needed_cols]
        # Add any missing needed columns at the end
        for col in needed_cols:
            if col not in header:
                header.append(col)
        worksheet.update('1:1', [header])
    row = [''] * len(header)
    row[0] = key_hash
    row[1] = 'active'
    if 'all_features' in features_to_unlock:
        for feat in ALL_FEATURES:
            idx = header.index(feat)
            row[idx] = 'yes'
            if feat != 'all_features':
                row[header.index(f'{feat}_expiration')] = feature_expirations.get(feat, 'lifetime')
                row[header.index(f'{feat}_license_type')] = feature_types.get(feat, 'lifetime')
    else:
        for feat in ALL_FEATURES:
            idx = header.index(feat)
            row[idx] = 'yes' if feat in features_to_unlock else 'no'
            if feat in features_to_unlock and feat != 'all_features':
                row[header.index(f'{feat}_expiration')] = feature_expirations.get(feat, 'lifetime')
                row[header.index(f'{feat}_license_type')] = feature_types.get(feat, 'lifetime')
    if 'user' in header:
        row[header.index('user')] = user
    if 'notes' in header:
        row[header.index('notes')] = notes
    worksheet.append_row(row)
    return key_hash

# --- PySide6 GUI ---
class LicenseKeyGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FoS-DeckPro License Key Generator')
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel('<b>FoS-DeckPro License Key Generator</b>'))
        layout.addWidget(QLabel('Enter user info and select features to unlock.'))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('User Name (optional)')
        layout.addWidget(QLabel('User Name:'))
        layout.addWidget(self.name_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText('Notes (optional)')
        layout.addWidget(QLabel('Notes:'))
        layout.addWidget(self.notes_input)

        # Features checkboxes and per-feature controls
        self.feature_checks = {}
        self.feature_type_boxes = {}
        self.feature_expiry_boxes = {}
        features_box = QGroupBox('Features to Unlock:')
        features_layout = QVBoxLayout(features_box)
        self.select_all = QCheckBox('Select All Features (bundle)')
        self.select_all.stateChanged.connect(self.toggle_all_features)
        features_layout.addWidget(self.select_all)
        for feat in ALL_FEATURES:
            if feat == 'all_features':
                continue
            row = QHBoxLayout()
            cb = QCheckBox(feat.replace('_', ' ').title())
            self.feature_checks[feat] = cb
            row.addWidget(cb)
            # License type dropdown
            type_box = QComboBox()
            type_box.addItems(['subscription', 'lifetime'])
            type_box.setCurrentText('subscription')
            self.feature_type_boxes[feat] = type_box
            row.addWidget(type_box)
            # Expiration date picker
            expiry_box = QDateEdit()
            expiry_box.setCalendarPopup(True)
            expiry_box.setDate(QDate.currentDate().addMonths(1))
            self.feature_expiry_boxes[feat] = expiry_box
            row.addWidget(expiry_box)
            # Connect type_box to enable/disable expiry_box
            def update_expiry_enabled(box=expiry_box, tbox=type_box):
                box.setEnabled(tbox.currentText() == 'subscription')
            type_box.currentTextChanged.connect(update_expiry_enabled)
            update_expiry_enabled()
            features_layout.addLayout(row)
        layout.addWidget(features_box)

        self.generate_btn = QPushButton('Generate License Key')
        self.generate_btn.clicked.connect(self.generate_key_clicked)
        layout.addWidget(self.generate_btn)

        # Result area: QLineEdit for key, Copy button, and info label
        result_layout = QHBoxLayout()
        self.key_line = QLineEdit()
        self.key_line.setReadOnly(True)
        self.key_line.setPlaceholderText('License Key will appear here')
        result_layout.addWidget(self.key_line)
        self.copy_btn = QPushButton('Copy')
        self.copy_btn.clicked.connect(self.copy_key)
        result_layout.addWidget(self.copy_btn)
        layout.addLayout(result_layout)

        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

    def toggle_all_features(self, state):
        checked = state == 2
        for cb in self.feature_checks.values():
            cb.setChecked(checked)
        for tbox in self.feature_type_boxes.values():
            tbox.setCurrentText('lifetime' if checked else 'subscription')
        for ebox in self.feature_expiry_boxes.values():
            ebox.setDate(QDate.currentDate().addYears(99) if checked else QDate.currentDate().addMonths(1))
            ebox.setEnabled(not checked)

    def copy_key(self):
        key = self.key_line.text()
        if key:
            QApplication.clipboard().setText(key)

    def generate_key_clicked(self):
        user = self.name_input.text().strip()
        notes = self.notes_input.toPlainText().strip()
        features = [feat for feat, cb in self.feature_checks.items() if cb.isChecked()]
        feature_expirations = {}
        feature_types = {}
        for feat in features:
            tbox = self.feature_type_boxes[feat]
            ebox = self.feature_expiry_boxes[feat]
            t = tbox.currentText()
            feature_types[feat] = t
            if t == 'lifetime':
                feature_expirations[feat] = 'lifetime'
            else:
                feature_expirations[feat] = ebox.date().toString('yyyy-MM-dd')
        if self.select_all.isChecked():
            features = ['all_features']
            for feat in self.feature_checks:
                feature_types[feat] = 'lifetime'
                feature_expirations[feat] = 'lifetime'
        if not features:
            QMessageBox.warning(self, 'No Features Selected', 'Please select at least one feature to unlock.')
            return
        try:
            key = generate_key()
            key_hash = hash_key(key)
            add_hash_to_sheet(key_hash, features, feature_expirations, feature_types, user=user, notes=notes)
            self.key_line.setText(key)
            self.result_label.setText(f'<b>Features Unlocked:</b> {", ".join(features)}<br>'
                                     f'<b>Hash stored in sheet:</b> <code>{key_hash}</code>')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to generate or store key:\n{e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = LicenseKeyGenerator()
    win.show()
    sys.exit(app.exec()) 