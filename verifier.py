"""MVP verifier: every claim's quote must literally exist in the fetched source.
(Phase 2 adds an LLM judge that checks the quote truly supports the claim.)"""
import re


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def verify(entry: dict, source_text: str):
    src = _norm(source_text)
    claims = entry.get("claims") or []
    ok = 0
    for cl in claims:
        q = _norm(cl.get("quote", ""))
        cl["verified"] = len(q) >= 15 and q in src
        ok += cl["verified"]
    ratio = ok / len(claims) if claims else 0.0
    entry["verified_ratio"] = round(ratio, 2)
    if ratio >= 0.8:
        entry["status"] = "verified"
    elif ratio >= 0.5:
        entry["status"] = "partial"
    else:
        entry["status"] = "rejected"
    return entry
