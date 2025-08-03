from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import time
import mtranslate as mt

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# Write Voice.html with updated language setting
html_code = f'''<!DOCTYPE html>
<html lang="en">
<head><title>Speech Recognition</title></head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {{
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '{InputLanguage}';
            recognition.continuous = true;

            recognition.onresult = function(event) {{
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            }};

            recognition.onend = function() {{
                recognition.start();
            }};
            recognition.start();
        }}

        function stopRecognition() {{
            recognition.stop();
            output.innerHTML = "";
        }}
    </script>
</body>
</html>
'''

os.makedirs("Data", exist_ok=True)
with open("Data/Voice.html", "w", encoding='utf-8') as file:
    file.write(html_code)

# Chrome options
chrome_options = Options()
chrome_options.binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0 Safari/537.36"
chrome_options.add_argument(f"user-agent={user_agent}")

# Persist Chrome profile to save mic permission
profile_path = os.path.join(os.getcwd(), "ChromeProfile")
chrome_options.add_argument(f"user-data-dir={profile_path}")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

def SetAssistantStatus(Status):
    with open('Frontend/Files/Status.data', "w", encoding='utf-8') as file:
        file.write(Status)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        new_query = new_query.rstrip(".?!") + "?"
    else:
        new_query = new_query.rstrip(".?!") + "."

    return new_query.capitalize()

def UniversalTranslator(Text):
    return mt.translate(Text, "en", "auto").capitalize()

def SpeechRecognition():
    driver.get("http://127.0.0.1:5000/")
    time.sleep(2)  # Allow the page to fully load
    driver.find_element(By.ID, "start").click()

    while True:
        try:
            text = driver.find_element(By.ID, "output").text
            if text:
                driver.find_element(By.ID, "end").click()

                if InputLanguage.lower().startswith("en"):
                    return QueryModifier(text)
                else:
                    SetAssistantStatus("Translating...")
                    return QueryModifier(UniversalTranslator(text))
        except Exception:
            pass

if __name__== "_main_":
    while True:
        result = SpeechRecognition()
        print(result)