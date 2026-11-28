import re
from datetime import datetime, timezone
import config
import net

# Words that often appear in fake or malware-style repos
SUSPICIOUS_WORDS = re.compile(
    r"\b(crack(ed)?|keygen|patcher|activator|activation|license[- ]?key|serial[- ]?key|"
    r"free[- ]?download|download[- ]?free|mod[- ]?apk|premium[- ]?unlocked|bypass|"
    r"installer|desktop[- ]?suite|unlocked)\b",
    re.I,
)


def _owner_info(owner: str):
    headers = {"Accept": "application/vnd.github+json"}
    if config.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"
    r = net.get(f"https://api.github.com/users/{owner}", headers=headers)
    return r.json() if r else None


def looks_suspicious(c):
    """Returns (True/False, short reason). Only checks GitHub repos."""
    if c.source != "github":
        return False, ""

    # 1) suspicious words
    if SUSPICIOUS_WORDS.search(f"{c.name} {c.description}"):
        return True, "suspicious words in name or description"

    # 2) many stars but almost no forks
    stars = c.meta.get("stars", 0)
    forks = c.meta.get("forks")
    if forks is not None and stars >= 100 and forks < stars * 0.05:
        return True, f"{stars} stars but only {forks} forks (possible fake stars)"

    # 3) brand-new owner account with almost no followers
    info = _owner_info(c.name.split("/")[0])
    if info and info.get("created_at"):
        created = datetime.fromisoformat(info["created_at"].replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created).days
        followers = info.get("followers", 0)
        c.meta["owner_account_age_days"] = age_days
        c.meta["owner_followers"] = followers
        if age_days < 60 and followers < 10:
            return True, f"owner account is {age_days} days old with {followers} followers"
    return False, ""