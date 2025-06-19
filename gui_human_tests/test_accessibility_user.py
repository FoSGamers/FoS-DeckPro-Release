import pyautogui
import subprocess
import time
import os

proc = subprocess.Popen(['python3', 'main.py'])
time.sleep(5)

screenshots_dir = 'screenshots_accessibility_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'Screenshot: {fname}')

try:
    # Tab to File menu and open
    for _ in range(3):
        pyautogui.press('tab')
        time.sleep(0.2)
    pyautogui.press('enter')
    snap('file_menu_keyboard')
    # Tab to Add Card and open
    for _ in range(5):
        pyautogui.press('tab')
        time.sleep(0.2)
    pyautogui.press('enter')
    snap('add_card_keyboard')
    # Type card info
    pyautogui.write('Forest', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('LEA', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('3', interval=0.1)
    pyautogui.press('enter')
    snap('card_added_keyboard')
finally:
    proc.terminate()
    print('Accessibility user test complete.') 