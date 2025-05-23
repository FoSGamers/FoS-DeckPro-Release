import pandas as pd
import requests
import time
from datetime import datetime
from tqdm import tqdm
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import shutil
from PIL import Image, ImageTk
import io
import threading
import logging
import traceback

class ManaBoxEnhancerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ManaBox Enhancer")
        self.root.geometry("1200x800")
        
        # Setup logging
        self.setup_logging()
        
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
        self.active_filters = {}
        
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging to both file and console"""
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f'logs/manabox_enhancer_{timestamp}.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()  # This will output to terminal
            ]
        )
        
        logging.info(f"Logging initialized. Log file: {log_filename}")

    def load_column_config(self):
        """Load column configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_column_config()
        return self.get_default_column_config()

    def get_default_column_config(self):
        """Get default column configuration"""
        return {
            "columns": [
                {"id": "Name", "display": "Name", "width": 150},
                {"id": "Set code", "display": "Set code", "width": 100},
                {"id": "Set name", "display": "Set name", "width": 150},
                {"id": "Collector number", "display": "Collector number", "width": 120},
                {"id": "Foil", "display": "Foil", "width": 80},
                {"id": "Rarity", "display": "Rarity", "width": 100},
                {"id": "Quantity", "display": "Quantity", "width": 80},
                {"id": "ManaBox ID", "display": "ManaBox ID", "width": 100},
                {"id": "Scryfall ID", "display": "Scryfall ID", "width": 200},
                {"id": "Purchase price", "display": "Purchase price", "width": 100},
                {"id": "Misprint", "display": "Misprint", "width": 80},
                {"id": "Altered", "display": "Altered", "width": 80},
                {"id": "Condition", "display": "Condition", "width": 100},
                {"id": "Language", "display": "Language", "width": 80},
                {"id": "Purchase price currency", "display": "Purchase price currency", "width": 150},
                {"id": "type_line", "display": "Type", "width": 150},
                {"id": "mana_cost", "display": "Mana Cost", "width": 100},
                {"id": "colors", "display": "Colors", "width": 100},
                {"id": "color_identity", "display": "Color Identity", "width": 120},
                {"id": "oracle_text", "display": "Oracle Text", "width": 200},
                {"id": "legal_commander", "display": "Commander Legal", "width": 120},
                {"id": "legal_pauper", "display": "Pauper Legal", "width": 100},
                {"id": "cmc", "display": "CMC", "width": 80},
                {"id": "image_url", "display": "Image URL", "width": 200}
            ]
        }

    def save_column_config(self):
        """Save column configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.column_config, f, indent=2)

    def setup_gui(self):
        # Create main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)  # Make card display expandable
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Status section - MOVED TO TOP
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Status", padding="5")
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Progress section
        self.progress_frame = ttk.LabelFrame(self.main_frame, text="Progress", padding="5")
        self.progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # File selection section
        self.file_frame = ttk.LabelFrame(self.main_frame, text="File Operations", padding="5")
        self.file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(self.file_frame, text="Load Existing JSON", command=self.load_existing_json).grid(row=0, column=0, padx=5)
        ttk.Button(self.file_frame, text="Select New CSV", command=self.select_file).grid(row=0, column=1, padx=5)
        ttk.Button(self.file_frame, text="Process New Cards", command=self.process_file).grid(row=0, column=2, padx=5)
        ttk.Button(self.file_frame, text="Compare & Merge", command=self.compare_and_merge).grid(row=0, column=3, padx=5)
        
        # Column customization section
        self.customize_frame = ttk.LabelFrame(self.main_frame, text="Column Customization", padding="5")
        self.customize_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(self.customize_frame, text="Customize Columns", 
                  command=self.show_column_customization).grid(row=0, column=0, padx=5)
        ttk.Button(self.customize_frame, text="Update Card Fields", 
                  command=self.update_card_fields).grid(row=0, column=1, padx=5)
        
        # Price configuration section
        self.price_frame = ttk.LabelFrame(self.main_frame, text="Price Configuration", padding="5")
        self.price_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.price_frame, text="Round up threshold:").grid(row=0, column=0, padx=5)
        ttk.Entry(self.price_frame, textvariable=self.price_rounding_threshold, width=10).grid(row=0, column=1, padx=5)
        ttk.Button(self.price_frame, text="Update Prices", 
                  command=self.update_prices).grid(row=0, column=2, padx=5)
        
        # Display count configuration
        ttk.Label(self.price_frame, text="Cards per page:").grid(row=0, column=3, padx=5)
        display_count = ttk.Combobox(self.price_frame, textvariable=self.cards_per_page, 
                                   values=[50, 100, 200, 300, 400, 500], width=10)
        display_count.grid(row=0, column=4, padx=5)
        display_count.bind('<<ComboboxSelected>>', lambda e: self.display_cards())
        
        # Filter section
        self.filter_frame = ttk.LabelFrame(self.main_frame, text="Filters", padding="5")
        self.filter_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Add filter entry
        ttk.Label(self.filter_frame, text="Search:").grid(row=0, column=0, padx=5)
        filter_entry = ttk.Entry(self.filter_frame, textvariable=self.filter_text, width=40)
        filter_entry.grid(row=0, column=1, padx=5)
        filter_entry.bind('<KeyRelease>', lambda e: self.apply_filters())
        
        # Add filter options button
        ttk.Button(self.filter_frame, text="Advanced Filters", 
                  command=self.show_advanced_filters).grid(row=0, column=2, padx=5)
        
        # Card display section
        self.card_frame = ttk.LabelFrame(self.main_frame, text="Card Display", padding="5")
        self.card_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Create a frame for the treeview and scrollbars
        tree_frame = ttk.Frame(self.card_frame)
        tree_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Create card display area
        self.card_display = ttk.Treeview(tree_frame, show="headings")
        self.card_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.card_display.yview)
        y_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.card_display.xview)
        x_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        self.card_display.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Navigation buttons
        self.nav_frame = ttk.Frame(self.card_frame)
        self.nav_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(self.nav_frame, text="Previous", command=self.previous_page).grid(row=0, column=0, padx=5)
        ttk.Button(self.nav_frame, text="Next", command=self.next_page).grid(row=0, column=1, padx=5)
        
        # Export buttons
        self.export_frame = ttk.LabelFrame(self.main_frame, text="Export", padding="5")
        self.export_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(self.export_frame, text="Export to JSON", command=self.export_json).grid(row=0, column=0, padx=5)
        ttk.Button(self.export_frame, text="Export to CSV", command=self.export_csv).grid(row=0, column=1, padx=5)
    
    def load_existing_json(self):
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
                    self.display_cards()
                    
            except Exception as e:
                error_msg = f"Unexpected error loading JSON file: {str(e)}"
                logging.error(error_msg)
                logging.error(f"Full error details: {e.__class__.__name__}")
                logging.error(traceback.format_exc())
                messagebox.showerror("Error", error_msg)
    
    def select_file(self):
        self.input_file = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if self.input_file:
            self.status_label.config(text=f"Selected file: {os.path.basename(self.input_file)}")
    
    def process_file(self):
        if not self.input_file:
            messagebox.showerror("Error", "Please select a file first")
            return
            
        # Start processing in a separate thread
        threading.Thread(target=self._process_file_thread, daemon=True).start()
    
    def _process_file_thread(self):
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
                    print(f"Error processing card {i+1}: {e}")
                
                time.sleep(0.1)  # Rate limiting
            
            self.display_cards()
            self.status_label.config(text="Processing complete!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def compare_and_merge(self):
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
    
    def fetch_scryfall_data(self, scryfall_id):
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
                "ManaBox ID": "",  # This will be filled from the CSV
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
            print(f"Error fetching {scryfall_id}: {e}")
            # Return a card with all fields in the specified order
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
    
    def display_cards(self):
        # Clear current display
        for item in self.card_display.get_children():
            self.card_display.delete(item)
            
        # Get data to display
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if not data:
            return
        
        # Apply text filter
        filter_text = self.filter_text.get().lower()
        if filter_text:
            data = [card for card in data if any(
                filter_text in str(value).lower() 
                for value in card.values()
            )]
        
        # Apply advanced filters
        if self.active_filters:
            filtered_data = []
            for card in data:
                include_card = True
                for key, var in self.active_filters.items():
                    if var.get():
                        column, value = key.split('_', 1)
                        if str(card.get(column, "")) != value:
                            include_card = False
                            break
                if include_card:
                    filtered_data.append(card)
            data = filtered_data
        
        # Calculate pagination
        self.current_page = 0
        start_idx = 0
        end_idx = min(self.cards_per_page.get(), len(data))
        
        # Display cards
        for card in data[start_idx:end_idx]:
            values = [card.get(key, "") for key in self.card_display["columns"]]
            self.card_display.insert("", "end", values=values)
    
    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_cards()
    
    def next_page(self):
        display_data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        if display_data and (self.current_page + 1) * self.cards_per_page.get() < len(display_data):
            self.current_page += 1
            self.display_cards()
    
    def export_json(self):
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
            ordered_columns = [col["id"] for col in self.column_config["columns"]]
            # Only include columns that exist in the data
            existing_columns = [col for col in ordered_columns if col in df.columns]
            df = df[existing_columns]
            # Rename columns according to configuration
            column_rename = {col["id"]: col["display"] for col in self.column_config["columns"]}
            df = df.rename(columns=column_rename)
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", "CSV file exported successfully")

    def update_card_display_columns(self, data):
        """Update the treeview columns based on the configuration"""
        if not data:
            return
            
        # Add Whatnot price column if not exists
        if not any(col["id"] == "Whatnot price" for col in self.column_config["columns"]):
            self.column_config["columns"].append({
                "id": "Whatnot price",
                "display": "Whatnot Price",
                "width": 100
            })
        
        # Configure columns
        self.card_display["columns"] = tuple(col["id"] for col in self.column_config["columns"])
        
        # Set column headings and widths
        for col in self.column_config["columns"]:
            self.card_display.heading(col["id"], text=col["display"])
            self.card_display.column(col["id"], width=col["width"], minwidth=50, stretch=True)

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

    def update_prices(self):
        """Update prices with rounding"""
        if not self.merged_data and not self.new_data and not self.existing_data:
            logging.warning("No data to update prices")
            return
            
        data = self.merged_data if self.merged_data else (self.new_data if self.new_data else self.existing_data)
        threshold = self.price_rounding_threshold.get()
        logging.info(f"Starting price updates with threshold: {threshold}")
        
        updated_count = 0
        for card in data:
            if "Purchase price" in card:
                try:
                    price = float(card["Purchase price"])
                    decimal_part = price - int(price)
                    
                    if decimal_part >= threshold:
                        rounded_price = int(price) + 1
                    else:
                        rounded_price = int(price)
                    
                    card["Purchase price"] = f"${price:.2f}"
                    card["Whatnot price"] = f"${rounded_price}"
                    updated_count += 1
                    logging.debug(f"Updated prices for {card['Name']}: Original=${price:.2f}, Whatnot=${rounded_price}")
                except Exception as e:
                    logging.error(f"Error updating price for {card['Name']}: {str(e)}")
        
        logging.info(f"Price update complete. Updated {updated_count} cards")
        self.display_cards()

    def show_advanced_filters(self):
        """Show advanced filter dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Advanced Filters")
        dialog.geometry("400x500")
        
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
                column_values[key].add(str(value))
        
        # Create filter checkboxes
        filter_vars = {}
        for col in self.column_config["columns"]:
            if col["id"] in column_values:
                frame = ttk.LabelFrame(dialog, text=col["display"])
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
        
        # Add apply button
        ttk.Button(dialog, text="Apply Filters", 
                  command=lambda: self.apply_advanced_filters(filter_vars, dialog)).pack(pady=10)

    def toggle_all_filters(self, column, value):
        """Toggle all filters for a column"""
        for key, var in self.active_filters.items():
            if key.startswith(f"{column}_"):
                var.set(value)

    def apply_advanced_filters(self, filter_vars, dialog):
        """Apply advanced filters"""
        self.active_filters = filter_vars
        self.display_cards()
        dialog.destroy()

    def apply_filters(self):
        """Apply text and advanced filters"""
        self.display_cards()

def main():
    root = tk.Tk()
    app = ManaBoxEnhancerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 