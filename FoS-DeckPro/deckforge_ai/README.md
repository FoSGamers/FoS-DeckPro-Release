# DeckForge AI – Inventory-Based MTG Deck Generator

## Purpose
A smart, format-aware deckbuilding engine that:
- Uses a player's Manabox-enriched inventory (JSON/CSV)
- Builds fully legal, synergistic, winning decks (starting with Pauper/Commander Pauper)
- Simulates decks using MTG Forge CLI
- Learns from simulation results to improve future builds

## Directory Structure
```
deckforge_ai/
  __init__.py
  deck_learning_engine.py
  deckforge_gui_app.py
  deckforge_gui_autosim.py
  deckforge_json_deckbuilder.py
  forge_result_parser.py
  MTG Forge CLI Research.txt
  README.md
```

## Inventory Input
- Use Manabox-enhanced inventory files as the canonical data source.
- All Scryfall-derived fields (oracle_text, type_line, color_identity, legalities, etc.) are already present.
- **Do NOT re-query Scryfall** unless a field is missing or malformed.

### Expected Fields (examples)
- Name
- Scryfall ID
- oracle_text
- type_line
- colors, color_identity
- legal_pauper, legal_commander
- mana_cost, cmc
- rarity, set_name
- price (optional)

## Main Features
- **Deck Generation:** Format-aware, archetype-based, synergy-scored deck assembly
- **Simulation:** Export to Forge .dck, run headless simulations, parse results
- **Learning:** Update card/deck stats based on simulation outcomes
- **GUI & CLI:** Tkinter and PySide6 GUIs, plus CLI tools

## Usage
- Run any of the GUIs or CLI tools in this directory.
- All tools expect a Manabox-enriched inventory file as input.
- See `MTG Forge CLI Research.txt` for details on Forge integration.

## Extending/Integrating
- Add new formats by updating legality checks and archetype logic
- Add new export formats as needed
- For web/REST integration, wrap deck generation and simulation in API endpoints

## Development Notes
- All format legality, synergy, and archetype logic uses the pre-enriched inventory fields
- Only fetch from Scryfall if a field is missing or clearly wrong
- See code comments for extension points

---

**For questions or to add new features, see the main project README or contact the maintainers.** 