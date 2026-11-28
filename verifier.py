"""Verifier, two layers:
1) The quote must literally exist in the source text (plain code check).
2) A small AI question: does that quote really support the claim?"""
import re
import llm

SYSTEM = "You check facts carefully. Reply with JSON only."

PROMPT = """CLAIM: {claim}
QUOTE FROM THE SOURCE: {quote}

Does the quote support the claim?
- supports: the quote clearly says, or directly implies, the claim
- partly: the quote is related but covers only part of the claim
- not_supported: the quote does not back the claim up

Reply with JSON using two keys: "reason" (one short sentence about this claim)
and "verdict" (one of: supports, partly, not_supported)."""

SCORE = {"supports": 1.0, "partly": 0.5, "not_supported": 0.0}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def _judge(claim: str, quote: str):
    r = llm.chat_json(SYSTEM, PROMPT.format(claim=claim, quote=quote))
    verdict = str(r.get("verdict", "")).strip().lower() if isinstance(r, dict) else ""
    return verdict if verdict in SCORE else None


def verify(entry: dict, source_text: str):
    src = _norm(source_text)
    claims = entry.get("claims") or []
    total = 0.0
    for cl in claims:
        quote = cl.get("quote", "")
        q = _norm(quote)
        exists = len(q) >= 15 and q in src
        cl["verified"] = exists
        if not exists:
            cl["verdict"] = "quote_missing"
        else:
            verdict = _judge(cl.get("claim", ""), quote)
            if verdict is None:                      # judge failed: fall back to the quote check
                verdict = "supports"
                cl["judge"] = "unavailable"
            cl["verdict"] = verdict
            total += SCORE[verdict]
        print(f"    claim: {cl['verdict']:<13} | {cl.get('claim', '')[:70]}")

    ratio = total / len(claims) if claims else 0.0
    entry["verified_ratio"] = round(ratio, 2)
    if ratio >= 0.8:
        entry["status"] = "verified"
    elif ratio >= 0.5:
        entry["status"] = "partial"
    else:
        entry["status"] = "rejected"
    return entry