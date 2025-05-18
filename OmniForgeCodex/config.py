import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FORGE_EXECUTABLE = '/Users/jgleason/Library/Application Support/Forge/forge.sh'
    FORGE_USER_DATA = '/Users/jgleason/Library/Application Support/Forge/userdata'
    OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
    TEMP_DECK_DIR = os.path.join(OUTPUT_DIR, 'decks')
    RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
    DEFAULT_DATA_DIR = os.path.join(RESOURCES_DIR, 'default_data')
    SCRYFALL_API_URL = 'https://api.scryfall.com'
    SCRYFALL_REQUEST_DELAY = 0.1
    PROFIT_MARGIN = 0.2
    ROUNDING_THRESHOLD = 0.25
    DEFAULT_CARD_CONDITION = 'Near Mint'
    SALES_DESCRIPTION_TEMPLATES = {
        'pauper_edh': 'Pauper EDH {commander} {archetype} deck, {card_count} cards, ${price}',
        'pauper_60': 'Pauper 60-card {archetype} deck, {card_count} cards, ${price}'
    }
    DEFAULT_BUDGET = {'pauper_edh': 25.0, 'pauper_60': 25.0}
    DEFAULT_STRATEGY = 'single_most_powerful'
    LAND_PERCENTAGE = {'pauper_edh': (0.33, 0.40), 'pauper_60': (0.38, 0.42)}
    HEURISTIC_WEIGHTS = {
        'synergy': 0.4,
        'archetype_fit': 0.3,
        'staples': 0.2,
        'simulation_performance': 0.1
    }
    DEFAULT_OPPONENTS = 1
    DEFAULT_SIM_RUNS = 100
    FORGE_AI_PROFILES = ['Aggressive', 'Control']
    DEFAULT_THEME = 'dark'
    INVENTORY_COLUMNS = ['Name', 'Quantity', 'Purchase Price', 'Type', 'CMC']
    SIMULATION_DATA_DIR = os.path.join(RESOURCES_DIR, 'simulation_data')
