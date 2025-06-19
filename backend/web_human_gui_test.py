import os
import time
import asyncio
import openai
import base64
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from datetime import datetime

# Load OpenAI API key from .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

WEB_URL = os.getenv("PHASESYNTH_URL", "http://localhost:3000")  # Change as needed
SCREENSHOT_PATH = "web_gui_screenshot.png"
LOG_PATH = f"web_human_gui_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

# --- OpenAI Vision Analysis ---
def analyze_screenshot_with_openai(image_path, test_name):
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
    
    # Convert to base64 for OpenAI API
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    prompt = (
        f"You are an expert UI tester. Given this screenshot, is the PhaseSynth Ultra+ web app in the correct state for the '{test_name}' test? "
        "Are all required elements visible and interactive? Reply with a JSON: {\"ready\": true/false, \"missing\": [list], \"suggestion\": \"...\"}"
    )
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a UI testing assistant."},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
            ]}
        ],
        max_tokens=256
    )
    # Extract JSON from response
    import re, json as pyjson
    text = response.choices[0].message.content
    try:
        json_str = re.search(r'\{.*\}', text, re.DOTALL).group(0)
        result = pyjson.loads(json_str)
    except Exception:
        result = {"ready": False, "missing": [], "suggestion": "Could not parse OpenAI response."}
    return result, text

# --- Human-like Actions ---
async def human_like_type(page, selector, text):
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(0.05 + 0.05 * (os.urandom(1)[0] % 3))  # Random delay

async def human_like_click(page, selector):
    box = await page.locator(selector).bounding_box()
    if box:
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        await page.mouse.move(x, y, steps=15)
        await asyncio.sleep(0.2)
        await page.mouse.click(x, y)
        await asyncio.sleep(0.2)

