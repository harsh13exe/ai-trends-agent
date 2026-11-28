import calendar
from datetime import datetime, timezone

import feedparser

import config
import net

for name, url in config.BLOG_FEEDS.items():
    r = net.get(url)
    if not r:
        print(name, "-> download failed")
        continue
    print(name, r.status_code, r.headers.get("content-type"), len(r.content), "bytes")
    d = feedparser.parse(r.content)
    print("  entries:", len(d.entries))
    dates = [calendar.timegm(e.get("published_parsed") or e.get("updated_parsed"))
             for e in d.entries if (e.get("published_parsed") or e.get("updated_parsed"))]
    if dates:
        newest = datetime.fromtimestamp(max(dates), tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        print("  newest post:", newest, "| posts with a date:", len(dates))
    else:
        print("  no dated posts. Start of the response:", r.text[:150].replace("\n", " "))