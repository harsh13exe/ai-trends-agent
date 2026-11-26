import requests

BASE_HEADERS = {"User-Agent": "ai-trends-agent/0.1 (personal project)"}


def get(url, headers=None, timeout=20, **kw):
    h = dict(BASE_HEADERS)
    if headers:
        h.update(headers)
    try:
        r = requests.get(url, headers=h, timeout=timeout, **kw)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"[warn] GET failed {url[:90]}: {e}")
        return None
