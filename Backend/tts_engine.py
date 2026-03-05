import os
import sys
import numpy as np
import sounddevice as sd
import soundfile as sf
from TTS.api import TTS

# -------------------------------------------------
# ABSOLUTE PATHS (CRITICAL)
# -------------------------------------------------
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))     # Backend/
PROJECT_ROOT = os.path.dirname(ENGINE_DIR)                  # E:\Red Ai
DATA_DIR = os.path.join(PROJECT_ROOT, "Data")
AUDIO_PATH = os.path.join(DATA_DIR, "speech.wav")

os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# LOAD MODEL ONCE
# -------------------------------------------------
tts = TTS(
    model_name="tts_models/en/vctk/vits",
    progress_bar=False,
    gpu=False
)

# -------------------------------------------------
def speak(text: str):
    audio = tts.tts(text=text, speaker="p230")

    # normalize + energy boost
    audio = audio / np.max(np.abs(audio))
    audio = np.clip(audio * 1.25, -1.0, 1.0)

    sf.write(AUDIO_PATH, audio, 22050)

    data, sr = sf.read(AUDIO_PATH, dtype="float32")
    sd.play(data, sr)
    sd.wait()

# -------------------------------------------------
if __name__ == "__main__":
    # called from subprocess
    if len(sys.argv) > 1:
        speak(" ".join(sys.argv[1:]))
        sys.exit(0)

    # manual test mode
    while True:
        try:
            text = input("Enter the text: ").strip()
            if text:
                speak(text)
        except KeyboardInterrupt:
            break
