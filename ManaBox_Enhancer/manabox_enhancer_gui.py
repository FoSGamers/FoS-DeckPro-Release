import json
import os
from models.card import CARD_FIELDS

class ManaBoxEnhancerGUI:
    def setup_gui(self):
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        # ... existing code ...
        # --- Add Scryfall/Card Fields Filters ---
        filter_frame = ttk.LabelFrame(self.main_frame, text="Card Filters (All Fields)")
        filter_frame.pack(fill=tk.X, pady=5)
        self.filter_entries = {}
        numeric_fields = {f for f in CARD_FIELDS if any(x in f.lower() for x in ["price", "quantity", "number", "count", "cmc"])}
        for idx, field in enumerate(CARD_FIELDS):
            row = idx // 4
            col = (idx % 4) * 2
            label = ttk.Label(filter_frame, text=field+":")
            label.grid(row=row, column=col, sticky=tk.W, padx=2, pady=2)
            if field in numeric_fields:
                min_entry = ttk.Entry(filter_frame, width=8)
                min_entry.grid(row=row, column=col+1, sticky=tk.W, padx=1)
                min_entry.insert(0, "Min")
                max_entry = ttk.Entry(filter_frame, width=8)
                max_entry.grid(row=row, column=col+2, sticky=tk.W, padx=1)
                max_entry.insert(0, "Max")
                self.filter_entries[field] = (min_entry, max_entry)
            else:
                entry = ttk.Entry(filter_frame, width=18)
                entry.grid(row=row, column=col+1, columnspan=2, sticky=tk.W, padx=1)
                self.filter_entries[field] = entry
        # ... existing code ...
    def apply_filters(self):
        filters = {}
        for field, widget in self.filter_entries.items():
            if isinstance(widget, tuple):
                min_val = widget[0].get().strip()
                max_val = widget[1].get().strip()
                if min_val != "Min" or max_val != "Max":
                    filters[field] = (min_val if min_val != "Min" else "", max_val if max_val != "Max" else "")
            else:
                val = widget.get().strip()
                if val:
                    filters[field] = val
        filtered = []
        for card in self.existing_data or []:
            match = True
            for field, val in filters.items():
                if isinstance(val, tuple):
                    min_val, max_val = val
                    try:
                        card_val = float(card.get(field, 0))
                    except Exception:
                        match = False
                        break
                    if min_val:
                        try:
                            if card_val < float(min_val):
                                match = False
                                break
                        except Exception:
                            pass
                    if max_val:
                        try:
                            if card_val > float(max_val):
                                match = False
                                break
                        except Exception:
                            pass
                else:
                    or_values = [v.strip().lower() for v in val.split(",") if v.strip()]
                    card_val = str(card.get(field, "")).lower()
                    if not any(ov in card_val for ov in or_values):
                        match = False
                        break
            if match:
                filtered.append(card)
        # Update the grid/table with filtered
        self.update_card_grid(filtered)
# ... existing code ... 