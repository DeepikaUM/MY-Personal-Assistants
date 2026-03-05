import asyncio
import os
import re
import requests
from time import sleep
from PIL import Image
from dotenv import get_key

# ============================================================
# CONFIG
# ============================================================
DATA_DIR = "Data"
TRIGGER_FILE = r"Frontend\Files\ImageGeneration.data"
LOCK_FILE = r"Frontend\Files\ImageGeneration.lock"

API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

headers = {
    "Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}",
    "Accept": "image/png"
}

os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# SAFE FILENAME
# ============================================================
def safe_filename(text: str) -> str:
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    return text.strip().replace(" ", "_") or "image"

# ============================================================
# OPEN IMAGE
# ============================================================
def open_image(path):
    try:
        Image.open(path).show()
        print(f"📷 Opened image: {path}")
    except Exception as e:
        print(f"❌ Open error: {e}")

# ============================================================
# HF API
# ============================================================
async def generate_image(prompt: str):
    payload = {"inputs": f"{prompt}, ultra detailed, 4K, high quality"}

    response = await asyncio.to_thread(
        requests.post, API_URL, headers=headers, json=payload, timeout=120
    )

    if response.status_code != 200:
        print("❌ HF Error:", response.text)
        return None

    file_path = os.path.join(DATA_DIR, safe_filename(prompt) + ".png")

    with open(file_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Saved image: {file_path}")
    return file_path

# ============================================================
# MAIN WATCHER (HARD LOCKED)
# ============================================================
if __name__ == "__main__":
    print("🔁 Image watcher started (LOCK ENABLED)")

    while True:
        try:
            # 🔒 If another instance is generating → WAIT
            if os.path.exists(LOCK_FILE):
                sleep(0.5)
                continue

            if not os.path.exists(TRIGGER_FILE):
                sleep(0.5)
                continue

            with open(TRIGGER_FILE, "r", encoding="utf-8") as f:
                data = f.read().strip()

            if not data:
                sleep(0.5)
                continue

            parts = [p.strip() for p in data.split(",")]
            if len(parts) != 2:
                sleep(0.5)
                continue

            prompt, status = parts

            if status.lower() == "true" and prompt:
                # 🔒 CREATE LOCK (CRITICAL)
                open(LOCK_FILE, "w").close()

                print(f"🖼 Generating image for: {prompt}")

                image_path = asyncio.run(generate_image(prompt))
                if image_path:
                    open_image(image_path)

                # ✅ RESET TRIGGER
                with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
                    f.write("False, False")

                # 🔓 REMOVE LOCK
                os.remove(LOCK_FILE)

            sleep(0.5)

        except Exception as e:
            print(f"❌ Watcher error: {e}")
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
            sleep(1)
