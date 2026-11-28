"""Discovery: plain Python, no LLM. All sources are free."""
import calendar
import re
from datetime import datetime, timedelta, timezone
from html import unescape

import feedparser

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
                    "topics": ", ".join((repo.get("topics") or [])[:8]) or "none",
                    "forks": repo["forks_count"],
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


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def fetch_blogs():
    """Step 3: recent posts from official blogs (RSS feeds)."""
    now = datetime.now(timezone.utc)
    out = []
    for blog, url in config.BLOG_FEEDS.items():
        r = net.get(url)
        if not r:
            continue
        count = 0
        for e in feedparser.parse(r.content).entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            title = (e.get("title") or "").strip()
            link = e.get("link")
            if not (ts and title and link):
                continue
            published = datetime.fromtimestamp(calendar.timegm(ts), tz=timezone.utc)
            age_hours = (now - published).total_seconds() / 3600
            if age_hours > config.BLOG_MAX_AGE_HOURS:
                continue
            summary = _strip_html(e.get("summary") or e.get("description") or "")[:1500]
            out.append(
                Candidate(
                    name=f"{blog}: {title}",
                    url=link,
                    source="blog",
                    signal=config.BLOG_MAX_AGE_HOURS - age_hours,   # newer = higher
                    description=summary or title,
                    meta={"blog": blog, "published": published.strftime("%Y-%m-%d")},
                )
            )
            count += 1
        print(f"[feed] {blog}: {count} recent posts")
    return out


def fetch_releases():
    """Step 4: new releases of the projects on your watchlist."""
    now = datetime.now(timezone.utc)
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    out = []
    for repo in config.WATCHLIST:
        r = net.get(f"https://api.github.com/repos/{repo}/releases", headers=headers, params={"per_page": 5})
        if not r:
            continue
        count = 0
        for rel in r.json():
            if rel.get("draft") or rel.get("prerelease") or not rel.get("published_at"):
                continue
            tag = rel.get("tag_name") or ""
            m = re.match(r"v?(\d+)\.(\d+)(?:\.(\d+))?", tag)
            if not m:
                continue                      # tags that are not version numbers are skipped
            if re.search(r"(rc|alpha|beta|dev)\d*$", tag, re.I):
                continue                      # test versions such as 0.33.0rc3
            if config.RELEASE_ONLY_MAJOR_MINOR and int(m.group(3) or 0) != 0:
                continue                      # patch release, not interesting
            published = datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00"))
            age_hours = (now - published).total_seconds() / 3600
            if age_hours > config.RELEASE_MAX_AGE_HOURS:
                continue
            out.append(
                Candidate(
                    name=f"{repo} {rel.get('name') or tag}",
                    url=rel["html_url"],
                    source="release",
                    signal=config.RELEASE_MAX_AGE_HOURS - age_hours,   # newer = higher
                    description=(rel.get("body") or "").strip()[:6000],  # the release notes
                    meta={"project": repo, "version": tag, "published": published.strftime("%Y-%m-%d")},
                )
            )
            count += 1
            break                             # only the newest release per project
        print(f"[release] {repo}: {count} new")
    return out


def discover():
    allc = []
    for fn in (fetch_github, fetch_huggingface, fetch_hackernews, fetch_blogs, fetch_releases):
        try:
            items = fn()
            print(f"[discover] {fn.__name__}: {len(items)} candidates")
            allc += items
        except Exception as e:
            print(f"[warn] {fn.__name__} crashed: {e}")
    return allc