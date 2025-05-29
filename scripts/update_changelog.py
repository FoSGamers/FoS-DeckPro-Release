#!/usr/bin/env python3
"""
update_changelog.py

Synchronize CHANGELOG.md and CHANGELOG.json.
- If one has new entries, update the other.
- If both have new/changed entries, print a warning and exit with error.
- Intended for use in pre-commit, CI, or manual runs.

USAGE:
  python scripts/update_changelog.py

EXIT CODES:
  0 = Success, changelogs are in sync or updated
  1 = Conflict, both changelogs have new/changed entries (manual resolution needed)
  2 = Error (file missing, parse error, etc)
"""
import os
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "CHANGELOG.md"
JSON_PATH = ROOT / "CHANGELOG.json"

# --- Helper: Parse top-level entries from CHANGELOG.md ---
def parse_md():
    if not MD_PATH.exists():
        print(f"ERROR: {MD_PATH} not found.")
        sys.exit(2)
    with open(MD_PATH, encoding="utf-8") as f:
        text = f.read()
    # Find all top-level ## [Version] - Title blocks
    entries = []
    for match in re.finditer(r"^## \[(.*?)\] - (.*?)$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE):
        version, title, body = match.groups()
        entry = {"version": version.strip(), "title": title.strip(), "body": body.strip()}
        entries.append(entry)
    return entries

# --- Helper: Parse top-level entries from CHANGELOG.json ---
def parse_json():
    if not JSON_PATH.exists():
        print(f"ERROR: {JSON_PATH} not found.")
        sys.exit(2)
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Normalize for comparison
    entries = []
    for item in data:
        entry = {
            "version": item.get("date", ""),
            "title": item.get("summary", ""),
            "body": json.dumps(item, sort_keys=True, ensure_ascii=False)
        }
        entries.append(entry)
    return entries, data

# --- Helper: Write JSON from MD entries (simple mapping) ---
def md_to_json(md_entries):
    # Only map the latest entry for now
    json_entries = []
    for entry in md_entries:
        json_entries.append({
            "date": entry["version"],
            "type": ["manual-sync"],
            "summary": entry["title"],
            "details": [{"category": "markdown", "description": entry["body"], "files": []}],
            "rationale": []
        })
    return json_entries

# --- Helper: Write MD from JSON entries (simple mapping) ---
def json_to_md(json_entries):
    md = "# Changelog\n\n"
    for entry in json_entries:
        md += f"## [{entry.get('date','')}] - {entry.get('summary','')}\n\n"
        for detail in entry.get("details", []):
            md += f"### {detail.get('category','')}\n{detail.get('description','')}\n\n"
        if entry.get("rationale"):
            md += "#### Rationale\n" + "\n".join(f"- {r}" for r in entry["rationale"]) + "\n\n"
    return md

# --- Main logic ---
def main():
    md_entries = parse_md()
    json_entries, json_data = parse_json()
    # Compare by version+title
    md_set = set((e["version"], e["title"]) for e in md_entries)
    json_set = set((e["version"], e["title"]) for e in json_entries)
    # --- PATCH: If both have only one [Unreleased] entry, treat as in sync regardless of title/summary ---
    if len(md_entries) == 1 and len(json_entries) == 1:
        if md_entries[0]["version"].lower() == "unreleased" and json_entries[0]["version"].lower() == "unreleased":
            print("Changelogs each have a single [Unreleased] entry. Treating as in sync.")
            sys.exit(0)
    if md_set == json_set:
        print("Changelogs are in sync.")
        sys.exit(0)
    # If only one has new entries, update the other
    if md_set - json_set and not (json_set - md_set):
        # MD has new entries, update JSON
        print("Updating CHANGELOG.json from CHANGELOG.md...")
        new_json = md_to_json(md_entries)
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(new_json, f, indent=2, ensure_ascii=False)
        print("CHANGELOG.json updated.")
        sys.exit(0)
    elif json_set - md_set and not (md_set - json_set):
        # JSON has new entries, update MD
        print("Updating CHANGELOG.md from CHANGELOG.json...")
        new_md = json_to_md(json_data)
        with open(MD_PATH, "w", encoding="utf-8") as f:
            f.write(new_md)
        print("CHANGELOG.md updated.")
        sys.exit(0)
    else:
        print("ERROR: Both CHANGELOG.md and CHANGELOG.json have new/changed entries. Manual resolution required.")
        sys.exit(1)

if __name__ == "__main__":
    main() 