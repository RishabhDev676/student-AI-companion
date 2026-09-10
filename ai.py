import os
import requests
from dotenv import load_dotenv
import json


import re

def safe_json_parse(json_string, max_size_bytes: int = 10_000_000):
    """Safely parse a JSON string, stripping markdown fences or extracting JSON if present."""
    if isinstance(json_string, (dict, list)):
        return json_string
    if not isinstance(json_string, str):
        return None

    # 1. Protect against resource exhaustion (DoS) by limiting input size
    if len(json_string.encode('utf-8')) > max_size_bytes:
        raise ValueError("JSON payload too large.")
        
    cleaned = json_string.strip()
    if "```" in cleaned:
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

    try:
        # 2. Safely parse the string
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        # Attempt to extract outermost JSON object or array
        bracket_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if bracket_match:
            try:
                return json.loads(bracket_match.group(1).strip())
            except Exception:
                pass
        # 3. Handle malformed JSON safely
        print(f"Invalid JSON format: {e}")
        return None

# Load both .env and .env.local
load_dotenv()
load_dotenv(".env.local")

MODEL = "gemini-3.5-flash-lite"

API_KEYS = [
    os.getenv("API_KEY_1"),
    os.getenv("API_KEY_2"),
    os.getenv("API_KEY_3"),
    os.getenv("API_KEY_4"),
    os.getenv("API_KEY_5"),
    os.getenv("GEMINI_API_KEY"),
]
# Filter out None and empty strings
API_KEYS = [k for k in API_KEYS if k and k.strip()]

def ai(prompt, system="You are a helpful AI assistant.", max_tokens=1024, parse_json=False):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

    for i, key in enumerate(API_KEYS, 1):
        if not key:
            continue

        try:
            r = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": key
                },
                json={
                    "system_instruction": {
                        "parts": [{"text": system}]
                    },
                    "contents": [{
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens
                    }
                },
                timeout=30
            )

            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return safe_json_parse(text) if parse_json else text

            print(f"[AI] Key {i} failed ({r.status_code}), trying next...")

        except Exception as e:
            print(f"[AI] Key {i} error: {e}")

    return "AI temporarily unavailable. All API keys failed."