import mss
import base64
from io import BytesIO
from PIL import Image
import cv2
import pytesseract
import numpy as np
import requests
import pyautogui
import json
import re

def capture_screen():
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        print("Took screenshot")
        
        return img_base64

def ask_llm(task, image):
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "deepseek-r1:14b",
        "prompt": f"""
            You are an AI assistant that controls a computer. Given the screen text and UI elements, perform this task:
            Task: {task}
            Images: {[image]}
            Details: Provide just the executable Python automation code with no additional statements, explanations, or extra characters
            that performs the task using the following methods to click and type to interact with the GUI. Only think for a maximum
            of two iterations and/or 10 seconds, whichever is lowest. Use the provided images of my screen to determine the location
            the item described in the task. Include all necessary package imports.
            
            def click_at(x, y):
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                print("Clicked")

            def type_text(text):
                pyautogui.write(text, interval=0.1)
                print("Typed")
            """
        }

    output = ""
    with requests.post(url, json=data, stream=True) as response:
        for line in response.iter_lines():
            if line:
                try:
                    output += json.loads(line.decode("utf-8"))['response']
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)

    print(f"Response: {output}")

    return output

def execute_llm_code(code):
    cleaned_code = str(code).lstrip("```python").rstrip("```")
    print(f"Cleaned code: {cleaned_code}")
    exec(cleaned_code)

def ai_agent(task):
    screenshot = capture_screen()
    response = ask_llm(task, screenshot)
    llm_code = re.search(r'python\s*([\s\S]+?)```', response, re.DOTALL).group(1).strip()
    
    print("Executing Code from LLM:")
    print(llm_code)
    
    execute_llm_code(llm_code)

ai_agent("Open the Chrome browser on Windows 11 and a 2560 x 1440 monitor, and search for 'Python AI automation'.")
