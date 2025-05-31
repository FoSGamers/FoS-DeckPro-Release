import unittest
from ManaBox_Enhancer.logic.whatnot_packing_slip_parser import WhatnotPackingSlipParser

def always_true(_):
    return True

def always_false(_):
    return False

SAMPLE_TEXT = '''
--- PAGE 1 ---
Whatnot - Packing Slip
From: fosgamers
Orders #383155775
Livestream Name: Rise & Shine w/FoSGamers | 1K+ Singles
Livestream Date: 25 May, 2025
Ships to:
Aaron solomon (aarsolo) 20 Deborah Rd. Syosset, NY. 11791-6721. US
Tracking code: 00310110084508763652
Total: 1 item
Name: Armory Paladin normal Quantity: 1
Description: Foil: normal Collector number: 337 Set name: Fallout Set code: PIP Rarity: rare Language: ja
Attributes:
Order: 383155775
Price: $1.00 Subtotal: $1.00
--- PAGE 2 ---
Whatnot - Packing Slip
From: fosgamers
Orders #383196219
Livestream Name: Rise & Shine w/FoSGamers | 1K+ Singles
Livestream Date: 25 May, 2025
Ships to:
Robert Goettman (bogoet_36) 123 Orchard Dr. Beaver, PA. 15009-1117. US
Tracking code: 92001903478427300239622704
Total: 1 item
Name: NotACardItem Quantity: 1
Description: Some non-card item
Attributes:
Order: 383196219
Price: $1.00 Subtotal: $1.00
'''

class TestWhatnotPackingSlipParser(unittest.TestCase):
    def test_parse_card_sales(self):
        parser = WhatnotPackingSlipParser(card_name_validator=always_true)
        buyers = parser.parse(SAMPLE_TEXT)
        self.assertEqual(len(buyers), 2)
        buyer1 = buyers[0]
        self.assertEqual(buyer1['buyer']['name'], 'Aaron solomon')
        self.assertEqual(buyer1['buyer']['username'], 'aarsolo')
        self.assertIn('Armory Paladin normal', [s['Name'] for s in buyer1['sales']])
        self.assertEqual(buyer1['show']['title'], 'Rise & Shine w/FoSGamers | 1K+ Singles')
        self.assertEqual(buyer1['show']['date'], '25 May, 2025')
        card = buyer1['sales'][0]
        self.assertEqual(card['Quantity'], 1)
        self.assertEqual(card['Foil'], 'normal')
        self.assertEqual(card['Collector number'], '337')
        self.assertEqual(card['Set name'], 'Fallout')
        self.assertEqual(card['Set code'], 'PIP')
        self.assertEqual(card['Rarity'], 'rare')
        self.assertEqual(card['Language'], 'ja')

    def test_ignore_non_card_items(self):
        parser = WhatnotPackingSlipParser(card_name_validator=always_false)
        buyers = parser.parse(SAMPLE_TEXT)
        # No sales should be parsed since validator always returns False
        for buyer in buyers:
            self.assertEqual(len(buyer['sales']), 0)

    def test_missing_fields(self):
        text = '''--- PAGE 1 ---\nLivestream Name: Test Show\nLivestream Date: 1 Jan, 2024\nShips to:\nJane Doe (janed) 123 Main St.\nName: Test Card Quantity: 2\nDescription: Foil: normal\n'''
        parser = WhatnotPackingSlipParser(card_name_validator=always_true)
        buyers = parser.parse(text)
        self.assertEqual(len(buyers), 1)
        card = buyers[0]['sales'][0]
        self.assertEqual(card['Name'], 'Test Card')
        self.assertEqual(card['Quantity'], 2)
        self.assertEqual(card['Foil'], 'normal')
        # Missing fields should not raise errors
        self.assertNotIn('Set name', card)
        self.assertNotIn('Set code', card)

if __name__ == '__main__':
    unittest.main() 