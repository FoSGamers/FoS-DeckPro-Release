import os
import sys
import hashlib
import time
from pathlib import Path
from bs4 import BeautifulSoup
from system_database import system_db

DIST_DIR = Path(__file__).parent.parent / 'cursor-extension' / 'dist'
HTML_PATH = DIST_DIR / 'index.html'

REQUIRED_BUNDLES = ['main.bundle.js', '885.bundle.js']

def hash_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def audit_html():
    if not HTML_PATH.exists():
        print(f'[POST-BUILD AUDIT] index.html not found at {HTML_PATH}')
        sys.exit(1)
    with open(HTML_PATH, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    scripts = [s['src'] for s in soup.find_all('script', src=True)]
    missing = [b for b in REQUIRED_BUNDLES if b not in scripts]
    audit_result = {
        'timestamp': time.time(),
        'bundles': {},
        'missing': missing,
        'status': 'success' if not missing else 'failure'
    }
    for bundle in REQUIRED_BUNDLES:
        bundle_path = DIST_DIR / bundle
        if bundle_path.exists():
            audit_result['bundles'][bundle] = hash_file(bundle_path)
        else:
            audit_result['bundles'][bundle] = None
    # Log to DB
    system_db.register_build_audit(audit_result)
    if missing:
        print(f'[POST-BUILD AUDIT] Missing script tags: {missing}')
        sys.exit(2)
    print('[POST-BUILD AUDIT] All required script tags present.')
    sys.exit(0)

if __name__ == '__main__':
    audit_html() 