import os
import re
import shutil
from typing import List

def find_new_packing_slips(folder: str) -> List[str]:
    """
    Return a list of PDF file paths in the folder that are not in the 'done' subfolder.
    """
    done_folder = os.path.join(folder, 'done')
    os.makedirs(done_folder, exist_ok=True)
    all_pdfs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(folder, f))]
    return [f for f in all_pdfs if not f.startswith(done_folder)]

def move_and_rename_packing_slip(src_path: str, show_date: str, show_title: str, done_folder: str) -> str:
    """
    Move and rename the PDF to the done folder as 'YYYY-MM-DD ShowTitle.pdf'.
    Returns the new file path.
    """
    os.makedirs(done_folder, exist_ok=True)
    date_part = sanitize_filename(show_date.replace(',', '').replace(' ', '-'))
    title_part = sanitize_filename(show_title)[:60]  # Limit length for safety
    new_name = f"{date_part} {title_part}.pdf"
    dst_path = os.path.join(done_folder, new_name)
    # Avoid overwrite
    i = 1
    base_dst = dst_path
    while os.path.exists(dst_path):
        dst_path = base_dst.replace('.pdf', f'_{i}.pdf')
        i += 1
    shutil.move(src_path, dst_path)
    return dst_path

def sanitize_filename(s: str) -> str:
    """
    Remove or replace characters not safe for filenames.
    """
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    s = s.strip().replace(' ', '_')
    return s 