#!/usr/bin/env python3
"""
Test OpenAI Vision API with a single screenshot
"""

import os
import time
import pyautogui
import requests
import base64
from PIL import Image
from datetime import datetime

OPENAI_API_KEY = "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"

def resize_image_for_vision(image_path, max_width=800):
    """Resize image to max_width, maintaining aspect ratio, and save as compressed JPEG."""
    try:
        img = Image.open(image_path)
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        
        # Convert to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Save as compressed JPEG
        temp_path = image_path.replace('.png', '_vision.jpg')
        img.save(temp_path, format='JPEG', quality=70, optimize=True)
        
        # Check file size
        file_size = os.path.getsize(temp_path) / (1024 * 1024)  # MB
        print(f"📏 Resized image: {file_size:.2f}MB")
        
        return temp_path
    except Exception as e:
        print(f"⚠️ Image resize failed: {e}")
        return image_path

def test_vision_api(image_path, expected_desc):
    """Test OpenAI Vision API with a single image."""
    try:
        resized_path = resize_image_for_vision(image_path)
        
        # Check if file is still too large
        file_size = os.path.getsize(resized_path) / (1024 * 1024)  # MB
        if file_size > 4:
            return f"Image still too large ({file_size:.2f}MB) for Vision API"
        
        with open(resized_path, "rb") as img_file:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Convert image to base64
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Use the correct GPT-4 Vision API structure
            data = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Does this screenshot show: {expected_desc}? Answer YES or NO and explain briefly."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 150
            }
            
            print("🔄 Sending to OpenAI Vision API...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            print(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return f"✅ SUCCESS: {answer}"
            else:
                return f"❌ ERROR: {response.status_code} - {response.text[:200]}"
                
    except Exception as e:
        return f"❌ EXCEPTION: {str(e)}"

def main():
    print("🧪 Testing OpenAI Vision API")
    print("=" * 40)
    
    # Take a test screenshot
    test_dir = "vision_test"
    os.makedirs(test_dir, exist_ok=True)
    
    screenshot_path = os.path.join(test_dir, f"test_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    print(f"📸 Taking screenshot: {screenshot_path}")
    
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)
    
    # Test Vision API
    expected_desc = "A computer screen with some application or desktop visible"
    result = test_vision_api(screenshot_path, expected_desc)
    
    print(f"\n🎯 Vision API Result:")
    print(result)

if __name__ == "__main__":
    main() 