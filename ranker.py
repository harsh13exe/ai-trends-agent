"""Dedup + rank. Pure Python, no LLM needed for the MVP."""
import re
from collections import defaultdict
import config
import db


def key_for(url: str) -> str:
    u = url.lower().split("#")[0].split("?")[0]
    u = re.sub(r"^https?://(www\.)?", "", u).rstrip("/")
    for pat in (r"(github\.com/[^/]+/[^/]+)", r"(huggingface\.co/(?:spaces/)?[^/]+/[^/]+)"):
        m = re.match(pat, u)
        if m:
            return m.group(1)
    return u


def rank(cands):
    # 1) percentile of each item inside its own source
    by_src = defaultdict(list)
    for c in cands:
        c.key = key_for(c.url)
        by_src[c.source].append(c)
    pct = {}
    for src, items in by_src.items():
        items.sort(key=lambda x: x.signal, reverse=True)
        for i, c in enumerate(items):
            pct[id(c)] = 1 - i / max(len(items), 1)

    # 2) merge duplicates across sources
    merged = {}
    for c in cands:
        s = pct[id(c)] * config.SOURCE_WEIGHT.get(c.source, 0.8)
        if c.key in merged:
            m = merged[c.key]
            m.sources.append(c.source)
            m.score += s + 0.5            # bonus: seen on several platforms
            if c.discussion and not m.discussion:
                m.discussion = c.discussion
            for k, v in c.meta.items():
                m.meta.setdefault(k, v)
            if c.source in ("github", "huggingface"):
                m.name, m.url, m.description = c.name, c.url, c.description or m.description
        else:
            c.sources = [c.source]
            c.score = s
            merged[c.key] = c

    # 3) relevance boost and drop already-covered items
    final = []
    for c in merged.values():
        if db.is_seen(c.key):
            continue
        if config.is_relevant(c.name + " " + c.description):
            c.score += 0.3
        final.append(c)
    final.sort(key=lambda x: x.score, reverse=True)
    return final
