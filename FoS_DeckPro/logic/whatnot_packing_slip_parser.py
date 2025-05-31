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
        buyers = []
        pages = re.split(r"--- PAGE \d+ ---", text)
        for page in pages:
            if not page.strip():
                continue
            show_info = self._extract_show_info(page)
            buyer_info = self._extract_buyer_info(page)
            sales = self._extract_sales(page)
            if buyer_info and sales:
                buyers.append({
                    "show": show_info,
                    "buyer": buyer_info,
                    "sales": sales
                })
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
        # Find all Name: ... Quantity: ... blocks
        sales = []
        for m in re.finditer(r"Name: ([^\n]+?) Quantity: (\d+)[\n\r]+Description: ([^\n]+)?", page):
            raw_name = m.group(1).strip()
            quantity = int(m.group(2))
            description = m.group(3) or ''
            # Split foil/normal from name if present
            name, foil = self._split_name_foil(raw_name)
            # Ignore non-card names if validator is set
            if self.card_name_validator and not self.card_name_validator(name):
                continue
            # Extract fields from description
            fields = self._parse_description(description)
            fields["Name"] = name
            fields["Quantity"] = quantity
            # Prefer foil from name, then from description
            if foil:
                fields["Foil"] = foil
            elif "Foil" not in fields:
                fields["Foil"] = "normal"  # Default to normal if not specified
            sales.append(fields)
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