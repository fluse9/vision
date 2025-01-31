import mss
from PIL import Image
import pyautogui
import json
import re
import moondream as md
from datetime import datetime
import os
from openai import OpenAI
from time import sleep
from dotenv import load_dotenv

load_dotenv()

pyautogui.FAILSAFE = False 
moondream = md.vl(api_key=os.getenv('MOONDREAM_API_KEY'))
client = OpenAI(
    api_key=os.getenv('ALIBABA_CLOUD_MODEL_API_KEY'), 
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
)

def capture_screen():
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])
        img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(os.getcwd(), f"screenshot_{timestamp}.jpg")
        
        img.save(file_path, "JPEG")
        print(f"Screenshot saved at: {file_path}")

        return file_path
    
def ask_director_agent(prompt):
    completion = client.chat.completions.create(
        model="qwen2.5-vl-72b-instruct",
        messages=[
            {'role': 'system', 'content': 'You are an AI assistant that takes a user prompt and processes it into a Python dict with a task property and an item property.'},
            {'role': 'user', 'content': f"""
                Prompt: {prompt}

                Details: Process the provided prompt and determine the "task" to be completed and the item
                on the computer's user interface that needs to be located on the screen to complete the action. Include some details
                about the item's whereabouts from the prompt if possible in the item. Provide just a
                JSON string with the "task" and "item" properties and with no additional statements, explanations, or
                extra characters. If there is no relevant item or no actions are required on the user interface, set the item
                property's value to null. Both the "task" and "item" properties' values should be strings.
                """
            }
        ]
    )

    output = json.loads(completion.model_dump()['choices'][0]['message']['content'])
    print(f"Response: {output}")

    return (output['task'], output['item'])

def ask_image_agent(image_path, item):
    image = Image.open(image_path)
    points = moondream.point(image, item)
    print(f"Points: {points}")
    return points

def ask_task_agent(task, coordinates):
    completion = client.chat.completions.create(
        model="qwen2.5-vl-72b-instruct",
        messages=[
            {'role': 'system', 'content': 'You are an AI assistant that controls a computer.'},
            {'role': 'user', 'content': f"""
                Given the provided normalized x and y coordinates, perform this task:

                Task: {task}
                Coordinates: {coordinates}

                Details: Provide just the executable Python automation code with no additional statements, explanations, or
                extra characters that performs the task using the following methods to click and type to interact with the GUI.
                Include all necessary package imports. To apply the normalized coordinates to the screen's resolution multiply
                x by 2560 and y by 1440 to get the actual x and y coordinates for the cursor. Use sleep as needed to give 
                applications time to load.
                
                def click_at(x, y):
                    pyautogui.moveTo(x, y, duration=0.2)
                    pyautogui.click()
                    print("Clicked")

                def type_text(text):
                    pyautogui.write(text, interval=0.1)
                    print("Typed")
                """
            }
        ]
    )

    output = completion.model_dump()['choices'][0]['message']['content']
    print(f"Response: {output}")

    return output

def execute_llm_code(code):
    cleaned_code = str(code).lstrip("```python").rstrip("```")
    print(f"Cleaned code: {cleaned_code}")
    exec(cleaned_code)

def ai_agent(prompt):
    task, item = ask_director_agent(prompt)
    print(f"Beginning task: {task}")

    screenshot = capture_screen()
    coordinates = ask_image_agent(screenshot, item)
    response = ask_task_agent(task, coordinates)
    llm_code = re.search(r'python\s*([\s\S]+?)```', response, re.DOTALL).group(1).strip()
    
    print("Executing Code from LLM:")
    print(llm_code)
    
    execute_llm_code(llm_code)

while True:
    prompt = input()

    if prompt == 'stop':
        break

    ai_agent(prompt)
    sleep(2)
