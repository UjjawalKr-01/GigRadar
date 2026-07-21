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

# These bounty posts are explicitly targeting autonomous AI coding agents, not
# human freelancers — often tied to obscure/unverified crypto-adjacent payment
# platforms. Given real scam/wasted-effort risk, exclude these hard rather than
# just discouraging them.
AGENT_BAIT_SIGNALS = [
    r"ready for agent", r"\bagentic\b", r"for agents\b", r"\bai agent\b",
]
AGENT_BAIT_PENALTY = -20

# RemoteOK, WeWorkRemotely, and Jobicy are all general remote job boards —
# mostly full-time roles, not gig marketplaces. GitHub bounty issues, by
# contrast, are pre-filtered to be paid bounty work by their label, so being
# "just tagged bounty" is itself a strong signal even with no $ in the text.
SOURCE_SCORE_ADJUSTMENT = {
    "remoteok": -6,
    "weworkremotely": -6,
    "jobicy": -6,
    "github_bounty": 3,
}

# Jobicy provides a real job_type field per listing (e.g. "full-time", "freelance",
# "contract") — much more reliable than guessing from keywords, so use it directly
# when present instead of relying only on regex signals.
FREELANCE_JOB_TYPES = {"freelance", "contract", "temporary"}
FULLTIME_JOB_TYPES = {"full-time", "part-time"}

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

    for pattern in AGENT_BAIT_SIGNALS:
        if re.search(pattern, text):
            score += AGENT_BAIT_PENALTY
            break  # only apply once even if multiple agent-bait phrases match

    # Structural adjustment based on source type (penalize full-time job boards,
    # boost sources that are already pre-filtered to be gig/bounty work)
    score += SOURCE_SCORE_ADJUSTMENT.get(post.get("source", ""), 0)

    # If the source gives us an explicit job_type field (e.g. Jobicy), trust it
    # over keyword guessing — it's a direct signal, not an inference.
    # Jobicy sometimes returns this as a list (e.g. ["full-time","contract"])
    # rather than a single string, so normalize defensively either way.
    raw_job_type = post.get("job_type") or ""
    if isinstance(raw_job_type, list):
        job_type_values = [str(t).lower() for t in raw_job_type]
    else:
        job_type_values = [str(raw_job_type).lower()]

    if any(jt in FREELANCE_JOB_TYPES for jt in job_type_values):
        score += 6
        matched_positive.append(f"job_type:{job_type_values}")
    elif any(jt in FULLTIME_JOB_TYPES for jt in job_type_values):
        score -= 6

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