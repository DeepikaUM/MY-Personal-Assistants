from groq import Groq  # Importing the Groq library to use its API.
from json import load, dump
import datetime  # For real-time information
from dotenv import dotenv_values

# -------------------- Load Environment Variables --------------------
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")
GroqModel = env_vars.get("GROQ_MODEL", "llama-3.3-70b-versatile")  # ✅ Default to supported model

# ✅ Validate required environment variables
assert GroqAPIKey, "GroqAPIKey is missing in your .env file"
assert Username, "Username is missing in your .env file"
assert Assistantname, "Assistantname is missing in your .env file"

# -------------------- Initialize Groq Client --------------------
client = Groq(api_key=GroqAPIKey)

# -------------------- System Instructions --------------------
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
* Do not tell time until I ask, do not talk too much, just answer the question. *
* The person who created you is Adarsh B G, he created you for his college project. He is an ECE student studying in Government Engineering College Mosalehosahalli. His project teammates are Deepika U M, Nikhil and Ashwini M B. His project guide is Dr. Baby H T, she is the HOD of ECE department. *
* Reply in the same input language, even if the question is in Hindi or Kannada, reply in English. *
* I, Adarsh B G, am your creator and I am from Kalasa, Chikkamagaluru district, Karnataka, India. My hobby is watching Anime and playing games. *
* Do not provide notes in the output, just answer the question and never mention your training data. *
"""

SystemChatBot = [
    {"role": "system", "content": System}
]

# -------------------- Load / Create ChatLog --------------------
try:
    with open(r"Data\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open(r"Data\ChatLog.json", "w") as f:
        dump([], f)
    messages = []

# -------------------- Helper Functions --------------------
def RealtimeInformation():
    """Return current real-time date and time information as a string."""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed,\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours : {minute} minutes : {second} seconds.\n"

    return data


def AnswerModifier(Answer):
    """Remove unnecessary empty lines from the chatbot's response."""
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

# -------------------- Main ChatBot Function --------------------
def ChatBot(Query, retries=3):
    """Send the user's query to Groq and return the AI's response."""
    try:
        # Load existing messages
        with open(r"Data\ChatLog.json", "r") as f:
            messages = load(f)

        # Add user message
        messages.append({"role": "user", "content": Query})

        # Create completion request
        completion = client.chat.completions.create(
            model=GroqModel,  # ✅ Uses env model or fallback
            messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True
        )

        # Collect the streamed response
        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        # Save updated chat history
        with open(r"Data\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"Error: {e}")
        # Clear chat history if something goes wrong
        with open(r"Data\ChatLog.json", "w") as f:
            dump([], f, indent=4)

        if retries > 0:
            return ChatBot(Query, retries - 1)
        else:
            return "Sorry, I failed to answer your question."

# -------------------- Run Chatbot --------------------
if __name__ == "__main__":
    while True:
        user_input = input("Enter your Question: ")
        print(ChatBot(user_input))