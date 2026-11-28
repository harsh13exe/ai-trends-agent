"""Daily AI/ML trends agent.  Usage: python main.py [--no-send] [--top N]"""
import argparse
from collections import Counter

import config
import db
import publisher
import ranker
import relevance
import researcher
import sources
import trust
import verifier
import writer


def run(send: bool, top_n: int):
    cands = ranker.diversify(ranker.rank(sources.discover()))
    print(f"[rank] {len(cands)} fresh candidates")

    entries = []
    per_group = Counter()                      # how many entries each source already has
    for c in cands[: top_n * 6]:               # buffer: some will be skipped
        if len(entries) >= top_n:
            break
        group = c.meta.get("blog") or c.source
        if per_group[group] >= config.MAX_PER_GROUP:
            print(f"[skip] {c.name} (already have {config.MAX_PER_GROUP} from {group})")
            continue

        print(f"[work] {c.name}  (stars={c.meta.get('stars', '-')}, forks={c.meta.get('forks', '-')})")

        # 1) cheap checks first
        bad, why = trust.looks_suspicious(c)
        if bad:
            print(f"  skip (suspicious): {why}")
            db.mark_seen(c.key, c.name, c.url)
            continue
        if not relevance.passes_keywords(c):
            print("  skip (not AI/ML): no AI/ML keywords")
            db.mark_seen(c.key, c.name, c.url)
            continue

        # 2) download the real text
        text, facts, links = researcher.research(c)
        if len(text) < 200:
            print("  skip: not enough source text")
            continue

        # 3) AI judge, with a page excerpt
        ok, why = relevance.is_relevant(c, text)
        if not ok:
            print(f"  skip (not AI/ML): {why}")
            db.mark_seen(c.key, c.name, c.url)
            continue
        print(f"  AI/ML check passed: {why}")

        # 4) write, then verify
        e = writer.write(c, text, facts)
        if not e:
            print("  skip: model gave no valid JSON")
            continue
        e = verifier.verify(e, text)
        print(f"  status={e['status']} ratio={e['verified_ratio']}")
        if e["status"] == "rejected":
            continue
        e.update(name=c.name, links=links)
        for k, d in (("summary", ""), ("why_it_matters", ""), ("who_should_use", ""),
                     ("quick_start", "Not stated in the source")):
            e.setdefault(k, d)
        for k in ("pros", "cons", "alternatives"):
            e.setdefault(k, [])
        entries.append(e)
        per_group[group] += 1
        db.mark_seen(c.key, c.name, c.url)

    digest = publisher.build_digest(entries)
    path = publisher.save_markdown(digest)
    print(f"[saved] {path}")
    if send and entries:
        publisher.send_telegram(entries)
        publisher.send_email(digest)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-send", action="store_true", help="only save the report locally")
    ap.add_argument("--top", type=int, default=config.TOP_N)
    a = ap.parse_args()
    run(send=not a.no_send, top_n=a.top)