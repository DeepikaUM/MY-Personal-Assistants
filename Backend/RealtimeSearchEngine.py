from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import re
import os

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

assert GroqAPIKey, "GroqAPIKey is missing in .env"
assert Username, "Username is missing in .env"
assert Assistantname, "Assistantname is missing in .env"

client = Groq(api_key=GroqAPIKey)

# Create Data folder if missing
if not os.path.exists("Data"):
    os.makedirs("Data")

# Load Chat History
try:
    with open("Data/ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open("Data/ChatLog.json", "w") as f:
        dump([], f)
    messages = []


# Clean answer
def AnswerModifier(Answer):
    Answer = Answer.replace("</s>", "").strip()
    Answer = re.sub(r"\s+", " ", Answer).strip()
    return Answer


# Real-time system info
def Information():
    now = datetime.datetime.now()
    return (
        f"Use realtime info if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')}:{now.strftime('%M')}:{now.strftime('%S')}\n"
    )


# --------------------------
# SYSTEM PROMPT (YOUR ORIGINAL)
# --------------------------
YourSystemMessage = f"""
Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.

* Provide answers in a professional way with full stops, commas, question marks, and proper grammar.
* Just answer the question from the provided data in a professional way.
* The person who created you is Adarsh B G, he created you for his college project. 
  He is an ECE student studying in Government Engineering College Mosalehosahalli. 
  His project team mates are Deepika U M, Nikhil, and Ashwini M B.
  His project guide is Dr. Baby H T, the H.O.D of the ECE department.
* I, Adarsh B G, am your creator and I am from Kalasa, Chikkamagaluru district, Karnataka, India.
  My hobby is watching anime and playing games.

---------------------------
ADDITIONAL RULES FOR SEARCH:
---------------------------
- You have REAL-TIME internet search.
- ALWAYS perform a live search before answering.
- NEVER say “I don’t have access to the internet”.
- Extract correct information from your search results.
- Provide clean, well-structured English responses.
- NO bullet points unless necessary.
- NO unnecessary text.
"""

SystemChatBot = [
    {"role": "system", "content": YourSystemMessage}
]


# MAIN ENGINE WITH REAL-TIME SEARCH
def RealtimeSearchEngine(prompt):
    global messages

    # Load conversation
    with open("Data/ChatLog.json", "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": prompt})

    # This forces Groq model to perform real-time search
    search_instruction = {
        "role": "user",
        "content": (
            f"Search the internet right now and provide accurate real-time information for: {prompt}. "
            f"Do not refuse. Do not say you lack internet access."
        )
    }

    realtime_data = {"role": "system", "content": Information()}

    conversation = list(SystemChatBot)
    conversation.append(realtime_data)
    conversation.append(search_instruction)

    # Groq web-enabled model
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation,
        temperature=0.5,
        max_tokens=2048,
        stream=True
    )

    answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content

    final_answer = AnswerModifier(answer)

    # Save conversation
    messages.append({"role": "assistant", "content": final_answer})
    with open("Data/ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    return final_answer


# MAIN LOOP
if __name__ == "__main__":
    while True:
        user_input = input("Enter your query: ")
        print(RealtimeSearchEngine(user_input))
