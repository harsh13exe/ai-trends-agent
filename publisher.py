import smtplib
from datetime import date
from email.mime.text import MIMEText
import requests
import config

BADGE = {"verified": "✅ Verified", "partial": "⚠️ Partially verified"}


def _lst(items):
    items = items if isinstance(items, list) else [str(items)]
    return "\n".join(f"  • {i}" for i in items)


def format_entry(e: dict, idx: int) -> str:
    links = "\n".join(f"  - {u}" for u in e["links"])
    return (
        f"{idx}. {e['name']}  [{BADGE.get(e['status'], '')}]\n"
        f"{e['summary']}\n\n"
        f"Why it matters: {e['why_it_matters']}\n"
        f"Who should use it: {e['who_should_use']}\n"
        f"Quick start: {e['quick_start']}\n\n"
        f"Pros:\n{_lst(e['pros'])}\n"
        f"Cons:\n{_lst(e['cons'])}\n"
        f"Alternatives (model's suggestion, unverified):\n{_lst(e['alternatives'])}\n\n"
        f"Sources:\n{links}\n"
    )


def build_digest(entries) -> str:
    head = f"AI/ML Daily Trends - {date.today().isoformat()}\n{'=' * 40}\n\n"
    if not entries:
        return head + "No verified items today."
    return head + "\n\n".join(format_entry(e, i + 1) for i, e in enumerate(entries))


def save_markdown(text: str):
    config.REPORTS_DIR.mkdir(exist_ok=True)
    p = config.REPORTS_DIR / f"{date.today().isoformat()}.md"
    p.write_text(text, encoding="utf-8")
    return p


def send_telegram(entries):
    if not (config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID):
        print("[telegram] not configured, skipping")
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    msgs = [f"AI/ML Daily Trends - {date.today().isoformat()}"] + [
        format_entry(e, i + 1) for i, e in enumerate(entries)
    ]
    for m in msgs:
        for i in range(0, len(m), 4000):  # Telegram limit is 4096 chars
            r = requests.post(
                url,
                json={"chat_id": config.TELEGRAM_CHAT_ID, "text": m[i : i + 4000],
                      "disable_web_page_preview": True},
                timeout=30,
            )
            if not r.ok:
                print("[telegram] error:", r.text)


def send_email(text: str):
    if not (config.EMAIL_USER and config.EMAIL_APP_PASSWORD and config.EMAIL_TO):
        print("[email] not configured, skipping")
        return
    msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = f"AI/ML Daily Trends - {date.today().isoformat()}"
    msg["From"] = config.EMAIL_USER
    msg["To"] = config.EMAIL_TO
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(config.EMAIL_USER, config.EMAIL_APP_PASSWORD)
        s.send_message(msg)
    print("[email] sent")
