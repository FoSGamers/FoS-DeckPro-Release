import pyautogui
import subprocess
import time
import os

proc = subprocess.Popen(['python3', 'main.py'])
time.sleep(5)

screenshots_dir = 'screenshots_curiosity_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'Screenshot: {fname}')

try:
    # Open File, Edit, View, Tools menus (assume positions)
    menu_positions = [(60, 40), (120, 40), (180, 40), (240, 40)]
    for i, pos in enumerate(menu_positions):
        pyautogui.moveTo(*pos, duration=0.3)
        pyautogui.click()
        time.sleep(0.5)
        snap(f'menu_{i}_open')
    # Click visible buttons (assume some positions)
    button_positions = [(200, 120), (300, 120), (400, 120), (500, 120)]
    for i, pos in enumerate(button_positions):
        pyautogui.moveTo(*pos, duration=0.3)
        pyautogui.click()
        time.sleep(0.5)
        snap(f'button_{i}_clicked')
    # Open dialogs (assume some positions)
    dialog_positions = [(600, 120), (700, 120)]
    for i, pos in enumerate(dialog_positions):
        pyautogui.moveTo(*pos, duration=0.3)
        pyautogui.click()
        time.sleep(0.5)
        snap(f'dialog_{i}_opened')
finally:
    proc.terminate()
    print('Curiosity user test complete.') 