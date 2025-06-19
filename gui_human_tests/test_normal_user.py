import pyautogui
import subprocess
import time
import os

# Launch the app
proc = subprocess.Popen(['python3', 'main.py'])
time.sleep(5)  # Wait for app to launch

screenshots_dir = 'screenshots_normal_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'Screenshot: {fname}')

try:
    # Click File menu (assumes top left, adjust as needed)
    pyautogui.moveTo(60, 40, duration=0.5)
    pyautogui.click()
    time.sleep(1)
    snap('file_menu_open')

    # Click 'Add Card' (assume it's at a certain position, adjust as needed)
    pyautogui.moveTo(100, 120, duration=0.5)
    pyautogui.click()
    time.sleep(1)
    snap('add_card_dialog')

    # Type card name
    pyautogui.write('Lightning Bolt', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('LEA', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('1', interval=0.1)
    snap('add_card_filled')
    pyautogui.press('enter')
    time.sleep(1)
    snap('card_added')

    # Save inventory (assume File > Save is at a certain position)
    pyautogui.moveTo(60, 40, duration=0.5)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.moveTo(60, 80, duration=0.5)
    pyautogui.click()
    time.sleep(1)
    snap('inventory_saved')

finally:
    proc.terminate()
    print('Test complete.') 