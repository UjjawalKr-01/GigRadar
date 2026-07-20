"""
main.py
Runs the full pipeline: scrape -> filter/rank -> draft pitches -> compile digest -> send.
Intended to run on a schedule (see .github/workflows/digest.yml) or manually via:
    python main.py
"""

from scraper import get_all_posts
from filter import filter_and_rank
from pitch import draft_pitch
from notifier import send_telegram
from state import load_seen, save_seen


def build_digest_text(posts):
    if not posts:
        return "No new gig matches today. 🌱"

    lines = [f"🔎 {len(posts)} new gig match(es) today:\n"]
    for i, p in enumerate(posts, 1):
        lines.append(f"{i}. [{p['source']}] {p['title']}")
        lines.append(f"   Link: {p['url']}")
        lines.append(f"   Suggested pitch:\n   {p['pitch']}\n")
    return "\n".join(lines)


def run():
    seen = load_seen()

    all_posts = get_all_posts()
    print(f"Scraped {len(all_posts)} raw posts")

    # Drop anything we've already notified about
    new_posts = [p for p in all_posts if p.get("id") and p["id"] not in seen]
    print(f"{len(new_posts)} are new")

    ranked = filter_and_rank(new_posts, min_score=2, top_n=8)
    print(f"{len(ranked)} passed the filter")

    for p in ranked:
        p["pitch"] = draft_pitch(p)

    digest_text = build_digest_text(ranked)
    send_telegram(digest_text)

    # Mark everything we scraped (not just the ranked ones) as seen,
    # so low-scoring posts don't get re-evaluated every run either.
    all_ids = {p["id"] for p in all_posts if p.get("id")}
    save_seen(seen.union(all_ids))

    print("Done.")


if __name__ == "__main__":
    run()
