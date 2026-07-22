"""
trust_check.py
For GitHub bounty matches specifically, checks how old the issue author's
account and the repo itself are. A same-day (or near-same-day) account AND
repo, both posting a cash bounty, is a strong real-world scam/bait pattern
we've directly observed (e.g. accounts created the same day they post
several $10-25 bounties across freshly-cloned repos named after popular
libraries). This doesn't replace judgment, but flags the risk automatically
instead of requiring manual lookup every time.

Only called for the small number of finalist posts (top_n), not the full
scrape, to keep GitHub API usage well within free rate limits.
"""

import requests
from datetime import datetime, timezone

HEADERS = {"User-Agent": "gig-finder-bot/1.0 (personal use, contact: you@example.com)",
           "Accept": "application/vnd.github+json"}

NEW_ACCOUNT_THRESHOLD_DAYS = 7
NEW_REPO_THRESHOLD_DAYS = 7


def _days_since(iso_date_str):
    try:
        created = datetime.strptime(iso_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created).days
    except Exception:
        return None


def check_github_trust(author, repo_full_name):
    """
    Returns a dict: {"account_age_days": int|None, "repo_age_days": int|None,
    "warning": str|None}
    Fails silently (returns Nones, no warning) on any API error — this is a
    best-effort signal, not a hard requirement, and shouldn't break the whole
    pipeline if GitHub's API hiccups or rate-limits.
    """
    result = {"account_age_days": None, "repo_age_days": None, "warning": None}

    try:
        if author:
            resp = requests.get(f"https://api.github.com/users/{author}", headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                result["account_age_days"] = _days_since(resp.json().get("created_at", ""))
    except Exception as e:
        print(f"[trust_check] account check failed for {author}: {e}")

    try:
        if repo_full_name:
            resp = requests.get(f"https://api.github.com/repos/{repo_full_name}", headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                result["repo_age_days"] = _days_since(resp.json().get("created_at", ""))
    except Exception as e:
        print(f"[trust_check] repo check failed for {repo_full_name}: {e}")

    acc_age = result["account_age_days"]
    repo_age = result["repo_age_days"]

    if acc_age is not None and acc_age <= NEW_ACCOUNT_THRESHOLD_DAYS and \
       repo_age is not None and repo_age <= NEW_REPO_THRESHOLD_DAYS:
        result["warning"] = (
            f"⚠️ Both the account ({acc_age}d old) and repo ({repo_age}d old) are very new — "
            f"verify legitimacy before starting work."
        )
    elif acc_age is not None and acc_age <= NEW_ACCOUNT_THRESHOLD_DAYS:
        result["warning"] = f"⚠️ Account is only {acc_age} day(s) old — verify before starting work."
    elif repo_age is not None and repo_age <= NEW_REPO_THRESHOLD_DAYS:
        result["warning"] = f"⚠️ Repo is only {repo_age} day(s) old — verify before starting work."

    return result