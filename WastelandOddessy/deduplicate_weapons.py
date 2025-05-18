import json
import shutil
from collections import defaultdict

JSON_FILE = "wasteland_odyssey.json"
BACKUP_FILE = "wasteland_odyssey.json.bak"

def weapon_key(w):
    # Use a tuple of key stats to identify duplicates
    return (
        w.get("name", ""),
        w.get("description", ""),
        w.get("damage_dice", ""),
        w.get("hit_modifier", 0),
        w.get("type", ""),
        json.dumps(w.get("special_effects", []), sort_keys=True),
        json.dumps(w.get("buffs", []), sort_keys=True),
    )

def main():
    # Backup the original file
    shutil.copyfile(JSON_FILE, BACKUP_FILE)
    print(f"Backup created: {BACKUP_FILE}")

    with open(JSON_FILE, "r") as f:
        data = json.load(f)

    weapons = data.get("weapons", [])
    key_to_weapon = {}
    id_map = {}  # old_id -> new_id

    # Deduplicate weapons
    for w in weapons:
        k = weapon_key(w)
        if k not in key_to_weapon:
            key_to_weapon[k] = w
            id_map[w["id"]] = w["id"]
        else:
            # Map duplicate's id to the kept weapon's id
            id_map[w["id"]] = key_to_weapon[k]["id"]

    # Build new weapons list
    new_weapons = list(key_to_weapon.values())
    print(f"Deduplicated weapons: {len(weapons)} -> {len(new_weapons)}")

    # Update all player and enemy references
    for entity_list_name in ["players", "enemies"]:
        for entity in data.get(entity_list_name, []):
            eq = entity.get("equipment", {})
            # Update equipped weapon
            if eq.get("weapon"):
                old_id = eq["weapon"]
                eq["weapon"] = id_map.get(old_id, "")
            # Update items list
            if "items" in eq:
                eq["items"] = [id_map.get(i, i) for i in eq["items"]]

    # Remove references to deleted weapon ids from inventories
    valid_weapon_ids = set(w["id"] for w in new_weapons)
    for entity_list_name in ["players", "enemies"]:
        for entity in data.get(entity_list_name, []):
            eq = entity.get("equipment", {})
            if eq.get("weapon") and eq["weapon"] not in valid_weapon_ids:
                eq["weapon"] = ""
            if "items" in eq:
                eq["items"] = [i for i in eq["items"] if i in valid_weapon_ids or not i.startswith("weapon_")]

    data["weapons"] = new_weapons

    for entity_list_name in ["players", "enemies"]:
        for ent in data.get(entity_list_name, []):
            if "stats" not in ent:
                ent["stats"] = {}
            for stat in ["hp", "strength", "agility", "engineering", "intelligence", "luck"]:
                if stat in ent:
                    ent["stats"][stat] = ent[stat]
                    del ent[stat]

    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Deduplication complete. Updated {JSON_FILE}")

if __name__ == "__main__":
    main()