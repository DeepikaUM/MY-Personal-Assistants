from ddgs import DDGS
from datetime import datetime
import requests
import re

# -----------------------------
# Intent detection
# -----------------------------
def detect_intent(question: str) -> str:
    q = question.lower()

    if any(w in q for w in ["weather", "temperature", "rain", "forecast"]):
        return "weather"

    return "general"


# -----------------------------
# Extract city name safely
# -----------------------------
def extract_city(question: str) -> str | None:
    match = re.search(r"in\s+([a-zA-Z\s]+)$", question.lower())
    if match:
        return match.group(1).strip()
    return None


# -----------------------------
# Get weather using Open-Meteo
# -----------------------------
def get_weather(city: str):
    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search"
        f"?name={city}&count=1"
    )
    geo = requests.get(geo_url, timeout=10).json()

    if "results" not in geo or not geo["results"]:
        return "Location not found."

    loc = geo["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]

    weather_url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,wind_speed_10m"
    )

    data = requests.get(weather_url, timeout=10).json()
    current = data["current"]

    temp = current["temperature_2m"]
    wind = current["wind_speed_10m"]

    now = datetime.now().strftime("%I:%M %p")

    return (
        f"As of {now}, the current weather in {city.title()} is {temp}°C "
        f"with a wind speed of {wind} km/h."
    )


# -----------------------------
# Score relevance
# -----------------------------
def score_result(result, question):
    q_words = set(question.lower().split())
    text = (result.get("title", "") + " " + result.get("body", "")).lower()
    return sum(1 for w in q_words if w in text)


# -----------------------------
# Limit answer to 2–3 paragraphs
# -----------------------------
def limit_paragraphs(text: str, max_paragraphs=3) -> str:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return "\n\n".join(paragraphs[:max_paragraphs])


# -----------------------------
# Main answer logic
# -----------------------------
def web_answer(question: str):
    intent = detect_intent(question)

    # ---- WEATHER
    if intent == "weather":
        city = extract_city(question)
        if not city:
            return "Please specify a city."
        return get_weather(city)

    # ---- GENERAL SEARCH
    with DDGS() as ddgs:
        results = list(ddgs.text(question, max_results=10))

    if not results:
        return "No answer found."

    ranked = sorted(
        results,
        key=lambda r: score_result(r, question),
        reverse=True
    )

    best = ranked[0]
    body = best.get("body", "").strip()

    if not body:
        body = best.get("title", "").strip()

    return limit_paragraphs(body)


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    question = input().strip()
    print(web_answer(question))
