# Wasteland AI Card Generator

A modular, extensible RPG card generator with AI integration (OpenAI, DALL·E) and a PySide6 GUI.

## Features
- Batch card generation with AI prompts
- Structured RPG card format
- Front/back image generation (stubbed, ready for real AI)
- Live card rendering with overlays
- PNG export
- Scrollable session card list

## Structure
```
Card Generator/
├── main.py                # Entry point
├── gui/
│   └── card_window.py     # All PySide6 GUI code
├── ai/
│   ├── ai_stub.py         # Dummy AI (for now)
│   └── openai_provider.py # Real OpenAI integration (future)
├── cards/
│   ├── card.py            # Card data structures, schema, overlays
│   └── image_utils.py     # Image generation, overlays
├── config/
│   └── config.py          # Config loading, .env support
├── utils/
│   └── helpers.py         # Misc helpers
├── requirements.txt
└── README.md
```

## Running
1. `pip install -r requirements.txt`
2. `python main.py`

## Extending
- Add new AI/image providers in `ai/`
- Add new card types or overlays in `cards/`
- Update config in `config/` 