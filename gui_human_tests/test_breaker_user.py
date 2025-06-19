import pyautogui
import subprocess
import time
import os

proc = subprocess.Popen(['python3', 'main.py'])
time.sleep(5)

screenshots_dir = 'screenshots_breaker_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'Screenshot: {fname}')

try:
    # Rapid double-clicks on File menu
    for i in range(5):
        pyautogui.moveTo(60, 40, duration=0.1)
        pyautogui.click(clicks=2, interval=0.05)
        time.sleep(0.2)
        snap(f'file_menu_doubleclick_{i}')
    # Open/close dialogs rapidly
    for i in range(3):
        pyautogui.moveTo(100, 120, duration=0.1)
        pyautogui.click()
        time.sleep(0.2)
        pyautogui.press('esc')
        snap(f'open_close_dialog_{i}')
    # Enter invalid data in add card
    pyautogui.moveTo(100, 120, duration=0.2)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.write('!@#$%^&*()', interval=0.05)
    pyautogui.press('tab')
    pyautogui.write('???', interval=0.05)
    pyautogui.press('tab')
    pyautogui.write('-999', interval=0.05)
    snap('invalid_card_data')
    pyautogui.press('enter')
    time.sleep(0.5)
    snap('after_invalid_card')
    # Try to delete all cards (assume select all and delete)
    pyautogui.hotkey('command', 'a')
    time.sleep(0.2)
    pyautogui.press('delete')
    snap('delete_all_cards')
    # Spam undo/redo
    for i in range(5):
        pyautogui.hotkey('command', 'z')
        time.sleep(0.1)
        snap(f'undo_{i}')
    for i in range(5):
        pyautogui.hotkey('command', 'shift', 'z')
        time.sleep(0.1)
        snap(f'redo_{i}')
finally:
    proc.terminate()
    print('Breaker user test complete.') 