import pygame
import random
import os
import subprocess
from threading import Event

# -------------------------------------------------
# STOP FLAG (same API)
# -------------------------------------------------
stop_tts_event = Event()

# -------------------------------------------------
# PATHS (ABSOLUTE = IMPORTANT)
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIPER_EXE = os.path.join(BASE_DIR, "piper", "piper.exe")
VOICE_MODEL = os.path.join(
    BASE_DIR,
    "piper",
    "voices",
    "en_US-lessac-medium.onnx"
)

AUDIO_PATH = os.path.join(BASE_DIR, "Data", "speech.wav")

# -------------------------------------------------
# TEXT → AUDIO FILE (Piper)
# -------------------------------------------------
def TextToAudioFile(text: str) -> None:
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)

    process = subprocess.Popen(
        [
            PIPER_EXE,
            "--model", VOICE_MODEL,
            "--output_file", AUDIO_PATH
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True
    )

    process.stdin.write(text)
    process.stdin.close()
    process.wait()

# -------------------------------------------------
# CORE TTS FUNCTION (UNCHANGED NAME)
# -------------------------------------------------
def TTS(Text, func=lambda r=None: True):
    while True:
        try:
            TextToAudioFile(Text)

            pygame.mixer.init()
            pygame.mixer.music.load(AUDIO_PATH)
            pygame.mixer.music.play()

            stop_tts_event.clear()
            while pygame.mixer.music.get_busy():
                if func() is False or stop_tts_event.is_set():
                    break
                pygame.time.Clock().tick(10)

            return True

        except Exception as e:
            print(f"Error in TTS: {e}")

        finally:
            try:
                func(False)
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except Exception:
                pass

# -------------------------------------------------
# LONG TEXT HANDLER (UNCHANGED)
# -------------------------------------------------
def TextToSpeech(Text, func=lambda r=None: True):
    Data = str(Text).split(".")

    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "The rest of the text is now on the chat screen, sir, please check it.",
        "You can see the rest of the text on the chat screen, sir.",
        "The remaining part of the text is now on the chat screen, sir.",
        "Sir, you'll find more text on the chat screen for you to see.",
        "The rest of the answer is now on the chat screen, sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "The next part of the text is on the chat screen, sir.",
        "Sir, please check the chat screen for more information."
    ]

    if len(Data) > 4 and len(Text) >= 300:
        short_text = ".".join(Text.split(".")[0:2]) + ". " + random.choice(responses)
        TTS(short_text, func)
    else:
        TTS(Text, func)

# -------------------------------------------------
# STOP SPEAKING (UNCHANGED)
# -------------------------------------------------
def StopSpeaking():
    stop_tts_event.set()
    pygame.mixer.music.stop()

# -------------------------------------------------
# STANDALONE TEST
# -------------------------------------------------
if __name__ == "__main__":
    while True:
        TextToSpeech(input("Enter the text: "))
