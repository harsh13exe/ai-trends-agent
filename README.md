# AI/ML Daily Trends Agent (MVP)

Finds new AI/ML tools each day from GitHub, Hugging Face and Hacker News, reads the real
source text, writes a friendly explanation with a local Ollama model, checks every claim
against the source, then sends it to Telegram + email. 100% free.

## 1. Setup
1. Install Ollama: https://ollama.com  then run:
   `ollama pull qwen2.5:7b-instruct`   (about 5 GB, runs fine on 16 GB RAM)
2. `python -m venv venv` then activate it
   (Windows: `venv\Scripts\activate`, Mac/Linux: `source venv/bin/activate`)
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and fill it in.

## 2. Telegram (free)
1. In Telegram, message @BotFather, send `/newbot`, copy the token into `TELEGRAM_BOT_TOKEN`.
2. Send any message to your new bot.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser, find `"chat":{"id":123...}`
   and put that number in `TELEGRAM_CHAT_ID`.

## 3. Gmail (free)
Turn on 2-Step Verification, create an App Password at https://myaccount.google.com/apppasswords,
and put it in `EMAIL_APP_PASSWORD`. Set `EMAIL_USER` and `EMAIL_TO` to your address.

## 4. Test
`python main.py --no-send --top 2`   -> saves to `reports/` only, nothing is sent.
`python main.py`                      -> full run.

## 5. Schedule daily (laptop)
- Windows: Task Scheduler > Create Task > Trigger daily > Action: `venv\Scripts\python.exe`
  with argument `main.py`, "Start in" = project folder. In Settings tick
  "Run task as soon as possible after a scheduled start is missed".
- Mac/Linux: `crontab -e` then `0 8 * * * cd /path/to/ai-trends-agent && venv/bin/python main.py`

## How accuracy is protected
- Stars, license, dates come from APIs, not from the model.
- The model may only use fetched text; every claim needs an exact quote.
- Code checks the quote really exists in the source. Entries below 50% verified are dropped,
  50-80% are marked "partially verified".

## Roadmap
Phase 2: LLM judge in verifier, release watchlist, RSS blogs, Reddit.
Phase 3: Telegram feedback buttons, ranking weights, accuracy test set.
