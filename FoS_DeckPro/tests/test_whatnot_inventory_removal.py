import unittest
from ManaBox_Enhancer.logic.whatnot_inventory_removal import remove_sold_cards_from_inventory

def dummy_user_prompt(sale, matches):
    # Always pick the first match for testing
    return matches[0] if matches else None

class TestWhatnotInventoryRemoval(unittest.TestCase):
    def setUp(self):
        self.inventory = [
            {'Name': 'Card A', 'Set code': 'SET1', 'Collector number': '1', 'Language': 'en', 'Foil': 'normal', 'Quantity': 2},
            {'Name': 'Card B', 'Set code': 'SET2', 'Collector number': '2', 'Language': 'en', 'Foil': 'foil', 'Quantity': 1},
            {'Name': 'Card C', 'Set code': 'SET3', 'Collector number': '3', 'Language': 'en', 'Foil': 'normal', 'Quantity': 5},
            {'Name': 'Card D', 'Set code': 'SET4', 'Collector number': '4', 'Language': 'es', 'Foil': 'normal', 'Quantity': 1},
            {'Name': 'Card D', 'Set code': 'SET4', 'Collector number': '4', 'Language': 'en', 'Foil': 'normal', 'Quantity': 1},
        ]

    def test_exact_match_removal(self):
        sales = [{'Name': 'Card A', 'Set code': 'SET1', 'Collector number': '1', 'Language': 'en', 'Foil': 'normal', 'Quantity': 1}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales)
        self.assertEqual(updated[0]['Quantity'], 1)
        self.assertEqual(log[0]['action'], 'removed')

    def test_remove_all_quantity(self):
        sales = [{'Name': 'Card B', 'Set code': 'SET2', 'Collector number': '2', 'Language': 'en', 'Foil': 'foil', 'Quantity': 1}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales)
        self.assertTrue(all(c['Name'] != 'Card B' for c in updated))
        self.assertEqual(log[0]['action'], 'removed')

    def test_not_found(self):
        sales = [{'Name': 'Card X', 'Set code': 'SETX', 'Collector number': '99', 'Language': 'en', 'Foil': 'normal', 'Quantity': 1}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales)
        # No cards should be removed from inventory
        self.assertEqual(len(updated), len(self.inventory))
        self.assertEqual(log[0]['action'], 'not_found')

    def test_ambiguous(self):
        inv = self.inventory + [{'Name': 'Card A', 'Set code': 'SET1', 'Collector number': '1', 'Language': 'en', 'Foil': 'normal', 'Quantity': 1}]
        sales = [{'Name': 'Card A', 'Set code': 'SET1', 'Collector number': '1', 'Language': 'en', 'Foil': 'normal', 'Quantity': 1}]
        updated, log = remove_sold_cards_from_inventory(inv, sales)
        self.assertEqual(log[0]['action'], 'ambiguous')
        self.assertEqual(len(log[0]['matched_card']), 2)

    def test_partial_match(self):
        # Remove Card C with missing Language and Foil in sale
        sales = [{'Name': 'Card C', 'Set code': 'SET3', 'Collector number': '3', 'Quantity': 2}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales)
        self.assertEqual(updated[2]['Quantity'], 3)
        self.assertEqual(log[0]['action'], 'removed')

    def test_shortfall(self):
        sales = [{'Name': 'Card A', 'Set code': 'SET1', 'Collector number': '1', 'Language': 'en', 'Foil': 'normal', 'Quantity': 5}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales)
        self.assertTrue(all(c['Name'] != 'Card A' for c in updated))
        self.assertIn('Only 2 in inventory', log[0]['reason'])

    def test_language_ambiguity(self):
        # Card D exists in both 'en' and 'es', but sale has no language
        sales = [{'Name': 'Card D', 'Set code': 'SET4', 'Collector number': '4', 'Foil': 'normal', 'Quantity': 1}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales)
        self.assertEqual(log[0]['action'], 'ambiguous')
        self.assertIn('language', log[0]['reason'])

    def test_user_prompt_callback(self):
        # Card D exists in both 'en' and 'es', sale has no language, but user picks 'en'
        sales = [{'Name': 'Card D', 'Set code': 'SET4', 'Collector number': '4', 'Foil': 'normal', 'Quantity': 1}]
        updated, log = remove_sold_cards_from_inventory(self.inventory, sales, user_prompt_callback=dummy_user_prompt)
        # Should remove one of the Card D's
        d_cards = [c for c in updated if c['Name'] == 'Card D']
        self.assertEqual(len(d_cards), 1)
        self.assertEqual(log[0]['action'], 'removed')

    def test_regression_missed_cards(self):
        # Inventory with all the missed cards
        inv = [
            {'Name': "Will of the Jeskai", 'Set code': 'FDN', 'Collector number': '123', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Armory Paladin", 'Set code': 'CLB', 'Collector number': '350', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Ajani's Pridemate", 'Set code': 'M11', 'Collector number': '25', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Branching Evolution", 'Set code': 'C17', 'Collector number': '34', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Bribery", 'Set code': '8ED', 'Collector number': '80', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Wrathful Raptors", 'Set code': 'JMP', 'Collector number': '123', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Poetic Ingenuity", 'Set code': 'MOM', 'Collector number': '456', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Regal Imperiosaur", 'Set code': 'FUT', 'Collector number': '130', 'Foil': 'normal', 'Language': 'en', 'Quantity': 2},
            {'Name': "Sunfrill Imitator", 'Set code': 'MOM', 'Collector number': '789', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Scion of Calamity", 'Set code': 'C20', 'Collector number': '200', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Callous Bloodmage", 'Set code': 'STX', 'Collector number': '66', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Blazemire Verge", 'Set code': 'MH2', 'Collector number': '250', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Bedevil", 'Set code': 'RNA', 'Collector number': '157', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Banner of Kinship", 'Set code': 'NEO', 'Collector number': '300', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Coppercoat Vanguard", 'Set code': 'MAT', 'Collector number': '12', 'Foil': 'etched', 'Language': 'en', 'Quantity': 1},
            {'Name': "Chromatic Lantern", 'Set code': 'GRN', 'Collector number': '233', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Caves of Koilos", 'Set code': 'DMU', 'Collector number': '245', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Bleachbone Verge", 'Set code': 'MH2', 'Collector number': '251', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Agonasaur Rex", 'Set code': 'MOM', 'Collector number': '123', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Hulking Raptor", 'Set code': 'MOM', 'Collector number': '124', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Ethereal Armor", 'Set code': 'THS', 'Collector number': '17', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Insidious Roots", 'Set code': 'MID', 'Collector number': '234', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Cryptolith Rite", 'Set code': 'SOI', 'Collector number': '211', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Jacob Frye", 'Set code': 'UBB', 'Collector number': '1', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Legacy Weapon", 'Set code': 'DOM', 'Collector number': '218', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Evolving Wilds", 'Set code': 'M21', 'Collector number': '247', 'Foil': 'foil', 'Language': 'en', 'Quantity': 1},
            {'Name': "Eliminate", 'Set code': 'M21', 'Collector number': '94', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Diamond Lion", 'Set code': 'MH2', 'Collector number': '223', 'Foil': 'foil', 'Language': 'en', 'Quantity': 1},
            {'Name': "Deification", 'Set code': 'MOM', 'Collector number': '12', 'Foil': 'foil', 'Language': 'en', 'Quantity': 1},
            {'Name': "Defiant Strike", 'Set code': 'WAR', 'Collector number': '9', 'Foil': 'foil', 'Language': 'en', 'Quantity': 1},
            {'Name': "Deadly Cover-Up", 'Set code': 'MOM', 'Collector number': '13', 'Foil': 'normal', 'Language': 'en', 'Quantity': 2},
            {'Name': "Chef's Kiss", 'Set code': 'MH2', 'Collector number': '117', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Primal Vigor", 'Set code': 'C13', 'Collector number': '153', 'Foil': 'foil', 'Language': 'en', 'Quantity': 1},
            {'Name': "Witch's Oven", 'Set code': 'ELD', 'Collector number': '237', 'Foil': 'foil', 'Language': 'en', 'Quantity': 1},
        ]
        # Sales for each card
        sales = [
            {'Name': c['Name'], 'Set code': c['Set code'], 'Collector number': c['Collector number'], 'Foil': c['Foil'], 'Language': c['Language'], 'Quantity': 1} for c in inv
        ]
        updated, log = remove_sold_cards_from_inventory(inv, sales)
        # All should be removed
        for entry in log:
            self.assertEqual(entry['action'], 'removed', f"Failed for {entry['sale']}: {entry['reason']}")

    def test_sale_name_with_foil_normal_suffix(self):
        # Inventory contains 'Bribery', 'Bedevil', etc. as normal
        inventory = [
            {'Name': 'Bribery', 'Set code': '8ED', 'Collector number': '80', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Bedevil', 'Set code': 'RNA', 'Collector number': '157', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Agonasaur Rex', 'Set code': 'MOM', 'Collector number': '123', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Jacob Frye', 'Set code': 'UBB', 'Collector number': '1', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Legacy Weapon', 'Set code': 'DOM', 'Collector number': '218', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Eliminate', 'Set code': 'M21', 'Collector number': '94', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
            {'Name': "Chef's Kiss", 'Set code': 'MH2', 'Collector number': '117', 'Foil': 'normal', 'Language': 'en', 'Quantity': 1},
        ]
        # Sales with ' normal' at the end of the name
        sales = [
            {'Name': 'Bribery normal', 'Set code': '8ED', 'Collector number': '80', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Bedevil normal', 'Set code': 'RNA', 'Collector number': '157', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Agonasaur Rex normal', 'Set code': 'MOM', 'Collector number': '123', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Jacob Frye normal', 'Set code': 'UBB', 'Collector number': '1', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Legacy Weapon normal', 'Set code': 'DOM', 'Collector number': '218', 'Language': 'en', 'Quantity': 1},
            {'Name': 'Eliminate normal', 'Set code': 'M21', 'Collector number': '94', 'Language': 'en', 'Quantity': 1},
            {'Name': "Chef's Kiss normal", 'Set code': 'MH2', 'Collector number': '117', 'Language': 'en', 'Quantity': 1},
        ]
        # Simulate the parser splitting name/foil
        from ManaBox_Enhancer.logic.whatnot_packing_slip_parser import WhatnotPackingSlipParser
        parser = WhatnotPackingSlipParser()
        fixed_sales = []
        for sale in sales:
            name, foil = parser._split_name_foil(sale['Name'])
            fixed = dict(sale)
            fixed['Name'] = name
            fixed['Foil'] = foil or 'normal'
            fixed_sales.append(fixed)
        updated, log = remove_sold_cards_from_inventory(inventory, fixed_sales)
        for entry in log:
            self.assertEqual(entry['action'], 'removed', f"Failed for {entry['sale']}: {entry['reason']}")

if __name__ == '__main__':
    unittest.main() 