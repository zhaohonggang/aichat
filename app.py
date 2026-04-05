import os
import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

with open(os.path.join(CONFIG_DIR, "settings.json"), "r") as f:
    settings = json.load(f)

GOOGLE_API_KEY = settings["google_api_key"]
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
EXTERNAL_API_URL = settings["external_api_url"]


def load_models():
    models = []

    google_models_path = os.path.join(CONFIG_DIR, "google_models.json")
    with open(google_models_path, "r") as f:
        for m in json.load(f):
            m["provider"] = "google"
            models.append(m)

    home_models_path = os.path.join(CONFIG_DIR, "home_models.json")
    with open(home_models_path, "r") as f:
        for m in json.load(f):
            m["provider"] = "external"
            models.append(m)

    return models


MODELS = load_models()


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
