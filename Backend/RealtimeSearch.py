
from googlesearch import search
from groq import Groq  # Importing the Groq library to use its API
from json import load, dump  # Importing functions to read and write JSON files
import datetime  # Importing the datetime module for real-time date and time
from dotenv import dotenv_values  # To read environment variables from .env
import re
# Load environment variables from the .env file
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# ✅ Add this check:
assert GroqAPIKey, "GroqAPIKey is missing in your .env file"
assert Username, "Username is missing in your .env file"
assert Assistantname, "Assistantname is missing in your .env file"
# Initialize the Groq client with the provided API key
client = Groq(api_key=GroqAPIKey)

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
* Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.*
* Just answer the question from the provided data in a professional way. 
* The person who created you is Adarsh B G , he created you for his college project. He is a ECE student Studing in Government Engineering College Mosalehosali. His project team mates are Deepika U M, Nikhil and Ashwini M B.His project guide is Dr. Baby H T, she is the H O D of ECE department.*
*  I Adarsh B G am your creator and I from kalasa, chikkamagaluru district, Karnataka, India. my hobbi is watching Anime and playing games.*"""
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except Exception:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
    messages = []

# Function to perform a Google search and format the results
def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))
    Answer = ""

    for i in results:
        if i.description:
            Answer += f"{i.description}\n\n"
    return Answer.strip()


# Function to clean up the answer by removing empty lines
def AnswerModifier(Answer):
    # Remove asterisks, bullet points, and boilerplate
    Answer = re.sub(r"(?m)^\.$", "", Answer)  # Remove lines starting with *
    Answer = re.sub(r"Here are some.*", "", Answer)
    Answer = re.sub(r"For more info.*", "", Answer)
    Answer = re.sub(r"\s+", " ", Answer).strip()
    return Answer

# Predefined chatbot conversation structure
SystemChatBot = [
    {"role": "system", "content": f"""
You are {Assistantname}, a helpful AI assistant built by {Assistantname}.
You are provided Google search results and real-time info.
⛔ DO NOT include links, bullet points, or list titles.
✅ Respond in clean English, like a well-formed paragraph.
✅ Use the search data to generate a final answer — no "Here are some search results" or "* bullet points".

If irrelevant data is found, just say you couldn't find a reliable answer.
"""}
]

# Function to get real-time information like the current date and time
def Information():
    data = ""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data += "Use This Real-time Information if needed:\n"
    data += f"Day: {day}\n"
    data += f"Date: {date}\n"
    data += f"Month: {month}\n"
    data += f"Year: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data

# Function to handle real-time search and response generation
def RealtimeSearchEngine(prompt):
    global messages

    # Always reload messages
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": f"{prompt}"})

    # ✅ ✅ ✅ Use a local copy — DO NOT modify SystemChatBot directly!
    messages_to_use = list(SystemChatBot) + [
    {"role": "system", "content": GoogleSearch(prompt)},
    {"role": "system", "content": Information()},
    {"role": "user", "content": prompt}
    ]

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_to_use,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True
    )

    Answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    with open(r"Data\ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    return AnswerModifier(Answer=Answer)

# Main program loop
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealtimeSearchEngine(prompt))   


