# Backend/Automation.py

import socket
import os
import subprocess
import asyncio
import requests
import webbrowser
import keyboard
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import re

# ===============================
# LOAD ENV
# ===============================
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

assert GroqAPIKey, "GroqAPIKey missing in .env"

client = Groq(api_key=GroqAPIKey)

# ===============================
# SYSTEM PROMPT (CONTENT ONLY)
# ===============================
SystemChatBot = [{
    "role": "system",
    "content": (
        "You are a professional content writer. "
        "Write letters, reports, blogs, and articles clearly."
    )
}]
messages = []

# ===============================
# KNOWN WEB APPS
# ===============================
web_apps = {
    "facebook": "https://www.facebook.com",
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com"
}

# ===============================
# SAFE FILENAME
# ===============================
def safe_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip()
    return name or "untitled"

# ===============================
# INTERNET CHECK
# ===============================
def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

# ===============================
# GOOGLE SEARCH
# ===============================
def GoogleSearch(topic: str):
    if not is_connected():
        print("[red]No internet connection[/red]")
        return False

    from pywhatkit import search
    search(topic)
    return True

# ===============================
# CONTENT GENERATION
# ===============================
def Content(topic: str):
    def open_notepad(file_path):
        subprocess.Popen(["notepad.exe", file_path])

    def writer(prompt: str):
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            stream=True
        )

        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content

        messages.append({"role": "assistant", "content": answer})
        return answer

    topic = topic.strip()
    text = writer(topic)

    filename = safe_filename(topic).lower().replace(" ", "_")
    path = os.path.join("Data", f"{filename}.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    open_notepad(path)
    return True

# ===============================
# YOUTUBE SEARCH / PLAY
# ===============================
def YouTubeSearch(topic: str):
    webbrowser.open(
        f"https://www.youtube.com/results?search_query={topic}"
    )
    return True

def PlayYoutube(query: str):
    if not is_connected():
        print("[red]No internet connection[/red]")
        return False

    from pywhatkit import playonyt
    playonyt(query)
    return True

# ===============================
# OPEN APPLICATION / WEBSITE
# ===============================
def OpenApp(app: str, sess=requests.session()):
    app = app.lower().strip()

    if app in web_apps:
        webbrowser.open(web_apps[app])
        return True

    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        r = sess.get(
            f"https://www.google.com/search?q={app}",
            headers=headers
        )

        soup = BeautifulSoup(r.text, "html.parser")
        link = soup.find("a")
        if link and link.get("href"):
            webopen(link["href"])
            return True

    print(f"[red]Unable to open {app}[/red]")
    return False

# ===============================
# CLOSE APPLICATION
# ===============================
def CloseApp(app: str):
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False

# ===============================
# SYSTEM CONTROL (STRICT)
# ===============================
def System(command: str):
    command = command.lower().strip()

    if command == "mute":
        keyboard.press_and_release("volume mute")

    elif command == "unmute":
        keyboard.press_and_release("volume mute")

    elif command == "volume up":
        keyboard.press_and_release("volume up")

    elif command == "volume down":
        keyboard.press_and_release("volume down")

    else:
        print(f"[red]Unknown system command:[/red] {command}")

    return True

# ===============================
# TRANSLATE & EXECUTE
# ===============================
async def TranslateAndExecute(commands: list[str]):
    tasks = []

    for cmd in commands:
        cmd = cmd.strip().lower()

        if cmd.startswith("open "):
            tasks.append(
                asyncio.to_thread(OpenApp, cmd.replace("open ", ""))
            )

        elif cmd.startswith("close "):
            tasks.append(
                asyncio.to_thread(CloseApp, cmd.replace("close ", ""))
            )

        elif cmd.startswith("play "):
            tasks.append(
                asyncio.to_thread(PlayYoutube, cmd.replace("play ", ""))
            )

        elif cmd.startswith("content "):
            tasks.append(
                asyncio.to_thread(Content, cmd.replace("content ", ""))
            )

        elif cmd.startswith("google search "):
            tasks.append(
                asyncio.to_thread(
                    GoogleSearch,
                    cmd.replace("google search ", "")
                )
            )

        elif cmd.startswith("youtube search "):
            tasks.append(
                asyncio.to_thread(
                    YouTubeSearch,
                    cmd.replace("youtube search ", "")
                )
            )

        elif cmd.startswith("system "):
            # ⚠ system commands MUST NOT be async
            System(cmd.replace("system ", ""))

        else:
            print(f"[yellow]No handler for:[/yellow] {cmd}")

    if tasks:
        await asyncio.gather(*tasks)

# ===============================
# MAIN ENTRY
# ===============================
async def Automation(commands: list[str]):
    await TranslateAndExecute(commands)
    return True

# ===============================
# TEST
# ===============================
if __name__ == "__main__":
    asyncio.run(Automation([
        "content how to make smart gas detection system using esp32",
        "open facebook",
        "system volume up",
        "play python tutorial",
        "system mute"
    ]))
