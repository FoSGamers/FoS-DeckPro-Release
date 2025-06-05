import unittest
import tempfile
import os
import shutil
from ManaBox_Enhancer.utils.packing_slip_file_manager import find_new_packing_slips, move_and_rename_packing_slip, sanitize_filename

class TestPackingSlipFileManager(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.done_dir = os.path.join(self.tempdir, 'done')
        os.makedirs(self.done_dir, exist_ok=True)
        # Create some PDFs
        self.pdf1 = os.path.join(self.tempdir, 'slip1.pdf')
        self.pdf2 = os.path.join(self.tempdir, 'slip2.pdf')
        with open(self.pdf1, 'w') as f:
            f.write('test')
        with open(self.pdf2, 'w') as f:
            f.write('test')
        # Create a PDF in done
        self.done_pdf = os.path.join(self.done_dir, 'done.pdf')
        with open(self.done_pdf, 'w') as f:
            f.write('done')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_find_new_packing_slips(self):
        found = find_new_packing_slips(self.tempdir)
        self.assertIn(self.pdf1, found)
        self.assertIn(self.pdf2, found)
        self.assertNotIn(self.done_pdf, found)

    def test_move_and_rename_packing_slip(self):
        show_date = '2024-06-01'
        show_title = 'Test Show: Special/Characters?*'
        new_path = move_and_rename_packing_slip(self.pdf1, show_date, show_title, self.done_dir)
        self.assertTrue(os.path.exists(new_path))
        self.assertTrue(new_path.startswith(self.done_dir))
        self.assertIn('2024-06-01', new_path)
        self.assertIn('Test_Show_SpecialCharacters', new_path)

    def test_sanitize_filename(self):
        s = 'Test:Show/Name*?<>|'
        sanitized = sanitize_filename(s)
        self.assertNotIn(':', sanitized)
        self.assertNotIn('/', sanitized)
        self.assertNotIn('*', sanitized)
        self.assertNotIn('?', sanitized)
        self.assertNotIn('<', sanitized)
        self.assertNotIn('>', sanitized)
        self.assertNotIn('|', sanitized)
        self.assertIn('TestShowName', sanitized)

if __name__ == '__main__':
    unittest.main() 