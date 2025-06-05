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
        """
        Parses the full text of a packing slip PDF (all pages concatenated).
        Returns a list of dicts, one per buyer, each with show, buyer, and sales info.
        """
        print("=== RAW PDF TEXT PASSED TO PARSER ===")
        print(text)
        buyers = []
        pages = re.split(r"--- PAGE \\d+ ---", text)
        for page in pages:
            if not page.strip():
                continue
            show_info = self._extract_show_info(page)
            lines = page.splitlines()
            buyer_info = None
            sales = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                # Detect buyer block
                if line.startswith("Ships to:") or line.startswith("( NEW BUYER! )") or re.match(r".+\d{5}(-\d{4})?\. US", line):
                    if buyer_info and sales:
                        buyers.append({
                            "show": show_info,
                            "buyer": buyer_info,
                            "sales": sales
                        })
                        sales = []
                    # Parse buyer info (use next lines)
                    name = ''
                    username = ''
                    address = ''
                    # Try to extract name/username/address from next lines
                    if i+1 < len(lines):
                        next_line = lines[i+1].strip()
                        m = re.match(r"(.+?) \(([^)]+)\) (.+)", next_line)
                        if m:
                            name = m.group(1).strip()
                            username = m.group(2).strip()
                            address = m.group(3).strip()
                        else:
                            name = next_line
                    buyer_info = {"name": name, "username": username, "address": address}
                    i += 2
                    continue
                i += 1
            # After collecting all lines, extract sales for this page
            page_sales = self._extract_sales(page)
            if buyer_info and page_sales:
                buyers.append({
                    "show": show_info,
                    "buyer": buyer_info,
                    "sales": page_sales
                })
        if buyers:
            print("=== PARSED SALES FOR FIRST BUYER ===")
            for sale in buyers[0]["sales"]:
                print(sale)
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
        # Robustly handle Name: ... Quantity: ... [card name/details] Description: ...
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
            # Look for Name: ...
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
                    # Parse card_name_details (e.g., 'Prime Speaker Zegana foil en')
                    parts = card_name_details.split()
                    name = " ".join(parts[:-2]) if len(parts) > 2 else card_name_details
                    foil = parts[-2] if len(parts) > 1 else ''
                    lang = parts[-1] if len(parts) > 1 else ''
                    # Parse description fields
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
                continue
            i += 1
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