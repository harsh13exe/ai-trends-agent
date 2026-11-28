"""Daily AI/ML trends agent.  Usage: python main.py [--no-send] [--top N]"""
import argparse
import config
import db
import publisher
import ranker
import relevance
import researcher
import sources
import trust                                   # NEW
import verifier
import writer


def run(send: bool, top_n: int):
    cands = ranker.rank(sources.discover())
    print(f"[rank] {len(cands)} fresh candidates")

    entries = []
    for c in cands[: top_n * 4]:               # CHANGED: bigger buffer
        if len(entries) >= top_n:
            break
        print(f"[work] {c.name}  (stars={c.meta.get('stars', '-')}, forks={c.meta.get('forks', '-')})")

        bad, why = trust.looks_suspicious(c)
        if bad:
            print(f"  skip (suspicious): {why}")
            db.mark_seen(c.key, c.name, c.url)
            continue

        ok, why = relevance.is_relevant(c)
        if not ok:
            print(f"  skip (not AI/ML): {why}")
            db.mark_seen(c.key, c.name, c.url)
            continue
        print(f"  AI/ML check passed: {why}")

        text, facts, links = researcher.research(c)
        if len(text) < 200:
            print("  skip: not enough source text")
            continue
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