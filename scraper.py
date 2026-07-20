"""
scraper.py
Pulls fresh job/gig posts from Reddit, Hacker News, RemoteOK, and WeWorkRemotely.
All sources used here are public/official (no scraping of ToS-restricted sites).
"""

import requests
import feedparser
import time

HEADERS = {"User-Agent": "gig-finder-bot/1.0 (personal use, contact: you@example.com)"}

REDDIT_SUBS = ["forhire", "slavelabour", "webdev", "smallbusiness", "Wordpress"]
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]


def get_reddit_posts(limit=25):
    """Pull newest posts from each target subreddit via Reddit's public JSON endpoint."""
    posts = []
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("data", {}).get("children", []):
                d = item["data"]
                # Only care about [HIRING]/[TASK]/paid-sounding posts, not [FOR HIRE] (people offering, not asking)
                title = d.get("title", "")
                posts.append({
                    "source": f"reddit/r/{sub}",
                    "id": d.get("id"),
                    "title": title,
                    "url": "https://www.reddit.com" + d.get("permalink", ""),
                    "body": d.get("selftext", "")[:1000],
                    "num_comments": d.get("num_comments", 0),
                    "created_utc": d.get("created_utc", 0),
                })
        except Exception as e:
            print(f"[reddit] failed for r/{sub}: {e}")
        time.sleep(1)  # be polite to Reddit's rate limits
    return posts


def get_hn_freelance_posts():
    """
    Search Hacker News (via Algolia's public HN Search API) for the monthly
    'Freelancer? Seeking freelancer?' thread, then pull its top-level comments as job posts.
    """
    posts = []
    try:
        search_url = "https://hn.algolia.com/api/v1/search_by_date"
        params = {"query": "Freelancer? Seeking freelancer?", "tags": "story", "hitsPerPage": 3}
        resp = requests.get(search_url, params=params, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        for hit in hits:
            story_id = hit.get("objectID")
            item_url = f"https://hn.algolia.com/api/v1/items/{story_id}"
            item_resp = requests.get(item_url, timeout=10)
            item_resp.raise_for_status()
            item = item_resp.json()
            for child in item.get("children", [])[:60]:  # top-level comments only
                text = (child.get("text") or "")
                if not text:
                    continue
                posts.append({
                    "source": "hackernews",
                    "id": str(child.get("id")),
                    "title": text[:100].replace("\n", " ") + "...",
                    "url": f"https://news.ycombinator.com/item?id={child.get('id')}",
                    "body": text[:1000],
                    "num_comments": 0,
                    "created_utc": child.get("created_at_i", 0),
                })
    except Exception as e:
        print(f"[hn] failed: {e}")
    return posts


def get_remoteok_posts():
    """RemoteOK exposes a free public JSON API."""
    posts = []
    try:
        resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for d in data:
            if not isinstance(d, dict) or "id" not in d:
                continue  # first item is a metadata blob, skip it
            posts.append({
                "source": "remoteok",
                "id": str(d.get("id")),
                "title": d.get("position", d.get("title", "")),
                "url": d.get("url", ""),
                "body": (d.get("description") or "")[:1000],
                "num_comments": 0,
                "created_utc": 0,
                "tags": d.get("tags", []),
            })
    except Exception as e:
        print(f"[remoteok] failed: {e}")
    return posts


def get_wwr_posts():
    """WeWorkRemotely publishes free RSS feeds per category."""
    posts = []
    for feed_url in WWR_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                posts.append({
                    "source": "weworkremotely",
                    "id": entry.get("id", entry.get("link", "")),
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "body": entry.get("summary", "")[:1000],
                    "num_comments": 0,
                    "created_utc": 0,
                })
        except Exception as e:
            print(f"[wwr] failed for {feed_url}: {e}")
    return posts


def get_all_posts():
    all_posts = []
    all_posts.extend(get_reddit_posts())
    all_posts.extend(get_hn_freelance_posts())
    all_posts.extend(get_remoteok_posts())
    all_posts.extend(get_wwr_posts())
    return all_posts


if __name__ == "__main__":
    posts = get_all_posts()
    print(f"Pulled {len(posts)} total posts")
    for p in posts[:5]:
        print(p["source"], "-", p["title"])
