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

WEB_URL = os.getenv("PHASESYNTH_URL", "http://localhost:3000")
SCREENSHOT_PATH = "test_web_gui_screenshot.png"
LOG_PATH = f"test_web_human_gui_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def analyze_screenshot_with_openai(image_path, test_name):
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
    
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    prompt = (
        f"Analyze this screenshot of the PhaseSynth Ultra+ web app. "
        f"Describe what you see in detail. Is the React app loaded? "
        f"Are there any UI elements visible? Reply with JSON: "
        f"{{\"loaded\": true/false, \"elements\": [list], \"description\": \"...\", \"issues\": [list]}}"
    )
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a web app debugging assistant."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]}
            ],
            max_tokens=500
        )
        
        import re, json as pyjson
        text = response.choices[0].message.content
        try:
            json_str = re.search(r'\{.*\}', text, re.DOTALL).group(0)
            result = pyjson.loads(json_str)
        except Exception:
            result = {"loaded": False, "elements": [], "description": text, "issues": ["Could not parse response"]}
        return result, text
    except Exception as e:
        return {"loaded": False, "elements": [], "description": f"Error: {str(e)}", "issues": [str(e)]}, str(e)

async def run_test():
    log = open(LOG_PATH, "w")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Enable console logging
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: console_logs.append(f"ERROR: {err}"))
        
        print(f"[INFO] Navigating to {WEB_URL}")
        log.write(f"[INFO] Navigating to {WEB_URL}\n")
        
        await page.goto(WEB_URL)
        await asyncio.sleep(10)  # Wait longer for React to load
        
        # Check page title and content
        title = await page.title()
        print(f"[INFO] Page title: {title}")
        log.write(f"[INFO] Page title: {title}\n")
        
        # Check if React root is populated
        try:
            root_content = await page.inner_html("#root")
            print(f"[INFO] Root content length: {len(root_content)}")
            log.write(f"[INFO] Root content length: {len(root_content)}\n")
            if len(root_content) > 0:
                print(f"[INFO] Root content preview: {root_content[:200]}...")
                log.write(f"[INFO] Root content preview: {root_content[:200]}...\n")
        except Exception as e:
            print(f"[ERROR] Could not get root content: {e}")
            log.write(f"[ERROR] Could not get root content: {e}\n")
        
        # Log console messages
        if console_logs:
            print(f"[CONSOLE] {len(console_logs)} messages:")
            log.write(f"[CONSOLE] {len(console_logs)} messages:\n")
            for msg in console_logs:
                print(f"  {msg}")
                log.write(f"  {msg}\n")
        
        # Take screenshot
        await page.screenshot(path=SCREENSHOT_PATH)
        print(f"[INFO] Screenshot saved: {SCREENSHOT_PATH}")
        log.write(f"[INFO] Screenshot saved: {SCREENSHOT_PATH}\n")
        
        # Analyze with OpenAI
        result, raw_response = analyze_screenshot_with_openai(SCREENSHOT_PATH, "debug_test")
        print(f"[OPENAI] {result}")
        log.write(f"[OPENAI] {result}\n[RAW]\n{raw_response}\n")
        
        await browser.close()
        log.close()
        print("[DONE] Test complete.")

if __name__ == "__main__":
    asyncio.run(run_test()) 