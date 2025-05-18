import csv
import json
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "commands.csv")
JSON_PATH = os.path.join(os.path.dirname(__file__), "commands.json")

def import_commands():
    commands = {}
    try:
        with open(CSV_PATH, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                cmd = row.get("command", "").strip().lower()
                res = row.get("response", "").strip()
                if cmd:
                    commands[cmd] = res

        with open(JSON_PATH, "w") as f:
            json.dump(commands, f, indent=2)

        print(f"Imported {len(commands)} commands into {JSON_PATH}")
    except Exception as e:
        print(f"Error importing commands: {e}")

if __name__ == "__main__":
    import_commands()
