import pandas as pd
import requests
import time
from datetime import datetime
from tqdm import tqdm
import os
import tkinter as tk
from tkinter import filedialog
import json
import shutil

# Create backup of the script itself
script_name = "manabox_enhancer.py"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_script_name = f"manabox_enhancer_{timestamp}.py"

# Make sure backup folder exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# Create backup of the script
shutil.copy2(script_name, os.path.join(BACKUP_FOLDER, backup_script_name))
print(f"Created script backup: {backup_script_name}")

# CONFIGURATION
BACKUP_FOLDER = "enrichment_backups"
RATE_LIMIT_SECONDS = 0.1

# Create and hide the root window
root = tk.Tk()
root.withdraw()

# Show file selection dialog
print("Please select your input CSV file...")
INPUT_FILE = filedialog.askopenfilename(
    title="Select CSV file",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

if not INPUT_FILE:
    print("No file selected. Exiting...")
    exit()

# Create timestamp for backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_filename = f"working_backup_{timestamp}.csv"
backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

# Make sure backup folder exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# Create initial backup of input file
shutil.copy2(INPUT_FILE, backup_path)
print(f"Created initial backup: {backup_path}")

# Load the original CSV
print(f"Loading file: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

# Function to call Scryfall API
def fetch_scryfall_data(scryfall_id):
    url = f"https://api.scryfall.com/cards/{scryfall_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Get the image URL from the card data
        image_url = ""
        if "image_uris" in data:
            image_url = data["image_uris"].get("normal", "")
        elif "card_faces" in data and len(data["card_faces"]) > 0:
            # Handle double-faced cards
            image_url = data["card_faces"][0]["image_uris"].get("normal", "")
            
        return {
            "type_line": data.get("type_line", ""),
            "mana_cost": data.get("mana_cost", ""),
            "colors": ", ".join(data.get("colors", [])),
            "color_identity": ", ".join(data.get("color_identity", [])),
            "oracle_text": data.get("oracle_text", ""),
            "legal_commander": data.get("legalities", {}).get("commander", "unknown"),
            "legal_pauper": data.get("legalities", {}).get("pauper", "unknown"),
            "image_url": image_url
        }
    except Exception as e:
        print(f"❌ Error fetching {scryfall_id}: {e}")
        return {
            "type_line": "ERROR",
            "mana_cost": "",
            "colors": "",
            "color_identity": "",
            "oracle_text": "",
            "legal_commander": "unknown",
            "legal_pauper": "unknown",
            "image_url": ""
        }

# Begin enrichment
print(f"\n🚀 Starting Scryfall enrichment for {len(df)} cards...\n")
start_time = time.time()
enriched_data = []

for i, (_, row) in enumerate(tqdm(df.iterrows(), total=len(df))):
    try:
        scryfall_id = row["Scryfall ID"]
        card_data = fetch_scryfall_data(scryfall_id)
    except KeyError as e:
        print(f"❌ Row {i+1} missing Scryfall ID: {e}")
        card_data = {
            "type_line": "ERROR",
            "mana_cost": "",
            "colors": "",
            "color_identity": "",
            "oracle_text": "",
            "legal_commander": "unknown",
            "legal_pauper": "unknown",
            "image_url": ""
        }

    enriched_data.append(card_data)

    # Save every 100 cards
    if (i + 1) % 100 == 0:
        temp_df = pd.concat([df.iloc[:i+1], pd.DataFrame(enriched_data)], axis=1)
        temp_filename = os.path.join(BACKUP_FOLDER, f"partial_{i+1}_cards.csv")
        temp_df.to_csv(temp_filename, index=False)
        print(f"🔒 Backup saved: {temp_filename}")

    time.sleep(RATE_LIMIT_SECONDS)

# Final merge
enriched_df = pd.concat([df, pd.DataFrame(enriched_data)], axis=1)

# Convert to JSON format
json_data = enriched_df.to_dict(orient='records')

# Save JSON file
json_filename = f"enriched_full_output_{timestamp}.json"
with open(json_filename, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

# Save CSV file
csv_filename = f"enriched_full_output_{timestamp}.csv"
enriched_df.to_csv(csv_filename, index=False)

elapsed = time.time() - start_time
print(f"\n✅ Enrichment complete!")
print(f"📄 JSON file saved to: {json_filename}")
print(f"📄 CSV file saved to: {csv_filename}")
print(f"🕒 Total time: {elapsed:.1f} seconds ({elapsed/60:.2f} minutes)")

def get_visible_columns(self):
    """Return a list of column configs that are currently visible, in display order."""
    return [col for col in self.column_config["columns"] if col.get("visible", True)]

def update_card_display_columns(self):
    """Update the treeview columns and headings based on the current config."""
    visible_cols = self.get_visible_columns()
    col_ids = [col["id"] for col in visible_cols]
    self.card_display["columns"] = col_ids
    for col in visible_cols:
        self.card_display.heading(col["id"], text=col["display"])
        self.card_display.column(col["id"], width=col.get("width", 100), minwidth=40, stretch=True)

def display_cards(self):
    """Display cards in the Treeview, matching the visible column order and field mapping."""
    self.card_display.delete(*self.card_display.get_children())
    visible_cols = self.get_visible_columns()
    col_ids = [col["id"] for col in visible_cols]

    # Choose which data to display
    display_data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
    if not display_data:
        return

    # Pagination
    start_idx = self.current_page * self.cards_per_page.get()
    end_idx = min(start_idx + self.cards_per_page.get(), len(display_data))

    for card in display_data[start_idx:end_idx]:
        row = []
        for col in visible_cols:
            value = card.get(col["id"], "")
            # Optional: format booleans, floats, etc.
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            row.append(value)
        self.card_display.insert("", "end", values=row)

def on_treeview_header_click(self, event):
    region = self.card_display.identify_region(event.x, event.y)
    if region == "heading":
        col = self.card_display.identify_column(event.x)
        col_index = int(col.replace("#", "")) - 1
        visible_cols = self.get_visible_columns()
        if 0 <= col_index < len(visible_cols):
            col_id = visible_cols[col_index]["id"]
            self.show_column_filter_dialog(col_id)

def show_column_filter_dialog(self, col_id):
    # Get unique values for this column
    display_data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
    values = sorted(set(str(card.get(col_id, "")) for card in display_data))
    dialog = tk.Toplevel(self.root)
    dialog.title(f"Filter: {col_id}")
    dialog.geometry("300x400")
    vars = []
    for val in values:
        var = tk.BooleanVar(value=col_id not in self.active_filters or val in self.active_filters[col_id])
        chk = ttk.Checkbutton(dialog, text=val, variable=var)
        chk.pack(anchor=tk.W)
        vars.append((val, var))
    def apply_filter():
        selected = set(val for val, var in vars if var.get())
        if selected:
            self.active_filters[col_id] = selected
        else:
            self.active_filters.pop(col_id, None)
        self.display_cards()
        dialog.destroy()
    ttk.Button(dialog, text="Apply", command=apply_filter).pack(pady=10)

def save_column_widths_on_resize(self, event=None):
    """Save the current widths of visible columns to the config."""
    visible_cols = self.get_visible_columns()
    for col in visible_cols:
        col_id = col['id']
        try:
            width = self.card_display.column(col_id, option='width')
            col['width'] = width
        except Exception as e:
            print(f"Error saving width for {col_id}: {e}")
    self.save_column_config()

ttk.Button(filter_frame, text="Search", command=self.display_cards).pack(side=tk.LEFT, padx=5)

def show_column_visibility_dialog(self):
    dialog = tk.Toplevel(self.root)
    dialog.title("Show/Hide Columns")
    dialog.geometry("300x400")
    vars = []
    for i, col in enumerate(self.column_config["columns"]):
        var = tk.BooleanVar(value=col.get("visible", True))
        chk = ttk.Checkbutton(dialog, text=col["display"], variable=var)
        chk.pack(anchor=tk.W)
        vars.append((col, var))
    def save_and_close():
        for col, var in vars:
            col["visible"] = var.get()
        self.save_column_config()
        # --- The key part: update columns and display using the new config ---
        self.update_card_display_columns()
        self.display_cards()
        dialog.destroy()
    ttk.Button(dialog, text="Save", command=save_and_close).pack(pady=10)

DEFAULT_COLUMNS = [
    {"id": "Name", "display": "Name", "width": 150, "visible": True},
    {"id": "Set code", "display": "Set code", "width": 100, "visible": True},
    {"id": "Set name", "display": "Set name", "width": 150, "visible": True},
    {"id": "Collector number", "display": "Collector number", "width": 120, "visible": True},
    {"id": "Foil", "display": "Foil", "width": 80, "visible": True},
    {"id": "Rarity", "display": "Rarity", "width": 100, "visible": True},
    {"id": "Quantity", "display": "Quantity", "width": 80, "visible": True},
    {"id": "ManaBox ID", "display": "ManaBox ID", "width": 100, "visible": True},
    {"id": "Scryfall ID", "display": "Scryfall ID", "width": 200, "visible": True},
    {"id": "Purchase price", "display": "Purchase price", "width": 100, "visible": True},
    {"id": "Misprint", "display": "Misprint", "width": 80, "visible": True},
    {"id": "Altered", "display": "Altered", "width": 80, "visible": True},
    {"id": "Condition", "display": "Condition", "width": 100, "visible": True},
    {"id": "Language", "display": "Language", "width": 80, "visible": True},
    {"id": "Purchase price currency", "display": "Purchase price currency", "width": 150, "visible": True},
    {"id": "type_line", "display": "Type", "width": 150, "visible": True},
    {"id": "mana_cost", "display": "Mana Cost", "width": 100, "visible": True},
    {"id": "colors", "display": "Colors", "width": 100, "visible": True},
    {"id": "color_identity", "display": "Color Identity", "width": 120, "visible": True},
    {"id": "oracle_text", "display": "Oracle Text", "width": 200, "visible": True},
    {"id": "legal_commander", "display": "Commander Legal", "width": 120, "visible": True},
    {"id": "legal_pauper", "display": "Pauper Legal", "width": 100, "visible": True},
    {"id": "cmc", "display": "CMC", "width": 80, "visible": True},
    {"id": "image_url", "display": "Image URL", "width": 200, "visible": True},
    {"id": "Whatnot price", "display": "Whatnot Price", "width": 100, "visible": True}
]

def get_default_column_config(self):
    return {"columns": DEFAULT_COLUMNS}
