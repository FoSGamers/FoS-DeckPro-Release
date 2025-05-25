import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'last_file.txt')

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
