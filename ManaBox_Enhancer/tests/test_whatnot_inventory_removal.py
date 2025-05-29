import unittest
from ManaBox_Enhancer.logic.whatnot_inventory_removal import remove_sold_cards_from_inventory

class TestWhatnotInventoryRemoval(unittest.TestCase):
    def setUp(self):
        self.inventory = [
            {'Name': 'Card A', 'Set code': 'SET1', 'Collector number': '1', 'Language': 'en', 'Foil': 'normal', 'Quantity': 2},
            {'Name': 'Card B', 'Set code': 'SET2', 'Collector number': '2', 'Language': 'en', 'Foil': 'foil', 'Quantity': 1},
            {'Name': 'Card C', 'Set code': 'SET3', 'Collector number': '3', 'Language': 'en', 'Foil': 'normal', 'Quantity': 5},
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
        self.assertEqual(len(updated), 3)
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

if __name__ == '__main__':
    unittest.main() 