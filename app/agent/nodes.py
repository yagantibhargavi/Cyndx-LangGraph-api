import os
import re
from typing import Optional

import requests
from dotenv import load_dotenv
from groq import Groq

from .state import AgentState

load_dotenv()

# ---------- Groq client ----------
def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Put it in .env")
    return Groq(api_key=api_key)


GROQ_CLIENT = _get_groq_client()

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))


# ---------- Helper: normalize messages ----------
def _messages_from_state(state: AgentState):
    # expects state["messages"] = [{"role":"user","content":"..."}, ...]
    msgs = state.get("messages", [])
    if not isinstance(msgs, list):
        msgs = []
    return msgs


def _last_user_text(state: AgentState) -> str:
    for m in reversed(_messages_from_state(state)):
        if m.get("role") == "user" and m.get("content"):
            return str(m["content"])
    # fallback: last message content
    msgs = _messages_from_state(state)
    return str(msgs[-1]["content"]) if msgs else ""


# ---------- TOOL: Weather via Open-Meteo (free, no key) ----------
def _extract_city(text: str) -> Optional [str]:
    # “weather in Boston”, “What is the weather in Boston today?”
    m = re.search(r"weather\s+(in|at)\s+([A-Za-z .'-]+)", text, re.IGNORECASE)
    if m:
        return m.group(2).strip()
    # “in Boston?” fallback
    m2 = re.search(r"\bin\s+([A-Za-z .'-]+)\??$", text.strip(), re.IGNORECASE)
    if m2:
        return m2.group(1).strip()
    return None


def _get_weather_summary(city: str) -> str:
    # 1) geocode city -> lat/lon
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=15,
    )
    geo.raise_for_status()
    gj = geo.json()
    if not gj.get("results"):
        return f"I couldn't find coordinates for '{city}'. Try a bigger city name (e.g., 'Boston, MA')."

    r0 = gj["results"][0]
    lat, lon = r0["latitude"], r0["longitude"]
    resolved_name = f"{r0.get('name')}, {r0.get('admin1','')}, {r0.get('country','')}".replace(" ,", ",").strip(", ")

    # 2) forecast
    wx = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m",
            "timezone": "auto",
        },
        timeout=15,
    )
    wx.raise_for_status()
    wj = wx.json()
    cur = wj.get("current", {})
    t = cur.get("temperature_2m")
    feels = cur.get("apparent_temperature")
    precip = cur.get("precipitation")
    wind = cur.get("wind_speed_10m")

    return (
        f"Weather for {resolved_name} right now:\n"
        f"- Temperature: {t}°C (feels like {feels}°C)\n"
        f"- Precipitation: {precip} mm\n"
        f"- Wind: {wind} km/h"
    )


# ---------- Planner Node ----------
async def planner_node(state: AgentState) -> AgentState:
    user_input = _last_user_text(state)

    system = (
        "You are a routing assistant.\n"
        "Decide if the user needs an external tool (up-to-date / factual lookup like weather, news, prices, real-time info).\n"
        "If yes, output ONLY: TOOL\n"
        "If no, output ONLY: RESPONDER\n"
    )

    try:
        resp = GROQ_CLIENT.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_input},
            ],
            temperature=0,
        )
        decision = (resp.choices[0].message.content or "").strip().upper()
    except Exception:
        decision = ""

    # Hard guard + fallback heuristic
    if decision not in {"TOOL", "RESPONDER"}:
        keywords = ["weather", "temperature", "forecast", "latest", "news", "price", "today", "now"]
        decision = "TOOL" if any(k in user_input.lower() for k in keywords) else "RESPONDER"

    state["next_node"] = "tool" if decision == "TOOL" else "responder"
    return state


# ---------- Tool Node ----------
def tool_node(state: AgentState) -> AgentState:
    user_text = _last_user_text(state)
    city = _extract_city(user_text)

    msgs = state.get("messages", [])

    # WEATHER TOOL
    if city:
        weather = _get_weather_summary(city)
        msgs.append({"role": "assistant", "content": weather})
        state["messages"] = msgs
        state["response"] = weather
        return state

    # 🔥 FALLBACK TOOL RESPONSE (MANDATORY)
    fallback = "Tool not available for this request yet."

    msgs.append({"role": "assistant", "content": fallback})
    state["messages"] = msgs
    state["response"] = fallback

    return state

# ---------- Responder Node ----------
def responder_node(state: AgentState) -> AgentState:
    user_text = _last_user_text(state)

    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_text},
        ],
        temperature=DEFAULT_TEMPERATURE,
    )

    reply_text = (resp.choices[0].message.content or "").strip()

    # save assistant message
    msgs = state.get("messages", [])
    msgs.append({"role": "assistant", "content": reply_text})
    state["messages"] = msgs

    # 🔥 THIS LINE IS THE MOST IMPORTANT
    state["response"] = reply_text

    return state
