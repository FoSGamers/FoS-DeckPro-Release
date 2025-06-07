import re
from typing import List, Dict, Any, Optional

class WhatnotPackingSlipParser:
    """
    Parses Whatnot packing slip PDFs (as extracted text) into structured data for inventory removal and analytics.
    Extracts show info, buyer info, and card sales, and ignores non-card items.
    """
    def __init__(self, card_name_validator=None):
        """
        card_name_validator: Optional[callable] - function to validate if a name is a real card (e.g., via Scryfall or inventory)
        """
        self.card_name_validator = card_name_validator

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """Parse packing slip text into structured data."""
        # print("\n=== RAW PDF TEXT PASSED TO PARSER ===\n")
        # print(text)
        # print("\n")
        
        buyers = []
        current_buyer = None
        current_sales = []
        current_show = None
        
        # Split into pages and process each
        pages = text.split("--- PAGE")
        for page in pages:
            if not page.strip():
                continue
                
            # Extract show info if present
            show_match = re.search(r"Livestream Name: ([^\n]+)\nLivestream Date: ([^\n]+)", page)
            if show_match:
                current_show = {
                    "title": show_match.group(1).strip(),
                    "date": show_match.group(2).strip()
                }
            
            # Extract buyer info
            buyer_match = re.search(r"Ships to:\n([^\n]+)", page)
            if buyer_match:
                # If we have a previous buyer with sales, add them to the list
                if current_buyer and current_sales:
                    buyers.append({
                        "buyer": current_buyer,
                        "sales": current_sales,
                        "show": current_show
                    })
                    # print(f"=== PARSED SALES FOR PREVIOUS BUYER ===\n")
                    # for sale in current_sales:
                    #     print(sale)
                    # print("\n")
                
                # Start new buyer
                buyer_info = buyer_match.group(1).strip()
                name_match = re.match(r"([^(]+) \(([^)]+)\)", buyer_info)
                if name_match:
                    current_buyer = {
                        "name": name_match.group(1).strip(),
                        "username": name_match.group(2).strip(),
                        "address": buyer_info[name_match.end():].strip()
                    }
                    current_sales = []  # Reset sales for new buyer
            
            # Extract sales for current buyer
            if current_buyer:
                sales = self._extract_sales(page)
                if sales:
                    current_sales.extend(sales)
                    # print(f"Adding buyer with info: {current_buyer} and {len(sales)} sales")
        
        # Add the last buyer if they have sales
        if current_buyer and current_sales:
            buyers.append({
                "buyer": current_buyer,
                "sales": current_sales,
                "show": current_show
            })
            # print(f"=== PARSED SALES FOR LAST BUYER ===\n")
            # for sale in current_sales:
            #     print(sale)
            # print("\n")
        
        return buyers

    def _extract_show_info(self, page: str) -> Dict[str, Any]:
        title = self._extract_field(page, r"Livestream Name:\s*(.*)")
        date = self._extract_field(page, r"Livestream Date:\s*(.*)")
        return {"title": title, "date": date}

    def _extract_buyer_info(self, page: str) -> Optional[Dict[str, Any]]:
        # Extract buyer name, username, address
        m = re.search(r"Ships to:\s*([A-Za-z0-9 .,'()_-]+) ([^\n]+)", page)
        if not m:
            return None
        name_line = m.group(1) or ''
        username = ''
        name = name_line
        if '(' in name_line and ')' in name_line:
            # e.g. Aaron solomon (aarsolo)
            name_match = re.match(r"(.+?)\s*\(([^)]+)\)", name_line)
            if name_match:
                name, username = name_match.groups()
        address = m.group(2) or ''
        return {
            "name": name.strip(),
            "username": username.strip(),
            "address": address.strip()
        }

    def _extract_sales(self, page: str) -> List[Dict[str, Any]]:
        sales = []
        lines = page.splitlines()
        current_break = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # Detect break/lot line
            break_match = re.match(r"(Break|Lot)[ #:]*([\w\- ]+)", line, re.IGNORECASE)
            if break_match:
                current_break = break_match.group(0).strip()
                i += 1
                continue
            # Handle 'Name: ... Quantity: ...' on the same line
            name_qty_match = re.match(r"Name: ([^\n]+) Quantity: (\d+)", line)
            if name_qty_match:
                name_part = name_qty_match.group(1).strip()
                qty = name_qty_match.group(2).strip()
                # Next line should be Description
                desc_line = None
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("Description:"):
                    desc_line = lines[i + 1].strip()
                    i += 1
                # Parse description fields
                desc_fields = {}
                if desc_line:
                    for m in re.finditer(r"([\w ]+): ([^:]+)", desc_line):
                        k, v = m.group(1).strip(), m.group(2).strip()
                        desc_fields[k] = v
                sale = {
                    "Name": name_part,
                    "Quantity": qty,
                    **desc_fields
                }
                if current_break:
                    sale["Break"] = current_break
                sales.append(sale)
                # print(f"[DEBUG] Detected sale (single line): {sale}")
                i += 1
                continue
            # Old multi-line format
            if line.startswith("Name:"):
                # Skip to Quantity
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("Quantity:"):
                    i += 1
                if i >= len(lines):
                    break
                i += 1  # Move past Quantity
                # Next line: card name/details (if not empty and not a URL)
                if i < len(lines):
                    card_line = lines[i].strip()
                    if card_line and not card_line.startswith("http") and not card_line.startswith("Order:") and not card_line.startswith("Description:"):
                        card_name_details = card_line
                        i += 1
                    else:
                        card_name_details = None
                else:
                    card_name_details = None
                # Next line: Description
                desc_line = None
                while i < len(lines):
                    if lines[i].strip().startswith("Description:"):
                        desc_line = lines[i].strip()
                        i += 1
                        break
                    i += 1
                if card_name_details and desc_line:
                    parts = card_name_details.split()
                    name = " ".join(parts[:-2]) if len(parts) > 2 else card_name_details
                    foil = parts[-2] if len(parts) > 1 else ''
                    lang = parts[-1] if len(parts) > 1 else ''
                    desc_fields = {}
                    for m in re.finditer(r"([\w ]+): ([^:]+)", desc_line):
                        k, v = m.group(1).strip(), m.group(2).strip()
                        desc_fields[k] = v
                    sale = {
                        "Name": name,
                        "Foil": foil,
                        "Language": lang,
                        **desc_fields
                    }
                    if current_break:
                        sale["Break"] = current_break
                    sales.append(sale)
                    # print(f"[DEBUG] Detected sale (multi-line): {sale}")
                continue
            i += 1
        # print(f"[DEBUG] Total sales found for page: {len(sales)}")
        return sales

    def _split_name_foil(self, raw_name: str):
        # If the name ends with ' normal' or ' foil', split it
        m = re.match(r"(.+?)\s+(normal|foil|etched)$", raw_name, re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip().lower()
        return raw_name, None

    def _parse_description(self, desc: str) -> Dict[str, Any]:
        # Try to extract as many fields as possible
        fields = {}
        # Foil
        m = re.search(r"Foil: ([^ ]+)", desc)
        if m:
            fields["Foil"] = m.group(1)
        # Collector number
        m = re.search(r"Collector number: ([^ ]+)", desc)
        if m:
            fields["Collector number"] = m.group(1)
        # Set name
        m = re.search(r"Set name: ([^ ]+)", desc)
        if m:
            fields["Set name"] = m.group(1)
        # Set code
        m = re.search(r"Set code: ([^ ]+)", desc)
        if m:
            fields["Set code"] = m.group(1)
        # Rarity
        m = re.search(r"Rarity: ([^ ]+)", desc)
        if m:
            fields["Rarity"] = m.group(1)
        # Language
        m = re.search(r"Language: ([^ ]+)", desc)
        if m:
            fields["Language"] = m.group(1)
        return fields

    def _extract_field(self, text: str, pattern: str) -> str:
        m = re.search(pattern, text)
        return m.group(1).strip() if m else '' 