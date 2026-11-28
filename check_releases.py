import config
import net

headers = {"Accept": "application/vnd.github+json"}
if config.GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"

for repo in config.WATCHLIST:
    r = net.get(f"https://api.github.com/repos/{repo}/releases", headers=headers, params={"per_page": 4})
    if not r:
        print(repo, "-> failed")
        continue
    print(repo)
    for rel in r.json():
        flags = ("prerelease " if rel.get("prerelease") else "") + ("draft" if rel.get("draft") else "")
        print("   ", rel["tag_name"], (rel.get("published_at") or "")[:10], flags)