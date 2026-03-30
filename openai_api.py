import os
import time
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

GOOGLE_API_KEY = "AIzaSyAaq5l8Jjt-LluMow96oe5jwovplix37uU"
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

MODELS = [
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
    {"id": "gemini-flash-latest", "name": "Gemini Flash Latest"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash-Lite"},
    {"id": "gemini-pro-latest", "name": "Gemini Pro Latest"},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
    {"id": "gemma-3-1b-it", "name": "Gemma 3 1B"},
    {"id": "gemma-3-4b-it", "name": "Gemma 3 4B"},
    {"id": "gemma-3-12b-it", "name": "Gemma 3 12B"},
    {"id": "gemma-3-27b-it", "name": "Gemma 3 27B"},
    {"id": "grant-0.1", "name": "Grant 0.1"},
]

GRANT_MODEL_ID = "grant-0.1"
GRANT_RESPONSE = "Hello, I am Grant 0.1"


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


@app.route("/v1/models", methods=["GET"])
def openai_models():
    return jsonify(
        {
            "object": "list",
            "data": [
                {
                    "id": m["id"],
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "local",
                }
                for m in MODELS
            ],
        }
    )


@app.route("/v1/models/<model_id>", methods=["GET"])
def openai_model_info(model_id):
    for m in MODELS:
        if m["id"] == model_id:
            return jsonify(
                {
                    "id": m["id"],
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "local",
                    "permission": [],
                    "root": m["id"],
                    "parent": None,
                }
            )
    return jsonify(
        {"error": {"message": "Model not found", "type": "invalid_request_error"}}
    ), 404


@app.route("/v1/chat/completions", methods=["POST"])
def openai_chat_completions():
    data = request.json
    model_id = data.get("model", GRANT_MODEL_ID)
    messages = data.get("messages", [])

    if model_id == GRANT_MODEL_ID:
        content = GRANT_RESPONSE
    else:
        last_message = messages[-1] if messages else {}
        message = last_message.get("content", "")
        history = []
        for msg in messages[:-1]:
            if msg.get("role") in ["user", "assistant"]:
                history.append({"role": msg["role"], "content": msg.get("content", "")})
        try:
            content = call_gemini(model_id, message, history)
        except Exception as e:
            return jsonify({"error": {"message": str(e), "type": "api_error"}}), 500

    return jsonify(
        {
            "id": f"chatcmpl-{os.urandom(8).hex()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": sum(
                    len(m.get("content", "").split()) for m in messages
                ),
                "completion_tokens": len(content.split()),
                "total_tokens": sum(len(m.get("content", "").split()) for m in messages)
                + len(content.split()),
            },
        }
    )


if __name__ == "__main__":
    print("=" * 50)
    print("OpenAI Compatible API Server")
    print("=" * 50)
    print(f"\nAvailable Models ({len(MODELS)}):")
    for model in MODELS:
        print(f"  - {model['name']}")
    print(f"\nGrant Model: {GRANT_MODEL_ID}")
    print("\nStarting API server at http://localhost:5001")
    print("=" * 50)

    app.run(debug=True, port=5001)
