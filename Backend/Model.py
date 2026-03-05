# Backend/Model.py

import cohere
from rich import print
from dotenv import dotenv_values

# ===============================
# LOAD ENV
# ===============================
env_vars = dotenv_values(".env")
cohereAPIKEY = env_vars.get("CohereAPIKEY")

assert cohereAPIKEY, "CohereAPIKEY missing in .env"

co = cohere.Client(api_key=cohereAPIKEY)

# ===============================
# SUPPORTED FUNCTION TAGS
# ===============================
funcs = [
    "exit",
    "general",
    "realtime",
    "open",
    "close",
    "play",
    "generate image",
    "system",
    "content",
    "youtube search",
    "reminder",
    "google search"
]

# ===============================
# REALTIME KEYWORDS (CRITICAL)
# ===============================
REALTIME_KEYWORDS = [
    "current",
    "today",
    "now",
    "right now",
    "latest",
    "weather",
    "temperature",
    "stock",
    "price",
    "news",
    "score",
    "won",
    "yesterday",
    "today’s",
    "today's",
    "match",
    "election"
]

def is_realtime_query(query: str) -> bool:
    q = query.lower()
    return any(keyword in q for keyword in REALTIME_KEYWORDS)

# ===============================
# PREAMBLE (STRICT)
# ===============================
preamble = """
You are a Decision Making Model.

Your job is ONLY to classify and convert user input into executable commands.

RULES:
- Do NOT answer questions.
- Do NOT explain anything.
- ONLY return commands.

GENERAL RULES:
- general <query>
- realtime <query>
- open <app>
- close <app>
- play <song>
- content <topic>
- google search <topic>
- youtube search <topic>
- generate image <prompt>
- reminder <datetime and text>
- exit

SYSTEM RULES (VERY IMPORTANT):
For system actions, ONLY use ONE of these EXACT commands:
- system volume up
- system volume down
- system mute
- system unmute

❌ NEVER use words like:
increase, decrease, raise, lower, boost, reduce

If user intent matches volume control, map it to the exact system command above.

If unsure, respond with:
general <query>
"""

# ===============================
# CHAT HISTORY (FEW-SHOT)
# ===============================
ChatHistory = [
    {"role": "User", "message": "increase system volume"},
    {"role": "Chatbot", "message": "system volume up"},
    {"role": "User", "message": "mute the sound"},
    {"role": "Chatbot", "message": "system mute"},
    {"role": "User", "message": "who is apj abdul kalam"},
    {"role": "Chatbot", "message": "general who is apj abdul kalam"},
]

# ===============================
# SYSTEM NORMALIZATION MAP
# ===============================
SYSTEM_NORMALIZE = {
    "system increase volume": "system volume up",
    "system increase system volume": "system volume up",
    "system raise volume": "system volume up",
    "system volume increase": "system volume up",

    "system decrease volume": "system volume down",
    "system lower volume": "system volume down",
    "system reduce volume": "system volume down",

    "system mute volume": "system mute",
    "system unmute volume": "system unmute",
}

# ===============================
# MAIN DECISION FUNCTION
# ===============================
def FirstLayerDMM(prompt: str, depth: int = 0):
    if depth > 3:
        return [f"general {prompt}"]

    try:
        stream = co.chat_stream(
            model="command-r-08-2024",
            message=prompt,
            temperature=0.3,
            chat_history=ChatHistory,
            prompt_truncation="OFF",
            preamble=preamble
        )
    except Exception as e:
        print(f"[red]Cohere Error:[/red] {e}")
        return [f"general {prompt}"]

    response_text = ""
    for event in stream:
        if event.event_type == "text-generation":
            response_text += event.text

    response_text = response_text.replace("\n", "").strip()

    # split multiple commands
    tasks = [t.strip() for t in response_text.split(",") if t.strip()]

    filtered_tasks = []

    for task in tasks:
        t = task.lower().strip()

        # normalize system commands
        if t.startswith("system"):
            t = SYSTEM_NORMALIZE.get(t, t)

        for func in funcs:
            if t.startswith(func):
                filtered_tasks.append(t)
                break

    # ===============================
    # FORCE REALTIME (RULE-BASED)
    # ===============================
    if is_realtime_query(prompt):
        return [f"realtime {prompt}"]

    if not filtered_tasks:
        return [f"general {prompt}"]

    return filtered_tasks

# ===============================
# CLI TEST
# ===============================
if __name__ == "__main__":
    print("[green]Model test started[/green]")
    while True:
        q = input(">>> ")
        print(FirstLayerDMM(q))
