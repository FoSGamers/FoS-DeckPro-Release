from PySide6.QtCore import QObject, Signal
from config import Config
import random
from typing import List, Dict, Any

class DeckBuilderEngine(QObject):
    progress = Signal(str)

    def __init__(self, inventory_manager, scryfall_client, codex_rules_manager, sim_knowledge_base):
        super().__init__()
        self.inventory_manager = inventory_manager
        self.scryfall_client = scryfall_client
        self.rules_manager = codex_rules_manager
        self.knowledge_base = sim_knowledge_base
        self.config = Config
        self._setup_error_handling()

    def _setup_error_handling(self):
        self.error_handlers = {
            'invalid_card': self._handle_invalid_card,
            'deck_size': self._handle_deck_size_error,
            'mana_curve': self._handle_mana_curve_error,
            'color_balance': self._handle_color_balance_error,
            'budget': self._handle_budget_error
        }

    def _validate_deck_size(self, deck: dict) -> bool:
        format_ = deck["stats"]["format"]
        expected_size = 100 if format_ == "pauper_edh" else 60
        actual_size = sum(count for _, count in deck["mainboard"])
        return actual_size == expected_size

    def _validate_mana_curve(self, deck: dict) -> bool:
        curve = deck["stats"]["mana_curve"]
        total_spells = sum(curve.values())
        if total_spells == 0:
            return False
            
        # Check for proper curve distribution
        low_cmc = sum(curve[i] for i in range(3)) / total_spells
        mid_cmc = sum(curve[i] for i in range(3, 5)) / total_spells
        high_cmc = sum(curve[i] for i in range(5, 7)) / total_spells
        
        return 0.4 <= low_cmc <= 0.6 and 0.2 <= mid_cmc <= 0.4 and 0.1 <= high_cmc <= 0.3

    def _validate_color_balance(self, deck: dict) -> bool:
        color_counts = {}
        for card, _ in deck["mainboard"]:
            for color in card.get("colors", []):
                color_counts[color] = color_counts.get(color, 0) + 1
                
        if not color_counts:
            return True  # Colorless deck
            
        total = sum(color_counts.values())
        for count in color_counts.values():
            if count / total < 0.1:  # No color should be less than 10%
                return False
        return True

    def _handle_invalid_card(self, card: dict) -> None:
        self.progress.emit(f"Invalid card data: {card.get('name', 'Unknown')}")
        
    def _handle_deck_size_error(self, deck: dict) -> None:
        format_ = deck["stats"]["format"]
        expected_size = 100 if format_ == "pauper_edh" else 60
        actual_size = sum(count for _, count in deck["mainboard"])
        self.progress.emit(f"Invalid deck size: {actual_size} (expected {expected_size})")
        
    def _handle_mana_curve_error(self, deck: dict) -> None:
        self.progress.emit("Invalid mana curve distribution")
        
    def _handle_color_balance_error(self, deck: dict) -> None:
        self.progress.emit("Invalid color balance")
        
    def _handle_budget_error(self, deck: dict) -> None:
        self.progress.emit(f"Deck exceeds budget: ${deck['stats']['total_cost']}")

    def build_decks_iterative(self, user_preferences: dict, num_decks_to_build: int, build_strategy: str) -> List[Dict]:
        decks = []
        temp_inventory = self.inventory_manager.get_card_pool_for_deckbuilding(user_preferences)
        exclude_cards = {}

        for i in range(num_decks_to_build):
            self.progress.emit(f"Building deck {i+1}/{num_decks_to_build}")
            if build_strategy == "draft_style":
                deck = self._construct_single_deck(user_preferences, temp_inventory, exclude_cards, is_draft=True)
            else:
                deck = self._construct_single_deck(user_preferences, temp_inventory, exclude_cards)

            if not deck:
                self.progress.emit("No more viable decks can be built")
                break

            decks.append(deck)
            if build_strategy != "single_most_powerful":
                for card, count in deck["mainboard"]:
                    exclude_cards[card["scryfall_id"]] = exclude_cards.get(card["scryfall_id"], 0) + count

            if build_strategy == "single_most_powerful":
                break

        return decks

    def _construct_single_deck(self, prefs: dict, inventory_pool: list, exclude_cards: dict, is_draft: bool = False) -> Dict:
        try:
            # Validate preferences and inventory
            if not self._validate_preferences(prefs) or not inventory_pool:
                return {}
            
            format_ = prefs.get("format", "pauper_60")
            archetype = prefs.get("archetype", "Aggro")
            budget = prefs.get("budget", self.config.DEFAULT_BUDGET.get(format_, 25.0))
            commander_name = prefs.get("commander", "")
            themes = prefs.get("themes", [])

            deck_size = 100 if format_ == "pauper_edh" else 60
            land_percentage = self.config.LAND_PERCENTAGE[format_]
            land_count = int(deck_size * random.uniform(land_percentage[0], land_percentage[1]))
            spell_count = deck_size - land_count - (1 if format_ == "pauper_edh" else 0)

            commander_ci = []
            if commander_name:
                commander_data = self.scryfall_client.enrich_card_data(commander_name, ["color_identity"])
                commander_ci = commander_data.get("color_identity", [])

            pool = self.inventory_manager.get_card_pool_for_deckbuilding(
                {"format": format_, "commander_color_identity": commander_ci}, exclude_cards
            )

            if not pool:
                self.progress.emit("No cards available for deck building")
                return {}

            selected_spells = []
            total_cost = 0.0

            for _ in range(spell_count):
                scored_cards = []
                for card in pool:
                    if card["quantity"] <= exclude_cards.get(card["scryfall_id"], 0):
                        continue
                    score = (
                        self.config.HEURISTIC_WEIGHTS["archetype_fit"] * self.rules_manager.get_archetype_fit_score(card, archetype) +
                        self.config.HEURISTIC_WEIGHTS["staples"] * self.rules_manager.get_staple_score(card["name"], format_, archetype) +
                        self.config.HEURISTIC_WEIGHTS["synergy"] * sum(
                            self.rules_manager.get_synergy_score(card, other, {}) for other, _ in selected_spells
                        ) / (len(selected_spells) or 1) +
                        self.config.HEURISTIC_WEIGHTS["simulation_performance"] * self.knowledge_base.get_performance_data(card["name"]).get("win_rate", 0.0)
                    )
                    scored_cards.append((card, score))

                if not scored_cards:
                    break

                scored_cards.sort(key=lambda x: x[1], reverse=True)
                selected_card = scored_cards[0][0]

                card_cost = selected_card.get("purchase_price", 0.0)
                if total_cost + card_cost > budget:
                    continue

                selected_spells.append((selected_card, 1))
                total_cost += card_cost

                if is_draft:
                    exclude_cards[selected_card["scryfall_id"]] = exclude_cards.get(selected_card["scryfall_id"], 0) + 1

            color_counts = {}
            for card, _ in selected_spells:
                for color in card.get("colors", []):
                    color_counts[color] = color_counts.get(color, 0) + 1

            total_colors = sum(color_counts.values()) or 1
            lands = []
            for color in ["W", "U", "B", "R", "G"]:
                count = int(land_count * (color_counts.get(color, 0) / total_colors)) if total_colors else land_count // 5
                if count > 0:
                    land_name = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}[color]
                    lands.append(({"name": land_name, "type_line": "Basic Land", "purchase_price": 0.0}, count))

            commander = None
            if format_ == "pauper_edh" and commander_name:
                for card in pool:
                    if card["name"] == commander_name and card["quantity"] > exclude_cards.get(card["scryfall_id"], 0):
                        commander = card
                        exclude_cards[card["scryfall_id"]] = exclude_cards.get(card["scryfall_id"], 0) + 1
                        break

            if format_ == "pauper_edh" and not commander:
                self.progress.emit("No valid commander available")
                return {}

            # Optimize mana curve
            selected_spells = self._optimize_mana_curve(selected_spells)
            
            # Balance colors and create lands
            lands = self._balance_colors(selected_spells, land_count)
            
            # Create deck structure
            deck = {
                "mainboard": selected_spells + lands,
                "sideboard": [],
                "commander": commander,
                "stats": {
                    "mana_curve": self._calculate_mana_curve(selected_spells),
                    "total_cost": total_cost,
                    "archetype": archetype,
                    "format": format_,
                    "color_distribution": self._calculate_color_distribution(selected_spells)
                }
            }
            
            # Validate final deck
            if not self._validate_deck(deck):
                return {}
            
            return deck

        except Exception as e:
            self.progress.emit(f"Error building deck: {e}")
            return {}

    def _calculate_mana_curve(self, cards: list) -> dict:
        curve = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        for card, count in cards:
            cmc = int(card.get("cmc", 0))
            if cmc <= 6:
                curve[cmc] += count
            else:
                curve[6] += count
        return curve

    def _validate_preferences(self, prefs: dict) -> bool:
        """Validate user preferences for deck building"""
        required_fields = {'format', 'archetype'}
        if not all(field in prefs for field in required_fields):
            self.progress.emit("Missing required preferences")
            return False
        
        format_ = prefs.get('format')
        if format_ not in self.config.DEFAULT_BUDGET:
            self.progress.emit(f"Invalid format: {format_}")
            return False
        
        archetype = prefs.get('archetype')
        if archetype not in self.rules_manager.archetypes:
            self.progress.emit(f"Invalid archetype: {archetype}")
            return False
        
        budget = prefs.get('budget')
        if budget is not None and (not isinstance(budget, (int, float)) or budget <= 0):
            self.progress.emit(f"Invalid budget: {budget}")
            return False
        
        return True

    def _validate_card_data(self, card: dict) -> bool:
        """Validate card data structure and required fields"""
        required_fields = {'name', 'type_line', 'cmc', 'colors', 'scryfall_id'}
        if not all(field in card for field in required_fields):
            self.error_handlers['invalid_card'](card)
            return False
        return True

    def _optimize_mana_curve(self, selected_spells: list) -> list:
        """Optimize the mana curve of selected spells"""
        curve = self._calculate_mana_curve(selected_spells)
        total_spells = sum(curve.values())
        
        # Calculate target distribution
        target_distribution = {
            0: 0.05,  # 5% for 0 CMC
            1: 0.15,  # 15% for 1 CMC
            2: 0.25,  # 25% for 2 CMC
            3: 0.25,  # 25% for 3 CMC
            4: 0.15,  # 15% for 4 CMC
            5: 0.10,  # 10% for 5 CMC
            6: 0.05   # 5% for 6+ CMC
        }
        
        # Calculate current distribution
        current_distribution = {
            cmc: count / total_spells for cmc, count in curve.items()
        }
        
        # Adjust card counts to match target distribution
        optimized_spells = []
        for card, count in selected_spells:
            cmc = int(card.get('cmc', 0))
            if cmc > 6:
                cmc = 6
            
            target_count = int(total_spells * target_distribution[cmc])
            current_count = curve[cmc]
            
            if current_count < target_count:
                # Add more cards of this CMC
                optimized_spells.append((card, min(count + 1, card.get('quantity', 1))))
            else:
                # Keep current count
                optimized_spells.append((card, count))
            
        return optimized_spells

    def _balance_colors(self, selected_spells: list, land_count: int) -> list:
        """Balance the color distribution of the deck"""
        color_counts = {}
        for card, _ in selected_spells:
            for color in card.get('colors', []):
                color_counts[color] = color_counts.get(color, 0) + 1
            
        if not color_counts:
            # Colorless deck, distribute lands evenly
            return self._create_basic_lands(land_count, {})
        
        total_colors = sum(color_counts.values())
        target_percentage = 1.0 / len(color_counts)
        
        # Calculate land distribution
        land_distribution = {}
        for color, count in color_counts.items():
            percentage = count / total_colors
            if abs(percentage - target_percentage) > 0.1:  # More than 10% deviation
                # Adjust land count to balance colors
                land_distribution[color] = int(land_count * target_percentage)
            else:
                land_distribution[color] = int(land_count * percentage)
            
        return self._create_basic_lands(land_count, land_distribution)

    def _create_basic_lands(self, total_lands: int, distribution: dict) -> list:
        """Create basic lands based on color distribution"""
        lands = []
        if not distribution:
            # Even distribution for colorless decks
            per_color = total_lands // 5
            for color in ["W", "U", "B", "R", "G"]:
                if per_color > 0:
                    land_name = {"W": "Plains", "U": "Island", "B": "Swamp", 
                               "R": "Mountain", "G": "Forest"}[color]
                    lands.append(({"name": land_name, "type_line": "Basic Land", 
                                 "purchase_price": 0.0}, per_color))
        else:
            # Use provided distribution
            for color, count in distribution.items():
                if count > 0:
                    land_name = {"W": "Plains", "U": "Island", "B": "Swamp", 
                               "R": "Mountain", "G": "Forest"}[color]
                    lands.append(({"name": land_name, "type_line": "Basic Land", 
                                 "purchase_price": 0.0}, count))
        return lands

    def _validate_deck(self, deck: dict) -> bool:
        """Validate the complete deck structure"""
        if not self._validate_deck_size(deck):
            self.error_handlers['deck_size'](deck)
            return False
        
        if not self._validate_mana_curve(deck):
            self.error_handlers['mana_curve'](deck)
            return False
        
        if not self._validate_color_balance(deck):
            self.error_handlers['color_balance'](deck)
            return False
        
        if deck['stats']['total_cost'] > self.config.DEFAULT_BUDGET.get(deck['stats']['format'], 25.0):
            self.error_handlers['budget'](deck)
            return False
        
        return True

    def _calculate_color_distribution(self, cards: list) -> dict:
        """Calculate the color distribution of the deck"""
        color_counts = {}
        for card, count in cards:
            for color in card.get('colors', []):
                color_counts[color] = color_counts.get(color, 0) + count
        return color_counts
