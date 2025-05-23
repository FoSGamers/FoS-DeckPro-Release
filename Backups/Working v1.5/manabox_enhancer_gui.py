import pandas as pd
import requests
import time
from datetime import datetime
from tqdm import tqdm
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json
import shutil
from PIL import Image, ImageTk
import io
import threading
import logging
import traceback

# --- Constants ---
MANABOX_FIELDS = {
    "Name", "Set code", "Set name", "Collector number", "Foil", "Rarity", "Quantity",
    "ManaBox ID", "Scryfall ID", "Purchase price", "Misprint", "Altered", "Condition",
    "Language", "Purchase price currency", "type_line", "mana_cost", "colors",
    "color_identity", "oracle_text", "legal_commander", "legal_pauper", "cmc", "image_url"
}

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

CHECKBOX_FILTER_FIELDS = {
    "Foil", "Rarity", "Misprint", "Altered", "Condition", "Language", "legal_commander", "legal_pauper"
}

# --- Logging setup ---
def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    log_filename = f"logs/manabox_enhancer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.info(f"Logging initialized. Log file: {log_filename}")

# --- Main GUI Class ---
class ManaBoxEnhancerGUI:
    def __init__(self, root):
        setup_logging()
        self.root = root
        self.root.title("ManaBox Enhancer")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Load column configuration
        self.config_file = "column_config.json"
        self.column_config = self.load_column_config()
        
        # Variables
        self.input_file = None
        self.existing_json_file = None
        self.existing_data = None
        self.new_data = None
        self.merged_data = None
        self.current_page = 0
        self.cards_per_page = tk.IntVar(value=100)  # Default to 100 cards
        
        # Add price rounding configuration
        self.price_rounding_threshold = tk.DoubleVar(value=0.3)  # Default threshold
        self.price_rounding_config = {
            "threshold": 0.3,
            "round_up": True
        }
        
        # Add filter variables
        self.filter_text = tk.StringVar()
        self.filter_widgets = {}
        self.filter_values = {}
        
        # Add image preview variables
        self.preview_image = None
        self.preview_label = None
        
        self.setup_gui()
        
    def setup_gui(self):
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Status and Progress at the top
        status_progress = ttk.Frame(self.main_frame)
        status_progress.pack(fill=tk.X, pady=(0, 10))
        self.status_label = ttk.Label(status_progress, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=(0, 20))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_progress, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # File Operations
        file_ops = ttk.LabelFrame(self.main_frame, text="File Operations")
        file_ops.pack(fill=tk.X, pady=5)
        ttk.Button(file_ops, text="Load Existing JSON", command=self.load_existing_json).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(file_ops, text="Select New CSV", command=self.select_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(file_ops, text="Process New Cards", command=self.process_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(file_ops, text="Compare & Merge", command=self.compare_and_merge).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(file_ops, text="Create Backup", command=self.create_backup).pack(side=tk.LEFT, padx=5, pady=5)

        # Column Customization and Price Config side by side
        config_frame = ttk.Frame(self.main_frame)
        config_frame.pack(fill=tk.X, pady=5)
        col_custom = ttk.LabelFrame(config_frame, text="Column Customization")
        col_custom.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(col_custom, text="Customize Columns", command=self.show_column_customization).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(col_custom, text="Update Card Fields", command=self.update_card_fields).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(col_custom, text="Show/Hide Columns", command=self.show_column_visibility_dialog).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(col_custom, text="Rename Custom Field", command=self.rename_custom_field_dialog).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(col_custom, text="Add Custom Field", command=self.add_custom_field_dialog).pack(side=tk.LEFT, padx=5, pady=5)

        price_config = ttk.LabelFrame(config_frame, text="Price Configuration")
        price_config.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        ttk.Label(price_config, text="Round up threshold:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(price_config, textvariable=self.price_rounding_threshold, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(price_config, text="Update Prices", command=self.update_prices).pack(side=tk.LEFT, padx=5)
        ttk.Label(price_config, text="Cards per page:").pack(side=tk.LEFT, padx=5)
        display_count = ttk.Combobox(price_config, textvariable=self.cards_per_page, values=[50, 100, 200, 300, 400, 500], width=10)
        display_count.pack(side=tk.LEFT, padx=5)
        display_count.bind('<<ComboboxSelected>>', lambda e: self.display_cards())

        # Filters
        filter_frame = ttk.LabelFrame(self.main_frame, text="Filters")
        filter_frame.pack(fill=tk.X, pady=5)
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_text, width=40)
        filter_entry.pack(side=tk.LEFT, padx=5)
        filter_entry.bind('<KeyRelease>', lambda e: self.apply_filters())
        ttk.Button(filter_frame, text="Search", command=lambda: filter_entry.focus_set()).pack(side=tk.LEFT, padx=5)

        # --- Paned Window for Card Display and Preview ---
        paned = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left: Card Display (with filter row overlay)
        display_frame = ttk.Frame(paned)
        paned.add(display_frame, weight=4)

        # Canvas for horizontal scrolling
        self.display_canvas = tk.Canvas(display_frame, highlightthickness=0)
        self.display_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Horizontal scrollbar
        self.h_scroll = tk.Scrollbar(display_frame, orient="horizontal", command=self.display_canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.display_canvas.configure(xscrollcommand=self.h_scroll.set)

        # Frame inside canvas for filter row and table
        self.inner_frame = ttk.Frame(self.display_canvas)
        self.display_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Card table frame
        card_table_frame = ttk.Frame(self.inner_frame)
        card_table_frame.pack(fill=tk.BOTH, expand=True)

        self.card_display = ttk.Treeview(card_table_frame, show="headings")
        self.card_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scrollbar = ttk.Scrollbar(card_table_frame, orient=tk.VERTICAL, command=self.card_display.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.card_display.configure(yscrollcommand=y_scrollbar.set)

        # Sync canvas size to content
        self.inner_frame.bind("<Configure>", self._sync_canvas_width)
        self.card_display.bind("<Configure>", self._sync_canvas_width)
        self.card_display.bind('<ButtonRelease-1>', self._on_column_resize)
        self.card_display.bind('<B1-Motion>', self._on_column_resize)

        self.create_filter_row()
        self.update_card_display_columns()

        # Right: Card Preview
        preview_frame = ttk.LabelFrame(paned, text="Card Preview")
        paned.add(preview_frame, weight=1)
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(padx=10, pady=10)

        # Bind selection event
        self.card_display.bind('<<TreeviewSelect>>', self.show_card_preview)

        # Navigation and Export
        nav_export = ttk.Frame(self.main_frame)
        nav_export.pack(fill=tk.X, pady=5)
        ttk.Button(nav_export, text="Previous", command=self.previous_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_export, text="Next", command=self.next_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_export, text="Export to JSON", command=self.export_json).pack(side=tk.RIGHT, padx=5)
        ttk.Button(nav_export, text="Export to CSV", command=self.export_csv).pack(side=tk.RIGHT, padx=5)

        self.card_display.bind('<ButtonRelease-1>', self.save_column_widths_on_resize)

    def create_backup(self):
        """Create a backup of the current data"""
        if not self.merged_data and not self.new_data and not self.existing_data:
            messagebox.showerror("Error", "No data to backup")
            return

        data_to_backup = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data_to_backup:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)

        # Backup JSON
        json_filename = os.path.join(backup_dir, f"backup_{timestamp}.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data_to_backup, f, indent=2, ensure_ascii=False)

        # Backup CSV
        csv_filename = os.path.join(backup_dir, f"backup_{timestamp}.csv")
        df = pd.DataFrame(data_to_backup)
        df.to_csv(csv_filename, index=False)

        messagebox.showinfo("Success", f"Backup created:\n{json_filename}\n{csv_filename}")

    def show_card_preview(self, event):
        """Show card preview when a row is selected"""
        selection = self.card_display.selection()
        if not selection:
            return

        # Get the selected item's values
        item = self.card_display.item(selection[0])
        values = item['values']
        
        # Get the image URL from the data
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data:
            return

        # Find the card in the data
        card = None
        for c in data:
            if all(str(c.get(col["id"], "")) == str(val) for col, val in zip(self.column_config["columns"], values)):
                card = c
                break

        if not card or "image_url" not in card:
            return

        try:
            # Download and display the image
            response = requests.get(card["image_url"])
            image_data = Image.open(io.BytesIO(response.content))
            
            # Resize image while maintaining aspect ratio
            max_size = (300, 300)
            image_data.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image_data)
            
            # Update preview
            self.preview_label.configure(image=photo)
            self.preview_label.image = photo  # Keep a reference
            
        except Exception as e:
            logging.error(f"Error loading card preview: {e}")
            self.preview_label.configure(image='')

    def save_column_config(self):
        """Save column configuration to file"""
        with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.column_config, f, indent=2)

    def load_column_config(self):
        """Load column configuration from file"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"columns": [col.copy() for col in DEFAULT_COLUMNS]}

    def fetch_scryfall_data(self, scryfall_id):
        """Fetch card data from Scryfall API"""
        url = f"https://api.scryfall.com/cards/{scryfall_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Get image URL
            image_url = ""
            if "image_uris" in data:
                image_url = data["image_uris"].get("normal", "")
            elif "card_faces" in data and len(data["card_faces"]) > 0:
                image_url = data["card_faces"][0]["image_uris"].get("normal", "")
            
            # Create card data with fields in the specified order
            card_data = {
                "Name": data.get("name", ""),
                "Set code": data.get("set", ""),
                "Set name": data.get("set_name", ""),
                "Collector number": data.get("collector_number", ""),
                "Foil": "normal",
                "Rarity": data.get("rarity", ""),
                "Quantity": 1,
                "ManaBox ID": "",
                "Scryfall ID": scryfall_id,
                "Purchase price": 0.0,
                "Misprint": False,
                "Altered": False,
                "Condition": "near_mint",
                "Language": "en",
                "Purchase price currency": "USD",
                "type_line": data.get("type_line", ""),
                "mana_cost": data.get("mana_cost", ""),
                "colors": ", ".join(data.get("colors", [])),
                "color_identity": ", ".join(data.get("color_identity", [])),
                "oracle_text": data.get("oracle_text", ""),
                "legal_commander": data.get("legalities", {}).get("commander", "unknown"),
                "legal_pauper": data.get("legalities", {}).get("pauper", "unknown"),
                "cmc": data.get("cmc", 0),
                "image_url": image_url
            }
            
            return card_data
            
        except Exception as e:
            logging.error(f"Error fetching {scryfall_id}: {e}")
            return {
                "Name": "ERROR",
                "Set code": "",
                "Set name": "",
                "Collector number": "",
                "Foil": "normal",
                "Rarity": "",
                "Quantity": 0,
                "ManaBox ID": "",
                "Scryfall ID": scryfall_id,
                "Purchase price": 0.0,
                "Misprint": False,
                "Altered": False,
                "Condition": "near_mint",
                "Language": "en",
                "Purchase price currency": "USD",
                "type_line": "ERROR",
                "mana_cost": "",
                "colors": "",
                "color_identity": "",
                "oracle_text": "",
                "legal_commander": "unknown",
                "legal_pauper": "unknown",
                "cmc": 0,
                "image_url": ""
            }

    def update_prices(self):
        """Update prices with rounding based on threshold"""
        if not self.merged_data and not self.new_data and not self.existing_data:
            messagebox.showerror("Error", "No data to update prices")
            return

        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        threshold = self.price_rounding_threshold.get()
        logging.info(f"Starting price updates with threshold: {threshold}")

        updated_count = 0
        for card in data:
            if "Purchase price" in card:
                try:
                    # Handle both string and float price formats
                    price_str = str(card["Purchase price"]).replace("$", "").strip()
                    price = float(price_str)
                    decimal_part = price - int(price)

                    if decimal_part >= threshold:
                        rounded_price = int(price) + 1
                    else:
                        rounded_price = int(price)

                    # Ensure minimum Whatnot price is $1
                    if rounded_price < 1:
                        rounded_price = 1

                    card["Purchase price"] = f"${price:.2f}"
                    card["Whatnot price"] = f"${rounded_price}"
                    updated_count += 1
                    logging.debug(f"Updated prices for {card.get('Name', '')}: Original=${price:.2f}, Whatnot=${rounded_price}")
                except Exception as e:
                    logging.error(f"Error updating price for {card.get('Name', '')}: {e}")

        # Ensure "Whatnot price" column is in config and visible
        found = False
        for col in self.column_config["columns"]:
            if col["id"] == "Whatnot price":
                col["visible"] = True
                found = True
                break
        if not found:
            self.column_config["columns"].insert(
                [col["id"] for col in self.column_config["columns"]].index("Purchase price") + 1,
                {"id": "Whatnot price", "display": "Whatnot Price", "width": 100, "visible": True}
            )
        self.save_column_config()
        self.update_card_display_columns(data)
        self.display_cards()
        messagebox.showinfo("Success", f"Updated prices for {updated_count} cards")

    def apply_filters(self):
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data:
            self.display_filtered_cards([])
            return
        visible_cols = [col for col in self.column_config["columns"] if col.get("visible", True)]
        filtered_data = []
        filter_text = self.filter_text.get().lower()
        for card in data:
            match = True
            if filter_text:
                if not any(filter_text in str(card.get(col["id"], "")).lower() for col in visible_cols):
                    continue
            for col in visible_cols:
                col_id = col["id"]
                filter_value = self.filter_values.get(col_id)
                card_value = str(card.get(col_id, ""))
                if col_id in CHECKBOX_FILTER_FIELDS:
                    if filter_value and card_value not in filter_value:
                        match = False
                        break
                else:
                    if filter_value and filter_value.lower() not in card_value.lower():
                        match = False
                        break
            if match:
                filtered_data.append(card)
        self.filtered_data = filtered_data
        self.current_page = 0
        self.display_filtered_cards(filtered_data)

    def display_filtered_cards(self, filtered_data):
        for item in self.card_display.get_children():
            self.card_display.delete(item)
        per_page = self.cards_per_page.get() if hasattr(self, "cards_per_page") else 100
        start_idx = self.current_page * per_page
        end_idx = min(start_idx + per_page, len(filtered_data))
        for card in filtered_data[start_idx:end_idx]:
            values = [card.get(col["id"], "") for col in self.column_config["columns"] if col.get("visible", True)]
            self.card_display.insert("", "end", values=values)

    def compare_and_merge(self):
        """Compare and merge existing and new data"""
        if not self.existing_data or not self.new_data:
            messagebox.showerror("Error", "Both existing JSON and new data are required")
            return
            
        self.merged_data = []
        existing_dict = {card["Name"]: card for card in self.existing_data}
        
        # Process new cards in their original order
        for new_card in self.new_data:
            if new_card["Name"] in existing_dict:
                # Update existing card
                existing_card = existing_dict[new_card["Name"]]
                existing_card["Quantity"] = new_card["Quantity"]
                # Preserve the original order from the new data
                existing_card['_original_order'] = new_card['_original_order']
                self.merged_data.append(existing_card)
            else:
                # Add new card
                self.merged_data.append(new_card)
        
        # Sort by original order
        self.merged_data.sort(key=lambda x: x['_original_order'])
        
        self.display_cards()
        self.status_label.config(text="Merge complete!")

    def display_cards(self):
        """Display cards in the treeview, applying all filters and pagination."""
        # Clear current display
        for item in self.card_display.get_children():
            self.card_display.delete(item)

        # Determine which data to display
        display_data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not display_data:
            return

        # Apply global and per-column filters
        visible_cols = [col for col in self.column_config["columns"] if col.get("visible", True)]
        filter_text = self.filter_text.get().lower()
        filtered_data = []
        for card in display_data:
            match = True
            # Global search
            if filter_text:
                if not any(filter_text in str(card.get(col["id"], "")).lower() for col in visible_cols):
                    continue
            # Per-column filters
            for col in visible_cols:
                col_id = col["id"]
                filter_value = self.filter_values.get(col_id)
                card_value = str(card.get(col_id, ""))
                if col_id in CHECKBOX_FILTER_FIELDS:
                    if filter_value and card_value not in filter_value:
                        match = False
                        break
                else:
                    if filter_value and filter_value.lower() not in card_value.lower():
                        match = False
                        break
            if match:
                filtered_data.append(card)

        # Pagination
        start_idx = self.current_page * self.cards_per_page.get()
        end_idx = min(start_idx + self.cards_per_page.get(), len(filtered_data))

        # Insert rows
        for card in filtered_data[start_idx:end_idx]:
            values = [card.get(col["id"], "") for col in visible_cols]
            self.card_display.insert("", "end", values=values)

    def next_page(self):
        if (self.current_page + 1) * self.cards_per_page.get() < len(self.filtered_data):
            self.current_page += 1
            self.display_filtered_cards(self.filtered_data)

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_filtered_cards(self.filtered_data)

    def export_json(self):
        """Export data to JSON file"""
        data_to_export = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data_to_export:
            messagebox.showerror("Error", "No data to export")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_export, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", "JSON file exported successfully")
    
    def export_csv(self):
        """Export data to CSV file"""
        data_to_export = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data_to_export:
            messagebox.showerror("Error", "No data to export")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if filename:
            # Create DataFrame with columns in the configured order
            df = pd.DataFrame(data_to_export)
            # Reorder columns according to configuration
            visible_columns = [col["id"] for col in self.column_config["columns"] if col.get("visible", True)]
            # Only include columns that exist in the data
            existing_columns = [col for col in visible_columns if col in df.columns]
            df = df[existing_columns]
            # Rename columns according to configuration
            column_rename = {col["id"]: col["display"] for col in self.column_config["columns"]}
            df = df.rename(columns=column_rename)
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", "CSV file exported successfully")

    def update_card_display_columns(self, data=None):
        """Update the card display columns based on configuration and allow resizing."""
        if not data:
            data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data:
            return
        visible_cols = [col for col in self.column_config["columns"] if col.get("visible", True)]
        col_ids = [col["id"] for col in visible_cols]
        self.card_display["columns"] = col_ids
        for col in visible_cols:
            self.card_display.heading(col["id"], text=col["display"])
            width = col.get("width", 100)
            # Allow all columns to be resizable
            self.card_display.column(col["id"], width=width, minwidth=50, stretch=True)
        # After updating columns, also update the filter row overlay
        self.create_filter_row()

    def ensure_consistent_fields(self, data):
        """Ensure all cards have the same fields"""
        if not data:
            return data
        
        # Get all unique keys from all cards
        all_keys = set()
        for card in data:
            all_keys.update(card.keys())
        
        # Update each card to include all fields
        for card in data:
            for key in all_keys:
                if key not in card:
                    card[key] = ""  # Default empty value for missing fields
        
        return data

    def show_column_customization(self):
        """Show column customization dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Customize Columns")
        dialog.geometry("600x400")

        # Create listbox for columns
        listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add columns to listbox
        for col in self.column_config["columns"]:
            listbox.insert(tk.END, f"{col['display']} ({col['id']})")

        # Create buttons frame
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Add buttons
        ttk.Button(btn_frame, text="Move Up", 
                  command=lambda: self.move_column(listbox, -1)).pack(pady=5)
        ttk.Button(btn_frame, text="Move Down", 
                  command=lambda: self.move_column(listbox, 1)).pack(pady=5)
        ttk.Button(btn_frame, text="Rename", 
                  command=lambda: self.rename_column(listbox)).pack(pady=5)
        ttk.Button(btn_frame, text="Save", 
                  command=lambda: self.save_column_changes(dialog)).pack(pady=5)

    def move_column(self, listbox, direction):
        """Move selected column up or down"""
        selection = listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        new_index = index + direction
        
        if 0 <= new_index < listbox.size():
            # Move in listbox
            item = listbox.get(index)
            listbox.delete(index)
            listbox.insert(new_index, item)
            
            # Move in configuration
            col = self.column_config["columns"].pop(index)
            self.column_config["columns"].insert(new_index, col)
            
            listbox.selection_set(new_index)

    def rename_column(self, listbox):
        """Rename selected column"""
        selection = listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        col = self.column_config["columns"][index]
        
        # Create rename dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Rename Column")
        dialog.geometry("300x100")
        
        ttk.Label(dialog, text="New display name:").pack(pady=5)
        entry = ttk.Entry(dialog)
        entry.insert(0, col["display"])
        entry.pack(pady=5)
        
        def save_rename():
            col["display"] = entry.get()
            listbox.delete(index)
            listbox.insert(index, f"{col['display']} ({col['id']})")
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save_rename).pack(pady=5)

    def save_column_changes(self, dialog):
        """Save column configuration changes"""
        self.save_column_config()
        self.update_card_display_columns(self.merged_data if self.merged_data else 
                                       (self.new_data if self.new_data else self.existing_data))
        dialog.destroy()

    def update_card_fields(self):
        """Update all new or empty fields for all cards"""
        if not self.merged_data and not self.new_data and not self.existing_data:
            logging.warning("No data to update")
            messagebox.showerror("Error", "No data to update")
            return
        
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        logging.info(f"Starting card field updates for {len(data)} cards")
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Updating Card Fields")
        progress_window.geometry("300x150")
        
        # Add progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(pady=10, padx=10, fill=tk.X)
        
        # Add status label
        status_label = ttk.Label(progress_window, text="Starting update...")
        status_label.pack(pady=5)
        
        # Add cancel button
        cancel_var = tk.BooleanVar(value=False)
        def cancel_update():
            cancel_var.set(True)
            logging.info("Update cancelled by user")
            progress_window.destroy()
        
        cancel_button = ttk.Button(progress_window, text="Cancel", command=cancel_update)
        cancel_button.pack(pady=5)
        
        def update_process():
            total_cards = len(data)
            updated_count = 0
            error_count = 0
            
            for i, card in enumerate(data):
                if cancel_var.get():
                    break
                    
                try:
                    if "Scryfall ID" in card:
                        logging.debug(f"Updating card {i+1}/{total_cards}: {card['Name']}")
                        url = f"https://api.scryfall.com/cards/{card['Scryfall ID']}"
                        response = requests.get(url)
                        response.raise_for_status()
                        scryfall_data = response.json()
                        
                        # Update fields
                        card["cmc"] = scryfall_data.get("cmc", 0)
                        logging.debug(f"Updated CMC for {card['Name']}: {card['cmc']}")
                        
                        # Update other fields
                        for field in ["type_line", "mana_cost", "colors", "color_identity", 
                                    "oracle_text", "legal_commander", "legal_pauper"]:
                            if field not in card or not card[field]:
                                if field == "colors":
                                    card[field] = ", ".join(scryfall_data.get("colors", []))
                                elif field == "color_identity":
                                    card[field] = ", ".join(scryfall_data.get("color_identity", []))
                                elif field in ["legal_commander", "legal_pauper"]:
                                    card[field] = scryfall_data.get("legalities", {}).get(field.split("_")[1], "unknown")
                                else:
                                    card[field] = scryfall_data.get(field, "")
                                logging.debug(f"Updated {field} for {card['Name']}: {card[field]}")
                        
                        updated_count += 1
                        
                    # Update progress
                    progress = (i + 1) / total_cards * 100
                    progress_var.set(progress)
                    status_label.config(text=f"Updating card {i+1} of {total_cards}: {card['Name']}")
                    progress_window.update()
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    error_count += 1
                    logging.error(f"Error updating {card['Name']}: {str(e)}")
                    logging.error(traceback.format_exc())
            
            logging.info(f"Update complete. Updated {updated_count} cards. Errors: {error_count}")
            if not cancel_var.get():
                self.display_cards()
                messagebox.showinfo("Success", f"Card fields updated successfully\nUpdated: {updated_count}\nErrors: {error_count}")
            progress_window.destroy()
        
        # Start update process in a separate thread
        threading.Thread(target=update_process, daemon=True).start()

    def show_advanced_filters(self):
        """Show advanced filter dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Advanced Filters")
        dialog.geometry("400x600")  # Made taller to show more filters
        
        # Create filter options for each column
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data:
            return
            
        # Get unique values for each column
        column_values = {}
        for card in data:
            for key, value in card.items():
                if key not in column_values:
                    column_values[key] = set()
                # Convert value to string and add to set
                column_values[key].add(str(value))
        
        # Create a scrollable frame for filters
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create filter checkboxes
        filter_vars = {}
        for col in self.column_config["columns"]:
            if col["id"] in column_values and col.get("visible", True):
                frame = ttk.LabelFrame(scrollable_frame, text=col["display"])
                frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Add select all/none buttons
                btn_frame = ttk.Frame(frame)
                btn_frame.pack(fill=tk.X)
                ttk.Button(btn_frame, text="All", 
                          command=lambda c=col["id"]: self.toggle_all_filters(c, True)).pack(side=tk.LEFT)
                ttk.Button(btn_frame, text="None", 
                          command=lambda c=col["id"]: self.toggle_all_filters(c, False)).pack(side=tk.LEFT)
                
                # Add checkboxes for values
                for value in sorted(column_values[col["id"]]):
                    var = tk.BooleanVar(value=False)
                    filter_vars[f"{col['id']}_{value}"] = var
                    ttk.Checkbutton(frame, text=value, variable=var).pack(anchor=tk.W)
        
        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add apply and clear buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Apply Filters", 
                  command=lambda: self.apply_advanced_filters(filter_vars, dialog)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", 
                  command=lambda: self.clear_all_filters(filter_vars)).pack(side=tk.LEFT, padx=5)

    def toggle_all_filters(self, column, value):
        """Toggle all filters for a column"""
        for key, var in self.filter_widgets.items():
            if key.startswith(f"{column}_"):
                var.set(value)

    def apply_advanced_filters(self, filter_vars, dialog):
        """Apply advanced filters"""
        self.filter_widgets = filter_vars
        self.display_cards()
        dialog.destroy()

    def clear_all_filters(self, filter_vars):
        """Clear all filter checkboxes"""
        for var in filter_vars.values():
            var.set(False)

    def save_column_widths_on_resize(self, event=None):
        """Save current column widths to config"""
        for col in self.column_config["columns"]:
            col_id = col["id"]
            width = self.card_display.column(col_id, option='width')
            col["width"] = width
        self.save_column_config()

    def show_column_visibility_dialog(self):
        """Show dialog to toggle column visibility"""
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
            self.update_card_display_columns(self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data))
            self.display_cards()
            dialog.destroy()
        ttk.Button(dialog, text="Save", command=save_and_close).pack(pady=10)

    def rename_custom_field_dialog(self):
        """Show dialog to rename a custom field"""
        # Only allow renaming of custom fields
        custom_fields = [col for col in self.column_config["columns"] if col["id"] not in MANABOX_FIELDS]
        if not custom_fields:
            messagebox.showinfo("Rename Field", "No custom fields to rename.")
            return
        field_names = [col["display"] for col in custom_fields]
        idx = simpledialog.askinteger("Rename Field", f"Select field to rename (1-{len(field_names)}):\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(field_names)))
        if not idx or not (1 <= idx <= len(field_names)):
            return
        old_col = custom_fields[idx-1]
        new_id = simpledialog.askstring("Rename Field", "Enter new field name (no spaces):", initialvalue=old_col["id"])
        if not new_id or new_id in MANABOX_FIELDS:
            messagebox.showerror("Error", "Invalid or duplicate field name.")
            return
        new_display = simpledialog.askstring("Rename Field", "Enter new display name:", initialvalue=old_col["display"])
        if not new_display:
            new_display = new_id.replace("_", " ").title()
        self.rename_field(old_col["id"], new_id, new_display)

    def rename_field(self, old_id, new_id, new_display):
        """Rename a field in the configuration and data"""
        for col in self.column_config["columns"]:
            if col["id"] == old_id:
                col["id"] = new_id
                col["display"] = new_display
                break
        for card in self.existing_data:
            if old_id in card:
                card[new_id] = card.pop(old_id)
            else:
                card[new_id] = ""
        self.save_column_config()
        self.update_card_display_columns()
        self.display_cards()

    def add_custom_field_dialog(self):
        """Show dialog to add a new custom field"""
        field_id = simpledialog.askstring("Add Custom Field", "Enter new field name (no spaces):")
        if not field_id or field_id in MANABOX_FIELDS:
            messagebox.showerror("Error", "Invalid or duplicate field name.")
            return
        display_name = simpledialog.askstring("Add Custom Field", "Enter display name for the new field:")
        if not display_name:
            display_name = field_id.replace("_", " ").title()
        self.add_new_field(field_id, display_name)

    def add_new_field(self, field_id, display_name):
        """Add a new field to the configuration and data"""
        self.column_config["columns"].append({
            "id": field_id,
            "display": display_name,
            "width": 120,
            "visible": True
        })
        for card in self.existing_data:
            card[field_id] = ""
        self.save_column_config()
        self.update_card_display_columns()
        self.display_cards()

    def select_and_load_json(self):
        print("Opening file dialog for JSON...")
        filename = filedialog.askopenfilename(
            title="Select JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        print(f"File selected: {filename}")
        if filename:
            self.load_existing_json(filename)
        else:
            print("No file selected.")
            messagebox.showinfo("No file selected", "Please select a JSON file to load.")

    def load_existing_json(self):
        """Load existing JSON file"""
        self.existing_json_file = filedialog.askopenfilename(
            title="Select existing JSON file",
            filetypes=[("JSON files", "*.json")]
        )
        if self.existing_json_file:
            try:
                logging.info(f"Attempting to load JSON file: {self.existing_json_file}")
                with open(self.existing_json_file, 'r', encoding='utf-8') as f:
                    raw_data = f.read()
                    logging.debug(f"Raw JSON data length: {len(raw_data)} characters")
                    logging.debug(f"First 100 characters of JSON: {raw_data[:100]}")
                    self.existing_data = json.loads(raw_data)
                    if not isinstance(self.existing_data, list):
                        raise ValueError("JSON data must be a list of cards")
                    logging.info(f"Successfully loaded {len(self.existing_data)} cards")
                    if self.existing_data:
                        logging.debug(f"First card structure: {json.dumps(self.existing_data[0], indent=2)}")
                    self.status_label.config(text=f"Loaded existing JSON: {os.path.basename(self.existing_json_file)}")
                    self.update_card_display_columns(self.existing_data)
                    self.display_cards()
            except Exception as e:
                error_msg = f"Unexpected error loading JSON file: {str(e)}"
                logging.error(error_msg)
                logging.error(f"Full error details: {e.__class__.__name__}")
                logging.error(traceback.format_exc())
                messagebox.showerror("Error", error_msg)

    def setup_after_data_load(self):
        print("Setting up display after data load...")
        self.update_card_display_columns()
        self.create_filter_row()
        self.apply_filters()

    def select_file(self):
        """Select a new CSV file to process"""
        self.input_file = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if self.input_file:
            self.status_label.config(text=f"Selected file: {os.path.basename(self.input_file)}")
            logging.info(f"Selected file: {self.input_file}")

    def process_file(self):
        """Process the selected CSV file"""
        if not self.input_file:
            messagebox.showerror("Error", "Please select a file first")
            return
            
        # Start processing in a separate thread
        threading.Thread(target=self._process_file_thread, daemon=True).start()
    
    def _process_file_thread(self):
        """Thread function for processing the CSV file"""
        try:
            self.status_label.config(text="Loading file...")
            df = pd.read_csv(self.input_file)
            
            self.status_label.config(text="Processing cards...")
            self.new_data = []
            
            for i, (_, row) in enumerate(df.iterrows()):
                try:
                    scryfall_id = row["Scryfall ID"]
                    card_data = self.fetch_scryfall_data(scryfall_id)
                    # Add quantity from the CSV
                    card_data["Quantity"] = row.get("Quantity", 1)
                    # Store the original order
                    card_data['_original_order'] = i
                    self.new_data.append(card_data)
                    
                    # Update progress
                    progress = (i + 1) / len(df) * 100
                    self.progress_var.set(progress)
                    self.status_label.config(text=f"Processing card {i+1} of {len(df)}")
                    
                except Exception as e:
                    logging.error(f"Error processing card {i+1}: {e}")
                
                time.sleep(0.1)  # Rate limiting
            
            self.display_cards()
            self.status_label.config(text="Processing complete!")
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logging.error(error_msg)
            logging.error(traceback.format_exc())
            messagebox.showerror("Error", error_msg)

    def create_filter_row(self):
        """Create a filter row above the table, always in sync with visible columns."""
        # Remove any existing filter row overlay
        if hasattr(self, 'filter_overlay'):
            self.filter_overlay.destroy()
        self.filter_widgets.clear()
        self.filter_values.clear()

        # Overlay frame on top of the Treeview header
        self.filter_overlay = tk.Frame(self.card_display, bg="", height=24)
        self.filter_overlay.place(x=0, y=0, relwidth=1, height=24)

        visible_cols = [col for col in self.column_config["columns"] if col.get("visible", True)]
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        unique_values = {}
        if data:
            for col in visible_cols:
                col_id = col["id"]
                unique_values[col_id] = sorted({str(card.get(col_id, "")) for card in data})

        for idx, col in enumerate(visible_cols):
            col_id = col["id"]
            if col_id in CHECKBOX_FILTER_FIELDS:
                btn = ttk.Button(
                    self.filter_overlay,
                    text=f"Filter: {col['display']}",
                    width=10,
                    command=lambda c=col_id: self.open_checkbox_filter_popup(c)
                )
                self.filter_widgets[col_id] = btn
                self.filter_values.setdefault(col_id, set())
            else:
                var = tk.StringVar()
                entry = ttk.Entry(self.filter_overlay, textvariable=var)
                entry.bind("<KeyRelease>", lambda e, c=col_id, v=var: self.on_text_filter_change(c, v))
                self.filter_widgets[col_id] = entry
                self.filter_values.setdefault(col_id, "")

        self._resize_filter_row_widgets()

    def open_checkbox_filter_popup(self, col_id):
        """Popup with checkboxes for all unique values in the column, from the entire database."""
        popup = tk.Toplevel(self.root)
        popup.title(f"Filter: {col_id}")
        popup.transient(self.root)
        popup.grab_set()
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        values = sorted({str(card.get(col_id, "")) for card in data})
        canvas = tk.Canvas(popup)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        var_dict = {}
        for val in values:
            var = tk.BooleanVar(value=val in self.filter_values.get(col_id, set()))
            cb = ttk.Checkbutton(scrollable_frame, text=val if val else "(blank)", variable=var)
            cb.pack(anchor=tk.W, padx=5, pady=2)
            var_dict[val] = var
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="All", command=lambda: self.toggle_all_checkboxes(var_dict, True)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="None", command=lambda: self.toggle_all_checkboxes(var_dict, False)).pack(side=tk.LEFT, padx=5)
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        btn_frame2 = ttk.Frame(popup)
        btn_frame2.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame2, text="Apply", command=lambda: self.apply_checkbox_filter(col_id, var_dict, popup)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Cancel", command=popup.destroy).pack(side=tk.LEFT, padx=5)

    def toggle_all_checkboxes(self, var_dict, value):
        for var in var_dict.values():
            var.set(value)

    def apply_checkbox_filter(self, col_id, var_dict, popup):
        selected = {val for val, var in var_dict.items() if var.get()}
        self.filter_values[col_id] = selected
        popup.destroy()
        self.current_page = 0
        self.apply_filters()

    def on_text_filter_change(self, col_id, var):
        self.filter_values[col_id] = var.get()
        self.current_page = 0
        self.apply_filters()

    def _sync_canvas_width(self, event=None):
        self.display_canvas.configure(scrollregion=self.display_canvas.bbox("all"))
        tree_width = self.card_display.winfo_reqwidth()
        self.display_canvas.itemconfig(self.display_canvas.find_withtag("all")[0], width=tree_width)
        self._resize_filter_row_widgets()

    def _on_column_resize(self, event=None):
        self._resize_filter_row_widgets()

    def _resize_filter_row_widgets(self):
        """Resize and place filter widgets to match Treeview columns exactly, without blocking header events."""
        if not hasattr(self, 'filter_overlay'):
            return
        visible_cols = [col for col in self.column_config["columns"] if col.get("visible", True)]
        x = 0
        for idx, col in enumerate(visible_cols):
            col_id = col["id"]
            try:
                col_width = self.card_display.column(col_id, option="width")
            except tk.TclError:
                continue
            widget = self.filter_widgets.get(col_id)
            if widget:
                widget.place(x=x, y=0, width=col_width, height=24)
            x += col_width
        self.filter_overlay.config(width=x)
        self.filter_overlay.lift()  # Raise to update, then lower to allow header interaction
        self.filter_overlay.lower()  # Lower within its parent so Treeview header is interactive

def main():
    root = tk.Tk()
    app = ManaBoxEnhancerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 