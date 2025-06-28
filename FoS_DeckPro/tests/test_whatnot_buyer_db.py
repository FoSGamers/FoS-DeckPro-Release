import unittest
import tempfile
import os
import json
from FoS_DeckPro.logic.whatnot_buyer_db import WhatnotBuyerDB

class TestWhatnotBuyerDB(unittest.TestCase):
    def setUp(self):
        self.tempfile = tempfile.NamedTemporaryFile(delete=False)
        self.db = WhatnotBuyerDB(db_path=self.tempfile.name)

    def tearDown(self):
        self.tempfile.close()
        os.unlink(self.tempfile.name)

    def test_add_and_get_buyer(self):
        buyer = {'name': 'Alice', 'username': 'alice123', 'address': '123 Main St.'}
        sale = {'Name': 'Test Card', 'Quantity': 2, 'Price': 3.5}
        show = {'title': 'Test Show', 'date': '2024-01-01'}
        self.db.add_purchase(buyer, sale, show)
        b = self.db.get_buyer('alice123')
        self.assertEqual(b['name'], 'Alice')
        self.assertEqual(b['username'], 'alice123')
        self.assertEqual(b['address'], '123 Main St.')
        self.assertEqual(b['total_cards'], 2)
        self.assertEqual(b['total_spent'], 7.0)
        self.assertEqual(b['first_purchase'], '2024-01-01')
        self.assertEqual(b['last_purchase'], '2024-01-01')
        self.assertEqual(len(b['purchases']), 1)

    def test_update_buyer_multiple_purchases(self):
        buyer = {'name': 'Bob', 'username': 'bob', 'address': '456 Oak Ave.'}
        sale1 = {'Name': 'Card1', 'Quantity': 1, 'Price': 2.0}
        sale2 = {'Name': 'Card2', 'Quantity': 3, 'Price': 1.0}
        show1 = {'title': 'Show1', 'date': '2024-01-01'}
        show2 = {'title': 'Show2', 'date': '2024-02-01'}
        self.db.add_purchase(buyer, sale1, show1)
        self.db.add_purchase(buyer, sale2, show2)
        b = self.db.get_buyer('bob')
        self.assertEqual(b['total_cards'], 4)
        self.assertEqual(b['total_spent'], 5.0)
        self.assertEqual(b['first_purchase'], '2024-01-01')
        self.assertEqual(b['last_purchase'], '2024-02-01')
        self.assertEqual(len(b['purchases']), 2)

    def test_get_top_buyers(self):
        buyers = [
            {'name': 'A', 'username': 'a', 'address': 'x'},
            {'name': 'B', 'username': 'b', 'address': 'y'},
            {'name': 'C', 'username': 'c', 'address': 'z'}
        ]
        sales = [
            {'Name': 'Card', 'Quantity': 1, 'Price': 10.0},
            {'Name': 'Card', 'Quantity': 2, 'Price': 5.0},
            {'Name': 'Card', 'Quantity': 3, 'Price': 2.0}
        ]
        show = {'title': 'Show', 'date': '2024-01-01'}
        for b, s in zip(buyers, sales):
            self.db.add_purchase(b, s, show)
        top = self.db.get_top_buyers(2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]['username'], 'a')
        self.assertEqual(top[1]['username'], 'b')

if __name__ == '__main__':
    unittest.main() 