# --- Main Test Logic ---
async def run_web_human_gui_test():
    log = open(LOG_PATH, "w")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console errors and logs
        console_errors = []
        console_logs = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else console_logs.append(msg.text))
        
        # Listen for page errors
        page.on("pageerror", lambda err: console_errors.append(f"Page error: {err}"))
        
        # Listen for unhandled promise rejections
        page.on("unhandledrejection", lambda err: console_errors.append(f"Unhandled rejection: {err}"))
        
        # Add error event listener to capture any JavaScript errors
        await page.add_init_script("""
            window.addEventListener('error', function(e) {
                console.error('Global error:', e.error);
            });
            window.addEventListener('unhandledrejection', function(e) {
                console.error('Unhandled rejection:', e.reason);
            });
        """)
        
        await page.goto(WEB_URL)
        await asyncio.sleep(10)  # Wait much longer for React to load
        
        # Check if JavaScript is executing at all
        try:
            js_result = await page.evaluate("() => document.readyState")
            log.write(f"[JS] Document ready state: {js_result}\n")
            print(f"[JS] Document ready state: {js_result}")
            
            # Check if the root element exists
            root_exists = await page.evaluate("() => document.getElementById('root') !== null")
            log.write(f"[JS] Root element exists: {root_exists}\n")
            print(f"[JS] Root element exists: {root_exists}")
            
            # Check if any scripts are loaded
            script_count = await page.evaluate("() => document.scripts.length")
            log.write(f"[JS] Script count: {script_count}\n")
            print(f"[JS] Script count: {script_count}")
            
            # Check if main.bundle.js loaded
            main_script_loaded = await page.evaluate("() => Array.from(document.scripts).some(s => s.src.includes('main.bundle.js'))")
            log.write(f"[JS] Main bundle loaded: {main_script_loaded}\n")
            print(f"[JS] Main bundle loaded: {main_script_loaded}")
            
            # Check if the bundle is actually executing by looking for any global variables
            global_vars = await page.evaluate("() => { const globals = []; for (let key in window) { if (key.includes('webpack') || key.includes('React') || key.includes('__')) { globals.push(key); } } return globals.join(', '); }")
            log.write(f"[JS] Global webpack/React vars: {global_vars}\n")
            print(f"[JS] Global webpack/React vars: {global_vars}")
            
            # Check if React is trying to mount
            try:
                react_mounting = await page.evaluate("() => window.React !== undefined")
                log.write(f"[JS] React available: {react_mounting}\n")
                print(f"[JS] React available: {react_mounting}")
                
                # Check if ReactDOM is available
                react_dom_available = await page.evaluate("() => window.ReactDOM !== undefined")
                log.write(f"[JS] ReactDOM available: {react_dom_available}\n")
                print(f"[JS] ReactDOM available: {react_dom_available}")
                
                # Check if the app is trying to mount by looking for the mount call
                try:
                    mount_attempt = await page.evaluate("() => { try { const root = document.getElementById('root'); if (root && window.React && window.ReactDOM) { console.log('Attempting to mount React app...'); return 'React and ReactDOM available, root exists'; } else { return 'Missing React, ReactDOM, or root element'; } } catch (e) { return 'Error during mount attempt: ' + e.message; } }")
                    log.write(f"[JS] Mount attempt: {mount_attempt}\n")
                    print(f"[JS] Mount attempt: {mount_attempt}")
                except Exception as mount_e:
                    log.write(f"[JS] Mount check error: {mount_e}\n")
                    print(f"[JS] Mount check error: {mount_e}")
                
            except Exception as react_e:
                log.write(f"[JS] React check error: {react_e}\n")
                print(f"[JS] React check error: {react_e}")
            
            # Check if there are any global errors
            try:
                global_errors = await page.evaluate("() => window.onerror ? 'onerror handler exists' : 'no onerror handler'")
                log.write(f"[JS] Global error handler: {global_errors}\n")
                print(f"[JS] Global error handler: {global_errors}")
            except:
                log.write("[JS] Could not check global error handler\n")
                print("[JS] Could not check global error handler")
            
            # Check the actual content of the root div
            root_content = await page.evaluate("() => document.getElementById('root').innerHTML")
            log.write(f"[JS] Root content: {root_content}\n")
            print(f"[JS] Root content: {root_content}")
            
            # Check if the root div has any styles that might hide it
            root_style = await page.evaluate("() => window.getComputedStyle(document.getElementById('root')).display")
            log.write(f"[JS] Root display style: {root_style}\n")
            print(f"[JS] Root display style: {root_style}")
            
            # Check if there are any script execution errors
            try:
                script_errors = await page.evaluate("() => { const scripts = document.scripts; const errors = []; for (let script of scripts) { if (script.src && script.src.includes('main.bundle.js')) { console.log('Found main bundle script:', script.src); } } return 'Scripts checked'; }")
                log.write(f"[JS] Script check: {script_errors}\n")
                print(f"[JS] Script check: {script_errors}")
            except Exception as script_e:
                log.write(f"[JS] Script check error: {script_e}\n")
                print(f"[JS] Script check error: {script_e}")
            
        except Exception as e:
            log.write(f"[JS] Error checking JavaScript: {e}\n")
            print(f"[JS] Error checking JavaScript: {e}")
        
        # Log all console messages
        log.write(f"[CONSOLE LOGS] {console_logs}\n")
        log.write(f"[CONSOLE ERRORS] {console_errors}\n")
        print(f"[CONSOLE LOGS] {console_logs}")
        print(f"[CONSOLE ERRORS] {console_errors}")
        
        # Wait for React to mount
        try:
            await page.wait_for_selector("#root", timeout=10000)
            await page.wait_for_function("document.querySelector('#root').children.length > 0", timeout=10000)
        except Exception as e:
            log.write(f"[WARN] React app may not have loaded properly: {e}\n")
            print(f"[WARN] React app may not have loaded properly: {e}")
        
        # Check for JavaScript errors
        if console_errors:
            log.write(f"[ERROR] JavaScript errors found: {console_errors}\n")
            print(f"[ERROR] JavaScript errors found: {console_errors}")
        
        # Take initial screenshot
        await page.screenshot(path=SCREENSHOT_PATH, full_page=True)
        log.write(f"[INFO] Screenshot saved: {SCREENSHOT_PATH}\n")
        print(f"[INFO] Screenshot saved: {SCREENSHOT_PATH}")
        
        # Analyze screenshot with OpenAI Vision
        test_name = "initial_load"
        result, raw_response = analyze_screenshot_with_openai(SCREENSHOT_PATH, test_name)
        log.write(f"[OPENAI] {result}\n[RAW]\n{raw_response}\n")
        print(f"[OPENAI] {result}")
        
        # If not ready, try to auto-correct
        retries = 0
        while not result.get("ready", False) and retries < 3:
            print(f"[WARN] GUI not ready: {result.get('suggestion')}")
            log.write(f"[WARN] GUI not ready: {result.get('suggestion')}\n")
            # Try to refresh or follow suggestion
            await page.reload()
            await asyncio.sleep(5)  # Wait longer after reload
            await page.screenshot(path=SCREENSHOT_PATH, full_page=True)
            result, raw_response = analyze_screenshot_with_openai(SCREENSHOT_PATH, test_name)
            retries += 1
        if not result.get("ready", False):
            print("[FAIL] Could not get GUI into correct state after retries.")
            log.write("[FAIL] Could not get GUI into correct state after retries.\n")
            await browser.close()
            log.close()
            return
        print("[PASS] GUI is in correct state. Proceeding with human-like actions.")
        log.write("[PASS] GUI is in correct state. Proceeding.\n")
        
        # Example: Human-like login (customize selectors as needed)
        # await human_like_type(page, "input[name='username']", "testuser")
        # await human_like_type(page, "input[name='password']", "password123")
        # await human_like_click(page, "button[type='submit']")
        # Add more steps as needed for your app
        
        # Take another screenshot after action
        await page.screenshot(path="web_gui_post_action.png")
        log.write("[INFO] Post-action screenshot saved.\n")
        print("[INFO] Post-action screenshot saved.")
        
        await browser.close()
        log.close()
        print("[DONE] Web human GUI test complete.")

if __name__ == "__main__":
    asyncio.run(run_web_human_gui_test()) 