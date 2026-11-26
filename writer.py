import llm

SYSTEM = (
    "You are a careful, friendly tech writer helping a developer learn about new AI/ML tools. "
    "Use ONLY the SOURCE TEXT and FACTS provided. Never add facts from your own memory. "
    "If something is not in the source, write 'Not stated in the source'. "
    "Use simple, human, non-hype language. Reply with JSON only."
)

TEMPLATE = """TOOL: {name}
URL: {url}

FACTS (from APIs, trustworthy):
{facts}

SOURCE TEXT:
\"\"\"{text}\"\"\"

Write a JSON object with exactly these keys:
{{
  "summary": "1-2 simple sentences: what it is",
  "why_it_matters": "1-2 sentences in plain language",
  "who_should_use": "who benefits, in one sentence",
  "quick_start": "install/first steps ONLY if present in the source, else 'Not stated in the source'",
  "pros": ["2-3 short points based on the source"],
  "cons": ["1-3 limits or caveats based on the source; say 'Not stated' if none"],
  "alternatives": ["0-2 well-known alternatives (mark as your own suggestion)"],
  "claims": [
    {{"claim": "a factual statement you made above", "quote": "EXACT text copied word-for-word from SOURCE TEXT, max 200 chars"}}
  ]
}}
Give 3 to 6 claims. Every quote must be copied exactly from the SOURCE TEXT."""


def write(c, text, facts):
    prompt = TEMPLATE.format(name=c.name, url=c.url, facts=facts, text=text)
    return llm.chat_json(SYSTEM, prompt)
