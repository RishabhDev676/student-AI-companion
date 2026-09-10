import os
import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "gemini-3.5-flash-lite"

API_KEYS = [
    os.getenv("API_KEY_1"),
    os.getenv("API_KEY_2"),
    os.getenv("API_KEY_3"),
    os.getenv("API_KEY_4"),
    os.getenv(" "),
]

def ai(prompt, system="You are a helpful AI assistant.", max_tokens=1024):
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
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]

            print(f"[AI] Key {i} failed ({r.status_code}), trying next...")

        except Exception as e:
            print(f"[AI] Key {i} error: {e}")

    return "AI temporarily unavailable. All API keys failed."