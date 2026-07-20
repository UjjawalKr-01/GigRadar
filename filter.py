"""
filter.py
Scores posts so the digest surfaces well-scoped, paid, low-competition gigs
and buries vague "build me an app" or already-crowded posts.
"""

import re

# Words that suggest a real, scoped, paid task
POSITIVE_SIGNALS = [
    r"\$\d+", r"budget", r"paid", r"pay", r"hourly", r"fixed price",
    r"bug", r"fix", r"script", r"automation", r"integrate", r"integration",
    r"plugin", r"macro", r"spreadsheet", r"excel", r"google sheet",
    r"chrome extension", r"api", r"scrape", r"scraper", r"wordpress",
    r"small (task|job|project)", r"quick (task|job|fix)",
]

# Words that suggest scope creep / too big for a quick paid gig, or noise
NEGATIVE_SIGNALS = [
    r"equity only", r"unpaid", r"no budget", r"exposure",
    r"build (me |us )?(a |an )?(full|complete|entire) (app|platform|saas|website)",
    r"co-?founder", r"partner (up|wanted)", r"looking for a team",
    r"long[- ]term commitment", r"full[- ]time",
]

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

    # Low comment count = you're an early responder = better odds
    if post.get("num_comments", 0) <= MAX_COMMENTS_FOR_LOW_COMPETITION:
        score += 2
    else:
        score -= 2

    # Explicit $ mention is the single strongest signal
    if re.search(r"\$\d{2,4}", text):
        score += 3

    post["_score"] = score
    post["_matched"] = matched_positive
    return score


def filter_and_rank(posts, min_score=2, top_n=8):
    for p in posts:
        score_post(p)
    ranked = sorted(posts, key=lambda p: p["_score"], reverse=True)
    good = [p for p in ranked if p["_score"] >= min_score]
    return good[:top_n]
