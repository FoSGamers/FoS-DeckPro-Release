import pyautogui
import subprocess
import time
import os

proc = subprocess.Popen(['python3', 'main.py'])
time.sleep(5)

screenshots_dir = 'screenshots_power_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'Screenshot: {fname}')

try:
    # Add card via shortcut (assume Cmd+N)
    pyautogui.hotkey('command', 'n')
    time.sleep(0.5)
    snap('add_card_shortcut')
    pyautogui.write('Island', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('LEA', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('2', interval=0.1)
    pyautogui.press('enter')
    time.sleep(0.5)
    snap('card_added')
    # Save via shortcut (Cmd+S)
    pyautogui.hotkey('command', 's')
    time.sleep(0.5)
    snap('saved_shortcut')
    # Undo/redo via shortcuts
    pyautogui.hotkey('command', 'z')
    snap('undo_shortcut')
    pyautogui.hotkey('command', 'shift', 'z')
    snap('redo_shortcut')
    # Bulk select and delete
    pyautogui.hotkey('command', 'a')
    pyautogui.press('delete')
    snap('bulk_delete')
finally:
    proc.terminate()
    print('Power user test complete.') 