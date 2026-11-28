import config
import db
import llm

# Categories we keep. Add "ai_feature" here if you also want AI-powered everyday apps.
KEEP = {"ai_tool"}
VALID = {"ai_tool", "ai_feature", "not_ai"}

SYSTEM = ("You are a strict filter for a daily digest read by a software developer who builds with AI/ML. "
          "Reply with JSON only.")

PROMPT = """Classify this item into exactly one category. Judge by the excerpt, not only by the title.

- ai_tool: mainly about building, running, training, evaluating, deploying or understanding AI/ML.
  Examples: models, LLM frameworks, agent tools, RAG and vector tools, inference engines, datasets,
  ML libraries, image/video/audio generation models and their tooling, new model, product or API
  launches announced by AI labs, important AI research.
- ai_feature: an everyday end-user app or toy that only uses AI inside (video editors, chat toys,
  wallpaper apps, shopping bots), or a personal blog post or opinion piece that only mentions AI in passing.
- not_ai: not about AI/ML at all.

ITEM NAME: {name}
DESCRIPTION: {desc}
TOPICS: {topics}
SOURCE: {source}
EXCERPT FROM THE PAGE: {excerpt}

Reply with JSON using two keys: "category" (one of ai_tool, ai_feature, not_ai) and
"reason" (one short sentence written by you about this specific item)."""


def passes_keywords(c):
    """Cheap check, run BEFORE downloading anything."""
    if c.source in ("huggingface", "blog", "release"):
        return True
    return config.is_relevant(f"{c.name} {c.description} {c.meta.get('topics', '')}")


def is_relevant(c, text=""):
    """Returns (True/False, short reason). `text` is the downloaded page or README."""
    if c.source == "huggingface" and c.meta.get("type") == "model":
        return True, "Hugging Face model"

    # you chose these projects yourself, so their releases are relevant by definition
    if c.source == "release":
        return True, "release of a project on your watchlist"

    topics = c.meta.get("topics", "")
    if not passes_keywords(c):
        return False, "no AI/ML keywords"

    cached = db.get_judgement(c.key)
    if cached is not None:
        return cached

    r = llm.chat_json(SYSTEM, PROMPT.format(
        name=c.name, desc=(c.description or "none")[:300], topics=topics or "none",
        source=c.source, excerpt=(text or "not available")[:800]))
    category = str(r.get("category", "")).strip().lower() if isinstance(r, dict) else ""
    if category not in VALID:
        return True, "judge unavailable (kept)"      # fail open: never drop everything by accident

    ok = category in KEEP
    reason = f"{category}: {str(r.get('reason', ''))[:160]}"
    db.set_judgement(c.key, ok, reason)
    return ok, reason