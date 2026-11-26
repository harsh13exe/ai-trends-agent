import json
import re
import requests
import config


def chat_json(system: str, user: str, retries: int = 2):
    payload = {
        "model": config.OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_ctx": config.NUM_CTX},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    for attempt in range(retries + 1):
        try:
            r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=payload, timeout=600)
            r.raise_for_status()
            raw = r.json()["message"]["content"]
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                m = re.search(r"\{.*\}", raw, re.S)
                if m:
                    return json.loads(m.group(0))
        except Exception as e:
            print(f"[llm] attempt {attempt + 1} failed: {e}")
    return None
