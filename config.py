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
MAX_SOURCE_CHARS = 10000   # text given to the model per tool
MAX_PER_GROUP = 2          # at most 2 digest entries from the same source or blog

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# ---- Topic filters (edit freely) ----
HN_QUERIES = ["LLM", "AI", "machine learning", "open source model", "agents", "RAG", "fine-tuning"]
GITHUB_TERMS = ["llm", "ai agent", "machine learning", "rag", "diffusion", "mcp"]

_STRONG = re.compile(
    r"\b(ai|llm|llms|gpt|claude|gemini|llama|qwen|mistral|deepseek|rag|machine learning|"
    r"deep learning|neural network|transformers?|diffusion|embeddings?|fine-?tun\w*|openai|"
    r"anthropic|hugging ?face|ollama|mcp|langchain|ai agents?|agentic|generative)\b",
    re.I,
)
_WEAK = re.compile(r"\b(agents?|models?|inference|copilot|prompts?|vector)\b", re.I)


def is_relevant(text: str) -> bool:
    """Layer 1 (cheap): needs one strong AI/ML word, or two different weak ones."""
    text = text or ""
    if _STRONG.search(text):
        return True
    return len({m.lower() for m in _WEAK.findall(text)}) >= 2


# How much we trust each source when ranking
SOURCE_WEIGHT = {"github": 1.0, "huggingface": 1.0, "hackernews": 0.9, "blog": 1.1, "release": 1.0}

# ---- Step 3: official blogs with a working RSS feed (name -> feed URL) ----
BLOG_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Mistral AI": "https://mistral.ai/news/rss",
}
BLOG_MAX_AGE_HOURS = 168   # only posts from the last 7 days

# ---- Step 4: projects whose new releases you want to hear about ----
WATCHLIST = [
    "ollama/ollama",
    "huggingface/transformers",
    "vllm-project/vllm",
    "pytorch/pytorch",
    "open-webui/open-webui",
    "comfyanonymous/ComfyUI",
    "run-llama/llama_index",
]
RELEASE_MAX_AGE_HOURS = 336        # releases from the last 14 days
RELEASE_ONLY_MAJOR_MINOR = False   # False = also keep releases like 0.40.19 (many projects only publish these)