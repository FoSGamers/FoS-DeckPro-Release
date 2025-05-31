import json
import os
import re

def normalize(name):
    # Lowercase, remove apostrophes and punctuation, strip spaces
    return re.sub(r"[^a-z0-9 ]", "", name.lower())

# Load inventory
inv_file = 'models/inventory.json' if os.path.exists('models/inventory.json') else 'buyers.json'
with open(inv_file, encoding='utf-8') as f:
    inv = json.load(f)

names = set(c['Name'].strip() for c in inv if 'Name' in c)
normalized_names = {normalize(n): n for n in names}

missing_list = [
    'Cryptolith Rite','Jacob Frye','Deadly Cover-Up','Deification','Diamond Lion',
    'Eliminate','Evolving Wilds','Legacy Weapon','Chef\'s Kiss','Witch\'s Oven','barn_ez'
]

for missing in missing_list:
    norm_missing = normalize(missing)
    print(f'Checking: {missing}')
    found = [orig for norm, orig in normalized_names.items() if norm_missing in norm]
    if found:
        print('  Found:', found)
    else:
        print('  Not found') 