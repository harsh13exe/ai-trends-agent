import sqlite3
from datetime import date
import config


def _conn():
    c = sqlite3.connect(config.DB_PATH)
    c.execute(
        "CREATE TABLE IF NOT EXISTS seen (key TEXT PRIMARY KEY, name TEXT, url TEXT, day TEXT)"
    )
    return c


def is_seen(key: str) -> bool:
    with _conn() as c:
        return c.execute("SELECT 1 FROM seen WHERE key=?", (key,)).fetchone() is not None


def mark_seen(key: str, name: str, url: str):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO seen VALUES (?,?,?,?)",
            (key, name, url, date.today().isoformat()),
        )
