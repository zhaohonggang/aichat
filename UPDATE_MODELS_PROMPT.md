# Update Google Models JSON - Prompt

## Input
You will receive a JSON array of Google models with fields:
- `model`: model name
- `category`: model category
- `rpm`: requests per minute (can be 0, null, or number)
- `tpm`: tokens per minute
- `tpd`: tokens per day

## Task
Update `config/google_models.json` with valid models.

## Steps

### 1. Filter out invalid models
Remove models where:
- `rpm` is `0`
- `rpm` is `null`
- `rpm` is `"Unlimited"` (cannot be used as number)

### 2. Convert model names to API IDs
Convert `model` field to proper API ID format:
- Replace spaces with hyphens
- Lowercase
- Examples:
  - "Gemini 2.5 Flash" → "gemini-2.5-flash"
  - "Gemma 3 1B" → "gemma-3-1b-it"

### 3. Test each model via API
Load API key from config:

```python
import requests
import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
with open(os.path.join(CONFIG_DIR, "settings.json"), "r") as f:
    settings = json.load(f)

GOOGLE_API_KEY = settings["google_api_key"]
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

models = json.load(open('config/google_models.json'))

working = []
for m in models:
    model_id = m['id']
    try:
        url = f'{GOOGLE_BASE_URL}/{model_id}:generateContent'
        response = requests.post(url, params={'key': GOOGLE_API_KEY}, json={
            'contents': [{'role': 'user', 'parts': [{'text': 'hi'}]}]
        }, timeout=10)
        if response.status_code == 200:
            working.append(m)
            print(f'OK: {model_id}')
        else:
            print(f'ERROR {response.status_code}: {model_id}')
    except requests.exceptions.ReadTimeout:
        # Keep models that timeout - they may work with longer timeout
        working.append(m)
        print(f'TIMEOUT (kept): {model_id}')
    except Exception as e:
        print(f'ERROR: {model_id} - {str(e)[:60]}')

# Save working models
json.dump(working, open('config/google_models.json', 'w'), indent=2)
```

models = json.load(open('config/google_models.json'))

working = []
for m in models:
    model_id = m['id']
    try:
        url = f'{GOOGLE_BASE_URL}/{model_id}:generateContent'
        response = requests.post(url, params={'key': GOOGLE_API_KEY}, json={
            'contents': [{'role': 'user', 'parts': [{'text': 'hi'}]}]
        }, timeout=10)
        if response.status_code == 200:
            working.append(m)
            print(f'OK: {model_id}')
        else:
            print(f'ERROR {response.status_code}: {model_id}')
    except Exception as e:
        print(f'ERROR: {model_id} - {str(e)[:60]}')

# Save working models
json.dump(working, open('config/google_models.json', 'w'), indent=2)
```

### 4. Verify final count
Only keep models that returned `200 OK`.