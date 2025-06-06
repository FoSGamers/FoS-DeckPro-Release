# Card field definitions and helpers migrated from the monolithic app

CARD_FIELDS = [
    "Name", "Set code", "Set name", "Collector number", "Foil", "Rarity", "Quantity",
    "ManaBox ID", "Scryfall ID", "Purchase price", "Misprint", "Altered", "Condition",
    "Language", "Purchase price currency", "type_line", "mana_cost", "colors",
    "color_identity", "oracle_text", "legal_commander", "legal_pauper", "cmc", "image_url",
    "Whatnot price",
    # Scryfall price fields
    "price_usd", "price_usd_foil", "price_usd_etched", "price_eur", "price_eur_foil", "price_eur_etched", "price_tix",
    # Scryfall purchase URIs
    "buy_tcgplayer", "buy_cardmarket", "buy_cardhoarder", "buy_mtgo", "buy_cardkingdom", "buy_cardkingdom_foil"
]

# Optionally, a Card class could be implemented if needed by the modular app.
