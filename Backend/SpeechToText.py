from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import mtranslate as mt
import time

# =========================================================
# PATHS
# =========================================================
BASE_DIR = os.getcwd()
FRONTEND_FILES = os.path.join(BASE_DIR, "Frontend", "Files")

LANG_FILE = os.path.join(FRONTEND_FILES, "Language.data")
MIC_FILE = os.path.join(FRONTEND_FILES, "Mic.data")
STATUS_FILE = os.path.join(FRONTEND_FILES, "Status.data")

# =========================================================
# STATE HELPERS (NO GUI IMPORTS)
# =========================================================
def GetLanguage():
    try:
        with open(LANG_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "en-IN"


def GetMicrophoneStatus():
    try:
        with open(MIC_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "False"


def SetAssistantStatus(status):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(status)
    except:
        pass

# =========================================================
# HTML TEMPLATE (NO AUTO-RESTART BUG)
# =========================================================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>

    <script>
        const output = document.getElementById('output');
        let recognition = null;

        function startRecognition() {
            recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = '{LANG_CODE}';
            recognition.continuous = true;
            recognition.interimResults = false;

            recognition.onresult = function(event) {
                const transcript =
                    event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript;
            };

            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.onend = null;
                recognition.stop();
            }
            output.innerHTML = "";
        }
    </script>
</body>
</html>'''

# =========================================================
# SELENIUM SETUP
# =========================================================
chrome_options = Options()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--headless=new")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# =========================================================
# TEXT UTILITIES
# =========================================================
def QueryModifier(query):
    query = query.lower().strip()
    starters = [
        "how", "what", "who", "where", "when", "why",
        "which", "whose", "whom", "can you", "can i"
    ]

    if any(query.startswith(s) for s in starters):
        return query.rstrip(".!?") + "?"
    else:
        return query.rstrip(".!?") + "."

def UniversalTranslator(text, src_lang=None):
    translated = mt.translate(text, "en", src_lang if src_lang else "auto")
    return translated.capitalize()

# =========================================================
# MAIN SPEECH FUNCTION
# =========================================================
def SpeechRecognition():
    InputLanguage = GetLanguage()

    html_code = HTML_TEMPLATE.replace("{LANG_CODE}", InputLanguage)
    html_path = os.path.join(BASE_DIR, "DataVoice.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_code)

    driver.get(f"file:///{html_path}")
    driver.find_element(By.ID, "start").click()

    SetAssistantStatus("Listening …")

    while True:
        # 🛑 HARD STOP if mic OFF
        if GetMicrophoneStatus().lower() == "false":
            SetAssistantStatus("Available …")
            return "", InputLanguage.split("-")[0]

        try:
            text = driver.find_element(By.ID, "output").text

            if text.strip():
                driver.find_element(By.ID, "end").click()

                detected_lang = InputLanguage.split("-")[0].lower()

                if detected_lang == "en":
                    final_text = QueryModifier(
                        UniversalTranslator(text, detected_lang)
                    )
                else:
                    SetAssistantStatus("Translating …")
                    final_text = QueryModifier(
                        UniversalTranslator(text, detected_lang)
                    )

                return final_text, detected_lang

        except Exception:
            time.sleep(0.05)

# =========================================================
# TEST MODE
# =========================================================
if __name__ == "__main__":
    while True:
        text, lang = SpeechRecognition()
        if text:
            print(f"[{lang}] {text}")
