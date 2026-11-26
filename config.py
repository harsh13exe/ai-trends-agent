import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = BASE_DIR / "trends.db"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
NUM_CTX = 8192

TOP_N = int(os.getenv("TOP_N", "5"))
MAX_SOURCE_CHARS = 10000  # text given to the model per tool

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# ---- Topic filters (edit freely) ----
HN_QUERIES = ["LLM", "AI", "machine learning", "open source model", "agents", "RAG", "fine-tuning"]
GITHUB_TERMS = ["llm", "ai agent", "machine learning", "rag", "diffusion", "mcp"]

_RELEVANT = re.compile(
    r"\b(ai|llm|llms|gpt|claude|gemini|llama|qwen|mistral|deepseek|agent|agents|rag|"
    r"machine learning|deep learning|neural|transformer|diffusion|embedding|fine-?tun\w*|"
    r"inference|model|models|openai|anthropic|hugging ?face|ollama|mcp|copilot)\b",
    re.I,
)

def is_relevant(text: str) -> bool:
    return bool(_RELEVANT.search(text or ""))

# How much we trust each source when ranking
SOURCE_WEIGHT = {"github": 1.0, "huggingface": 1.0, "hackernews": 0.9}
