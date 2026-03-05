from ddgs import DDGS
from datetime import datetime
import requests

# -----------------------------
# Intent detection
# -----------------------------
def detect_intent(question: str) -> str:
    q = question.lower()

    if any(w in q for w in ["weather", "temperature", "rain", "forecast"]):
        return "weather"

    if any(w in q for w in ["program", "tv", "channel", "running", "live"]):
        return "tv"

    return "general"


# -----------------------------
# Get weather using API
# -----------------------------
def get_weather(city: str):
    # Geocoding
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    geo = requests.get(geo_url, timeout=10).json()

    if "results" not in geo:
        return "❌ Location not found."

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    # Weather
    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code,wind_speed_10m"
    )

    data = requests.get(weather_url, timeout=10).json()
    current = data["current"]

    temp = current["temperature_2m"]
    wind = current["wind_speed_10m"]

    now = datetime.now().strftime("%I:%M %p")

    return (
        f"As of {now}, the current weather in {city.title()}:\n\n"
        f"🌡 Temperature: {temp}°C\n"
        f"💨 Wind Speed: {wind} km/h\n"
    )


# -----------------------------
# Improve query
# -----------------------------
def improve_query(question: str, intent: str) -> str:
    if intent == "tv":
        return question + " current program now"
    return question


# -----------------------------
# Score relevance
# -----------------------------
def score_result(result, question):
    q_words = set(question.lower().split())
    text = (result.get("title", "") + " " + result.get("body", "")).lower()
    return sum(1 for w in q_words if w in text)


# -----------------------------
# Main web answer
# -----------------------------
def web_answer(question: str):
    intent = detect_intent(question)

    # ---- WEATHER (API, NOT SEARCH)
    if intent == "weather":
        city = question.lower().replace("weather", "").replace("current", "").replace("in", "").strip()
        return get_weather(city), "https://open-meteo.com/"

    # ---- TV / GENERAL (SEARCH)
    query = improve_query(question, intent)

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=10))

    if not results:
        return "❌ No results found.", None

    ranked = sorted(results, key=lambda r: score_result(r, question), reverse=True)
    best = ranked[0]

    body = best.get("body", "").strip()
    source = best.get("href", "")

    if intent == "tv":
        now = datetime.now().strftime("%I:%M %p")
        body = (
            f"As of around {now}, based on available TV schedules:\n\n"
            f"{body}\n\n"
            "(Note: Live TV programs may change in real time.)"
        )

    return body, source


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    question = input("Enter your question: ").strip()

    answer, source = web_answer(question)

    print("\n🔹 Answer:\n")
    print(answer)

    if source:
        print("\n🔗 Source:")
        print(source)
