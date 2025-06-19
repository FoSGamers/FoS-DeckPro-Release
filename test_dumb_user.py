import pyautogui
import subprocess
import time
import os
import random

print("🚀 Starting Dumb User Test")

proc = subprocess.Popen(['python3', '../main.py'])
time.sleep(8)

screenshots_dir = 'screenshots_dumb_user'
os.makedirs(screenshots_dir, exist_ok=True)

def snap(name):
    fname = os.path.join(screenshots_dir, f'{name}.png')
    pyautogui.screenshot(fname)
    print(f'📸 Screenshot: {fname}')

try:
    for i in range(15):
        x = random.randint(50, 1200)
        y = random.randint(50, 800)
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()
        time.sleep(random.uniform(0.2, 1.0))
        snap(f'random_click_{i}')
        if random.random() < 0.3:
            pyautogui.write('asdf!@#123', interval=0.05)
            pyautogui.press('enter')
            snap(f'random_typing_{i}')
        # Try to close dialogs (ESC or click top-right)
        if random.random() < 0.2:
            pyautogui.press('esc')
            snap(f'pressed_esc_{i}')
            pyautogui.moveTo(1300, 60, duration=0.2)
            pyautogui.click()
            snap(f'clicked_close_{i}')
    print("Test completed successfully!")
except Exception as e:
    print(f"❌ Test failed: {e}")
finally:
    print("Terminating app...")
    proc.terminate()
    print("✅ Dumb user test complete.") 