"""
state.py
Keeps track of which post IDs we've already sent, so the digest doesn't
repeat itself. Stored as a flat JSON file so it can be committed back to
the repo by the GitHub Action (see .github/workflows/digest.yml).
"""

import json
import os

STATE_FILE = os.path.join(os.path.dirname(__file__), "seen_posts.json")
MAX_STORED = 2000  # keep the file from growing forever


def load_seen():
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
        return set(data.get("seen_ids", []))
    except Exception:
        return set()


def save_seen(seen_ids):
    ids_list = list(seen_ids)[-MAX_STORED:]
    with open(STATE_FILE, "w") as f:
        json.dump({"seen_ids": ids_list}, f)
