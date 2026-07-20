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
    """Returns True if the digest was successfully delivered, False otherwise.
    Callers should NOT mark posts as 'seen' if this returns False, so nothing
    gets lost silently on a delivery failure."""
    if not BOT_TOKEN or not CHAT_ID:
        print("[notifier] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — printing digest instead:\n")
        print(text)
        return False

    # Strip any stray whitespace/newlines that can sneak in via copy-paste into secrets
    token = BOT_TOKEN.strip()
    chat_id = CHAT_ID.strip()

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Split into chunks if the digest is long
    chunks = [text[i:i + TELEGRAM_MSG_LIMIT] for i in range(0, len(text), TELEGRAM_MSG_LIMIT)] or [text]

    all_ok = True
    for chunk in chunks:
        try:
            resp = requests.post(url, data={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            }, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[notifier] Failed to send Telegram message: {e}")
            all_ok = False

    return all_ok
