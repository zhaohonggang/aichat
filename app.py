import os
import time
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

GOOGLE_API_KEY = "AIzaSyAaq5l8Jjt-LluMow96oe5jwovplix37uU"
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

MODELS = [
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "description": "Fast & capable, supports 1M tokens",
        "rpm": 10,
        "rpd": 250,
    },
    {
        "id": "gemini-flash-latest",
        "name": "Gemini Flash Latest",
        "description": "Latest release of Gemini Flash",
        "rpm": 10,
        "rpd": 250,
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "description": "Gemini 2.0 Flash model",
        "rpm": 10,
        "rpd": 250,
    },
    {
        "id": "gemini-2.0-flash-lite",
        "name": "Gemini 2.0 Flash-Lite",
        "description": "Lightweight & fast",
        "rpm": 15,
        "rpd": 1000,
    },
    {
        "id": "gemini-pro-latest",
        "name": "Gemini Pro Latest",
        "description": "Latest Gemini Pro model",
        "rpm": 5,
        "rpd": 100,
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "description": "Most capable Gemini model",
        "rpm": 5,
        "rpd": 100,
    },
    {
        "id": "gemma-3-1b-it",
        "name": "Gemma 3 1B",
        "description": "Google's lightweight Gemma model",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "gemma-3-4b-it",
        "name": "Gemma 3 4B",
        "description": "Google's compact Gemma model",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "gemma-3-12b-it",
        "name": "Gemma 3 12B",
        "description": "Google's medium Gemma model",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "gemma-3-27b-it",
        "name": "Gemma 3 27B",
        "description": "Google's large Gemma model",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "grant-0.1",
        "name": "Grant 0.1",
        "description": "Virtual AI assistant",
        "rpm": 999999,
        "rpd": 999999,
    },
]


def call_gemini(
    model_id: str, message: str, history: list = None, max_retries: int = 3
):
    url = f"{GOOGLE_BASE_URL}/{model_id}:generateContent"
    params = {"key": GOOGLE_API_KEY}

    contents = []
    for msg in history or []:
        contents.append(
            {
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}],
            }
        )
    contents.append({"role": "user", "parts": [{"text": message}]})

    data = {"contents": contents}

    for attempt in range(max_retries):
        try:
            response = requests.post(url, params=params, json=data, timeout=60)

            if response.status_code == 429:
                wait_time = (attempt + 1) * 2
                print(f"Rate limited, retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Error: {e}, retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise

    raise Exception("Max retries exceeded")


@app.route("/")
def index():
    return render_template(
        "index.html", models=MODELS, api_key_configured=bool(GOOGLE_API_KEY)
    )


@app.route("/api/models")
def get_models():
    return jsonify({"models": MODELS, "api_key_configured": bool(GOOGLE_API_KEY)})


@app.route("/api/chat", methods=["POST"])
def chat():
    if not GOOGLE_API_KEY:
        return jsonify({"error": "API key not configured"}), 400

    data = request.json
    model_id = data.get("model", "gemini-2.5-flash")
    message = data.get("message")
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Missing message"}), 400

    try:
        response = call_gemini(model_id, message, history)
        return jsonify({"response": response, "model": model_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("Google Gemini Chat - Web Interface")
    print("=" * 50)
    print(f"\nAvailable Models ({len(MODELS)}):")
    for model in MODELS:
        print(f"  - {model['name']}")
    print(f"\nAPI Key Configured: {bool(GOOGLE_API_KEY)}")
    print("\nStarting web server at http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, port=5000)
