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

# CONFIGURATION
BACKUP_FOLDER = "enrichment_backups"
RATE_LIMIT_SECONDS = 0.1

def create_backup(script_name):
    """Create backup of the script"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_script_name = f"manabox_enhancer_{timestamp}.py"
    
    # Make sure backup folder exists
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    
    # Create backup of the script
    shutil.copy2(script_name, os.path.join(BACKUP_FOLDER, backup_script_name))
    print(f"Created script backup: {backup_script_name}")
    return timestamp

def fetch_scryfall_data(scryfall_id):
    """Fetch card data from Scryfall API"""
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

def main():
    # Create backup of the script
    timestamp = create_backup("manabox_enhancer.py")
    
    # Create and hide the root window
    root = tk.Tk()
    root.withdraw()
    
    # Show file selection dialog
    print("Please select your input CSV file...")
    input_file = filedialog.askopenfilename(
        title="Select CSV file",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not input_file:
        print("No file selected. Exiting...")
        return
    
    # Create backup of input file
    backup_filename = f"working_backup_{timestamp}.csv"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)
    shutil.copy2(input_file, backup_path)
    print(f"Created initial backup: {backup_path}")
    
    # Load the original CSV
    print(f"Loading file: {input_file}")
    df = pd.read_csv(input_file)
    
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
    
    # Save output files
    output_base = f"enriched_full_output_{timestamp}"
    json_filename = f"{output_base}.json"
    csv_filename = f"{output_base}.csv"
    
    # Save JSON file
    json_data = enriched_df.to_dict(orient='records')
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Save CSV file
    enriched_df.to_csv(csv_filename, index=False)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Enrichment complete!")
    print(f"📁 JSON file saved to: {json_filename}")
    print(f"📁 CSV file saved to: {csv_filename}")
    print(f"🕒 Total time: {elapsed:.1f} seconds ({elapsed/60:.2f} minutes)")

if __name__ == "__main__":
    main()
