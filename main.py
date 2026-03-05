from threading import Lock
import sys
import os
import subprocess
import threading
import json
from dotenv import dotenv_values 
from asyncio import run
from time import sleep

from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition, mt
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech


file_lock = Lock()

# Load env
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")

assert Username, "Username missing in .env"
assert Assistantname, "Assistantname missing in .env"

DefaultMessage = f'''{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you?'''

Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]


def ShowDefaultChatIfNoChats():
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as File:
        if len(File.read()) < 5:
            with file_lock:
                with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                    file.write("")
                with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                    file.write(DefaultMessage)


def ReadChatLogJson():
    with open(os.path.join('Data', 'ChatLog.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        role = entry["role"]
        content = entry["content"]
        formatted_chatlog += f"{Username if role == 'user' else Assistantname}: {content}\n"
    with file_lock:
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(AnswerModifier(formatted_chatlog))


def ShowChatsOnGUI():
    with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as File:
        Data = File.read()
        if Data:
            with file_lock:
                with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
                    file.write('\n'.join(Data.split('\n')))


def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()
    greeting = f"{Assistantname}: Hi! I'm {Assistantname}, your personal assistant. How can I help you today?"
    ShowTextToScreen(greeting)
    TextToSpeech(f"Hi! I'm {Assistantname}, your personal AI assistant. How can I help you today?")


def MainExecution():
    global last_image_prompt, image_generation_in_progress
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening …")
    Query, original_lang = SpeechRecognition()
    if not Query.strip():
        SetAssistantStatus("Available …")
        return

    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Thinking …")
    Decision = FirstLayerDMM(Query)

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)
    Mearged_query = " and ".join(
        [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for queries in Decision:
        if "generate" in queries:
            ImageGenerationQuery = queries.replace("generate", "").replace("image", "").strip()
            ImageExecution = True

    for queries in Decision:
        if not TaskExecution and any(queries.startswith(func) for func in Functions):
            run(Automation(list(Decision)))
            TaskExecution = True

    if ImageExecution:
       
       
       try:
          status_path = r"Frontend\Files\ImageGeneration.data"
          with open(status_path, "w", encoding="utf-8") as file:
            file.write(f"{ImageGenerationQuery}, True")
       except Exception as e:
           print(f"❌ Error updating image status: {e}")



    if (G and R) or R:
        SetAssistantStatus("Searching …")
        Answer = RealtimeSearchEngine(QueryModifier(Mearged_query))
        translated_answer = mt.translate(Answer, original_lang, "en")
        ShowTextToScreen(f"{Assistantname}: {translated_answer}")
        SetAssistantStatus("Answering …")
        TextToSpeech(translated_answer)
        return

    for Queries in Decision:
        if "general" in Queries:
            SetAssistantStatus("Thinking …")
            QueryFinal = Queries.replace("general ", "")
            Answer = ChatBot(QueryModifier(QueryFinal))
            translated_answer = mt.translate(Answer, original_lang, "en")
            ShowTextToScreen(f"{Assistantname}: {translated_answer}")
            SetAssistantStatus("Answering …")
            TextToSpeech(translated_answer)
            return

        elif "realtime" in Queries:
            SetAssistantStatus("Searching …")
            QueryFinal = Queries.replace("realtime ", "")
            Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))
            translated_answer = mt.translate(Answer, original_lang, "en")
            ShowTextToScreen(f"{Assistantname}: {translated_answer}")
            SetAssistantStatus("Answering …")
            TextToSpeech(translated_answer)
            return

        elif "exit" in Queries:
            QueryFinal = "Okay, Bye!"
            Answer = ChatBot(QueryModifier(QueryFinal))
            translated_answer = mt.translate(Answer, original_lang, "en")
            ShowTextToScreen(f"{Assistantname}: {translated_answer}")
            SetAssistantStatus("Answering …")
            TextToSpeech(translated_answer)
            os._exit(0)


def FirstThread():
    while True:
        if GetMicrophoneStatus().strip().lower() == "true":
            MainExecution()
            sleep(1)  # ← NEW: prevents 20 requests/min crash
        else:
            if "Available …" not in GetAssistantStatus():
                SetAssistantStatus("Available …")
            sleep(0.2)


def ImageWatcherThread():
    subprocess.Popen(
        [sys.executable, os.path.join("Backend", "ImageGeneration.py")],
        creationflags=subprocess.CREATE_NO_WINDOW
    )


def start_backend():
    InitialExecution()
    FirstThread()


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.environ["IS_FROZEN"] = "true"

    if os.environ.get("APP_ALREADY_RUNNING") == "true":
        print("⛔ Preventing duplicate instance.")
        sys.exit(0)

    os.environ["APP_ALREADY_RUNNING"] = "true"

    gui_thread = threading.Thread(target=GraphicalUserInterface, daemon=True)
    gui_thread.start()

    sleep(2)
    threading.Thread(target=ImageWatcherThread, daemon=True).start()

    try:
        start_backend()
    except KeyboardInterrupt:
        print("🛑 Exiting cleanly...")
        sys.exit(0)
