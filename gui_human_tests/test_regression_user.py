import pyautogui
import subprocess
import time
import os

proc = subprocess.Popen(['python3', 'main.py'])
time.sleep(5)

screenshots_dir = 'screenshots_regression_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'Screenshot: {fname}')

try:
    # Add card
    pyautogui.moveTo(100, 120, duration=0.5)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.write('Swamp', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('LEA', interval=0.1)
    pyautogui.press('tab')
    pyautogui.write('4', interval=0.1)
    pyautogui.press('enter')
    snap('card_added')
    # Undo
    pyautogui.hotkey('command', 'z')
    snap('undo')
    # Redo
    pyautogui.hotkey('command', 'shift', 'z')
    snap('redo')
    # Save
    pyautogui.hotkey('command', 's')
    snap('save')
    # Load (assume File > Open at position)
    pyautogui.moveTo(60, 40, duration=0.5)
    pyautogui.click()
    time.sleep(0.5)
    pyautogui.moveTo(60, 100, duration=0.5)
    pyautogui.click()
    time.sleep(1)
    snap('load')
    # Repeat add/undo/redo
    for i in range(2):
        pyautogui.moveTo(100, 120, duration=0.5)
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.write(f'Plains{i}', interval=0.1)
        pyautogui.press('tab')
        pyautogui.write('LEA', interval=0.1)
        pyautogui.press('tab')
        pyautogui.write(str(i+5), interval=0.1)
        pyautogui.press('enter')
        snap(f'card_added_{i}')
        pyautogui.hotkey('command', 'z')
        snap(f'undo_{i}')
        pyautogui.hotkey('command', 'shift', 'z')
        snap(f'redo_{i}')
finally:
    proc.terminate()
    print('Regression user test complete.') 