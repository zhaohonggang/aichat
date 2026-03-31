import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

GOOGLE_API_KEY = "AIzaSyAaq5l8Jjt-LluMow96oe5jwovplix37uU"
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

MODELS = [
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "google",
        "rpm": 10,
        "rpd": 250,
    },
    {
        "id": "gemini-flash-latest",
        "name": "Gemini Flash Latest",
        "provider": "google",
        "rpm": 10,
        "rpd": 250,
    },
    {
        "id": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "provider": "google",
        "rpm": 10,
        "rpd": 250,
    },
    {
        "id": "gemini-2.0-flash-lite",
        "name": "Gemini 2.0 Flash-Lite",
        "provider": "google",
        "rpm": 15,
        "rpd": 1000,
    },
    {
        "id": "gemini-pro-latest",
        "name": "Gemini Pro Latest",
        "provider": "google",
        "rpm": 5,
        "rpd": 100,
    },
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "google",
        "rpm": 5,
        "rpd": 100,
    },
    {
        "id": "gemma-3-1b-it",
        "name": "Gemma 3 1B",
        "provider": "google",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "gemma-3-4b-it",
        "name": "Gemma 3 4B",
        "provider": "google",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "gemma-3-12b-it",
        "name": "Gemma 3 12B",
        "provider": "google",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "gemma-3-27b-it",
        "name": "Gemma 3 27B",
        "provider": "google",
        "rpm": 30,
        "rpd": 14400,
    },
    {
        "id": "Home-0.0.1",
        "name": "Home 0.0.1",
        "provider": "external",
        "rpm": 999999,
        "rpd": 999999,
    },
]

EXTERNAL_API_URL = "http://localhost:5010"


def call_google_gemini(model_id: str, message: str, history: list = None):
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

    response = requests.post(
        url, params=params, json={"contents": contents}, timeout=60
    )
    response.raise_for_status()
    result = response.json()
    return result["candidates"][0]["content"]["parts"][0]["text"]


def call_external_api(model_id: str, message: str, history: list = None):
    messages = []
    for msg in history or []:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = requests.post(
        f"{EXTERNAL_API_URL}/v1/chat/completions",
        json={"model": model_id, "messages": messages},
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]


@app.route("/")
def index():
    return render_template("index.html", models=MODELS)


@app.route("/api/models")
def get_models():
    return jsonify({"models": MODELS})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    model_id = data.get("model")
    message = data.get("message")
    history = data.get("history", [])

    if not model_id or not message:
        return jsonify({"error": "Missing model or message"}), 400

    model_info = next((m for m in MODELS if m["id"] == model_id), None)
    if not model_info:
        return jsonify({"error": f"Model {model_id} not found"}), 404

    try:
        if model_info["provider"] == "google":
            content = call_google_gemini(model_id, message, history)
        else:
            content = call_external_api(model_id, message, history)

        return jsonify({"response": content, "model": model_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("AI Chat - Web Interface")
    print("=" * 50)
    print(f"\nAvailable Models ({len(MODELS)}):")
    for m in MODELS:
        print(f"  - {m['name']} ({m['provider']})")
    print("\nWeb: http://localhost:5000")
    print("=" * 50)

    app.run(debug=True, port=5000)
