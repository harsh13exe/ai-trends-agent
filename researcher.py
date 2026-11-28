"""Fetch the real source text. Facts come from APIs, never from the model."""
import re
from bs4 import BeautifulSoup
import config
import net


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "svg", "noscript"]):
        t.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def research(c):
    """Returns (source_text, facts_text, source_links)."""
    text = ""
    links = [c.url]
    if c.discussion:
        links.append(c.discussion)

    if c.source == "release":
        text = c.description                          # the release notes
    elif c.key.startswith("github.com/"):
        repo = c.key.replace("github.com/", "")
        r = net.get(
            f"https://api.github.com/repos/{repo}/readme",
            headers={"Accept": "application/vnd.github.raw"},
        )
        text = r.text if r else ""
    elif c.key.startswith("huggingface.co/") and c.source != "blog":
        path = c.key.replace("huggingface.co/", "")
        r = net.get(f"https://huggingface.co/{path}/raw/main/README.md")
        text = r.text if r else ""

    if len(text) < 300 and c.source != "release":     # generic web page / fallback
        r = net.get(c.url)
        if r and "text/html" in r.headers.get("content-type", ""):
            text = _clean_html(r.text)
        elif r:
            text = r.text

    # blog page blocked or empty -> use the feed's own summary
    if len(text) < 300 and c.source == "blog" and c.description:
        text = c.description

    text = re.sub(r"\s+", " ", text).strip()[: config.MAX_SOURCE_CHARS]
    facts = "\n".join(f"- {k}: {v}" for k, v in c.meta.items()) or "- (none)"
    return text, facts, links