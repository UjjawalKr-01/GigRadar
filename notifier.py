"""
notifier.py
Sends the compiled digest to you via Telegram.
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars (see README for setup).
"""

import os
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

TELEGRAM_MSG_LIMIT = 4000  # Telegram caps messages around 4096 chars


def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("[notifier] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printing digest instead:\n")
        print(text)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    # Split into chunks if the digest is long
    chunks = [text[i:i + TELEGRAM_MSG_LIMIT] for i in range(0, len(text), TELEGRAM_MSG_LIMIT)] or [text]

    for chunk in chunks:
        try:
            resp = requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": chunk,
                "disable_web_page_preview": True,
            }, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[notifier] Failed to send Telegram message: {e}")
