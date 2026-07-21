"""
filter.py
Scores posts so the digest surfaces well-scoped, paid, low-competition gigs
and buries vague "build me an app" or already-crowded posts.
"""

import re

# Words that suggest a real, scoped, paid task
POSITIVE_SIGNALS = [
    r"budget", r"paid", r"pay", r"hourly", r"fixed price",
    r"bug", r"fix", r"script", r"automation", r"integrate", r"integration",
    r"plugin", r"macro", r"spreadsheet", r"excel", r"google sheet",
    r"chrome extension", r"api", r"scrape", r"scraper", r"wordpress",
    r"small (task|job|project)", r"quick (task|job|fix)",
]

# Currency signals: symbols (any amount) and 3-letter currency codes (any amount).
# Covers USD/$, EUR/€, GBP/£, INR/₹, JPY/¥, and generic codes like CAD, AUD, etc.
CURRENCY_SYMBOL_PATTERN = r"[\$€£₹¥]\s?\d+"
CURRENCY_CODE_PATTERN = r"\b\d+\s?(usd|eur|gbp|inr|cad|aud|jpy|chf|sgd|nzd)\b|\b(usd|eur|gbp|inr|cad|aud|jpy|chf|sgd|nzd)\s?\d+\b"

# Words that suggest scope creep / too big for a quick paid gig, or noise
NEGATIVE_SIGNALS = [
    r"equity only", r"unpaid", r"no budget", r"exposure",
    r"build (me |us )?(a |an )?(full|complete|entire) (app|platform|saas|website)",
    r"co-?founder", r"partner (up|wanted)", r"looking for a team",
    r"long[- ]term commitment", r"full[- ]time", r"full time",
    r"intern(ship)?\b", r"permanent (position|role)", r"years? of experience",
    r"salary", r"benefits package", r"401k", r"health insurance",
    r"apply (now|here|today)", r"job description", r"we are hiring for",
    r"relocat(e|ion)", r"visa sponsorship",
]

# RemoteOK and WeWorkRemotely are structurally full-time job boards, not gig
# marketplaces — most of what they list is permanent roles, not one-off tasks.
# Penalize posts from these sources so only genuinely gig-shaped posts (strong
# currency + task signals) can still clear the bar.
JOB_BOARD_SOURCE_PENALTY = {
    "remoteok": -6,
    "weworkremotely": -6,
}

MAX_COMMENTS_FOR_LOW_COMPETITION = 15


def score_post(post):
    text = f"{post.get('title','')} {post.get('body','')}".lower()
    score = 0
    matched_positive = []

    for pattern in POSITIVE_SIGNALS:
        if re.search(pattern, text):
            score += 2
            matched_positive.append(pattern)

    for pattern in NEGATIVE_SIGNALS:
        if re.search(pattern, text):
            score -= 5

    # Structural penalty for sources that are full-time job boards by nature
    score += JOB_BOARD_SOURCE_PENALTY.get(post.get("source", ""), 0)

    # Low comment count = you're an early responder = better odds
    if post.get("num_comments", 0) <= MAX_COMMENTS_FOR_LOW_COMPETITION:
        score += 2
    else:
        score -= 2

    # Explicit currency mention (any currency, not just USD) is the strongest signal
    if re.search(CURRENCY_SYMBOL_PATTERN, text) or re.search(CURRENCY_CODE_PATTERN, text, re.IGNORECASE):
        score += 3
        matched_positive.append("currency_amount")

    post["_score"] = score
    post["_matched"] = matched_positive
    return score


def filter_and_rank(posts, min_score=2, top_n=8):
    for p in posts:
        score_post(p)
    ranked = sorted(posts, key=lambda p: p["_score"], reverse=True)
    good = [p for p in ranked if p["_score"] >= min_score]
    return good[:top_n]