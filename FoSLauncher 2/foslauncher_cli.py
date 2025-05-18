# File: foslauncher_cli.py

import json
import os
import subprocess

MANIFEST_PATH = "modules/manifest.json"

def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        print(f"Manifest file not found at {MANIFEST_PATH}.")
        return []
    try:
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print("Error parsing manifest file. Please check the JSON format.")
        print(f"Details: {e}")
        return []

def list_modules(manifest):
    if not manifest:
        print("No modules available to launch.")
        return

    print("\n=== Available Modules ===")
    for i, module in enumerate(manifest):
        name = module.get("Name", "Unknown")
        module_id = module.get("ID", "no-id")
        status = module.get("Status", "Unknown")
        print(f"{i + 1}. {name} ({module_id}) - {status}")
    print("==========================\n")

def launch_module(manifest, choice):
    if not (1 <= choice <= len(manifest)):
        print("Invalid choice.")
        return

    module = manifest[choice - 1]
    entry = module.get("Path") or module.get("Entry")

    if not entry:
        print("Error launching module: 'Path' or 'Entry' key not found.")
        return

    print(f"\nLaunching: {module.get('Name', 'Unnamed Module')} → {entry}")

    try:
        process = subprocess.Popen(["python3", entry], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
    except Exception as e:
        print(f"Error launching module: {e}")

def main():
    manifest = load_manifest()
    list_modules(manifest)

    if not manifest:
        return

    try:
        choice = int(input("Enter the number of the module to launch: "))
        launch_module(manifest, choice)
    except ValueError:
        print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    main()
