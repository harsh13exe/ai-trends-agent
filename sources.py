"""Discovery: plain Python, no LLM. All sources are free."""
from datetime import datetime, timedelta, timezone
import config
import net
from models import Candidate


def fetch_hackernews():
    since = int((datetime.now(timezone.utc) - timedelta(hours=36)).timestamp())
    found = {}
    for q in config.HN_QUERIES:
        r = net.get(
            "https://hn.algolia.com/api/v1/search",
            params={
                "query": q,
                "tags": "story",
                "numericFilters": f"created_at_i>{since},points>15",
                "hitsPerPage": 30,
            },
        )
        if not r:
            continue
        for h in r.json().get("hits", []):
            title = h.get("title") or ""
            if not config.is_relevant(title):
                continue
            thread = f"https://news.ycombinator.com/item?id={h['objectID']}"
            found[h["objectID"]] = Candidate(
                name=title,
                url=h.get("url") or thread,
                source="hackernews",
                signal=h.get("points", 0),
                description=title,
                discussion=thread,
                meta={"hn_points": h.get("points", 0), "hn_comments": h.get("num_comments", 0)},
            )
    return list(found.values())


def fetch_github():
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    found = {}
    for term in config.GITHUB_TERMS:
        r = net.get(
            "https://api.github.com/search/repositories",
            headers=headers,
            params={
                "q": f"{term} created:>{since} stars:>40",
                "sort": "stars",
                "order": "desc",
                "per_page": 15,
            },
        )
        if not r:
            continue
        for repo in r.json().get("items", []):
            created = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
            age_days = max((now - created).total_seconds() / 86400, 1)
            found[repo["full_name"]] = Candidate(
                name=repo["full_name"],
                url=repo["html_url"],
                source="github",
                signal=repo["stargazers_count"] / age_days,  # stars per day = velocity
                description=repo.get("description") or "",
                meta={
                    "stars": repo["stargazers_count"],
                    "license": (repo.get("license") or {}).get("spdx_id") or "Not stated",
                    "language": repo.get("language") or "Not stated",
                    "created": repo["created_at"][:10],
                    "last_push": repo["pushed_at"][:10],
                },
            )
    return list(found.values())


def fetch_huggingface():
    out = []
    for kind in ("models", "spaces"):
        r = net.get(f"https://huggingface.co/api/{kind}", params={"sort": "trendingScore", "limit": 20})
        if not r:
            continue
        for m in r.json():
            mid = m.get("id")
            if not mid:
                continue
            prefix = "spaces/" if kind == "spaces" else ""
            out.append(
                Candidate(
                    name=mid,
                    url=f"https://huggingface.co/{prefix}{mid}",
                    source="huggingface",
                    signal=m.get("trendingScore") or m.get("likes", 0),
                    description=m.get("pipeline_tag") or kind[:-1],
                    meta={
                        "likes": m.get("likes", 0),
                        "downloads": m.get("downloads", "n/a"),
                        "type": kind[:-1],
                        "task": m.get("pipeline_tag") or "n/a",
                    },
                )
            )
    return out


def discover():
    allc = []
    for fn in (fetch_github, fetch_huggingface, fetch_hackernews):
        try:
            items = fn()
            print(f"[discover] {fn.__name__}: {len(items)} candidates")
            allc += items
        except Exception as e:
            print(f"[warn] {fn.__name__} crashed: {e}")
    return allc
