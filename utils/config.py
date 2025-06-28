import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'last_file.txt')

# --- Centralized Error Reporting Config ---
# Set to True to enable anonymous error reporting (opt-in, privacy-respecting)
ERROR_REPORTING_ENABLED = False
# Endpoint for error reports (leave blank to disable)
ERROR_REPORTING_ENDPOINT = ''
# App version for error reporting and diagnostics
APP_VERSION = '1.0.0'

def save_last_file(path):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(path)
    except Exception:
        pass

def load_last_file():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return None
