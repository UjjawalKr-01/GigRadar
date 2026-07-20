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


def build_digest_text(posts, stats):
    source_line = ", ".join(f"{src}: {count}" for src, count in stats["by_source"].items())

    header = (
        f"📊 Scan: {stats['total_scraped']} posts pulled ({source_line}) | "
        f"{stats['new_count']} new | {stats['ranked_count']} matched\n"
    )

    if not posts:
        return header + "\nNo new gig matches today. 🌱"

    lines = [header, f"🔎 {len(posts)} new gig match(es) today:\n"]
    for i, p in enumerate(posts, 1):
        lines.append(f"{i}. [{p['source']}] {p['title']}")
        lines.append(f"   Link: {p['url']}")
        lines.append(f"   Suggested pitch:\n   {p['pitch']}\n")
    return "\n".join(lines)


def run():
    seen = load_seen()

    all_posts = get_all_posts()
    print(f"Scraped {len(all_posts)} raw posts")

    # Per-source breakdown so a source going to 0 (e.g. Reddit getting blocked)
    # is visible directly in the Telegram message, not just in Actions logs.
    by_source = {}
    for p in all_posts:
        src = p.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

    # Drop anything we've already notified about
    new_posts = [p for p in all_posts if p.get("id") and p["id"] not in seen]
    print(f"{len(new_posts)} are new")

    ranked = filter_and_rank(new_posts, min_score=2, top_n=8)
    print(f"{len(ranked)} passed the filter")

    for p in ranked:
        p["pitch"] = draft_pitch(p)

    stats = {
        "total_scraped": len(all_posts),
        "by_source": by_source,
        "new_count": len(new_posts),
        "ranked_count": len(ranked),
    }

    digest_text = build_digest_text(ranked, stats)
    delivered = send_telegram(digest_text)

    if delivered:
        # Only mark everything we scraped as seen once we know the digest
        # actually reached you — otherwise a failed send would silently
        # lose real matches (they'd never be shown again).
        all_ids = {p["id"] for p in all_posts if p.get("id")}
        save_seen(seen.union(all_ids))
        print("Digest delivered — state updated.")
    else:
        print("Digest NOT delivered — state left unchanged so nothing is lost. Will retry these posts next run.")

    print("Done.")


if __name__ == "__main__":
    run()
