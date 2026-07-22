"""
scraper.py
Pulls fresh job/gig posts from Hacker News, RemoteOK, WeWorkRemotely, and Jobicy.
All sources used here are public/official (no scraping of ToS-restricted sites).

Note: Reddit was removed as a source. Reddit's legacy script-app API access now
effectively requires a moderation-tool use case to get approved, and their public
JSON endpoint actively blocks cloud/datacenter IPs (which is what GitHub Actions
runners look like to them) — so it wasn't a reliable source going forward.
"""

import requests
import feedparser

HEADERS = {"User-Agent": "gig-finder-bot/1.0 (personal use, contact: you@example.com)"}

WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]


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
        resp.encoding = "utf-8"  # RemoteOK doesn't always set charset correctly in headers,
        # which caused accented characters (e.g. "Cobrança") to get mangled otherwise.
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


def get_jobicy_posts():
    """
    Jobicy has a free public JSON API. Correction: earlier versions of this
    function assumed a `job_types=freelance` filter param existed — it doesn't.
    Jobicy's real params are just count/geo/industry/tag, and it's a general
    remote job board (mostly full-time), not a freelance-specific one. We now
    pull broadly and let filter.py's keyword/currency scoring do the work,
    same as RemoteOK/WWR.
    """
    posts = []
    try:
        url = "https://jobicy.com/api/v2/remote-jobs"
        params = {"count": 50}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        data = resp.json()
        for d in data.get("jobs", []):
            posts.append({
                "source": "jobicy",
                "id": str(d.get("id")),
                "title": d.get("jobTitle", ""),
                "url": d.get("url", ""),
                "body": (d.get("jobExcerpt") or d.get("jobDescription") or "")[:1000],
                "num_comments": 0,
                "created_utc": 0,
                "job_type": d.get("jobType", ""),  # kept for filter.py to inspect
            })
    except Exception as e:
        print(f"[jobicy] failed: {e}")
    return posts


def get_github_bounty_posts():
    """
    GitHub's search API can find issues tagged with a 'bounty' label across all
    public repos — real, cash-tagged coding tasks. Free, reliable, and (unlike
    Reddit) doesn't block requests from cloud/CI IPs.
    """
    posts = []
    try:
        url = "https://api.github.com/search/issues"
        params = {"q": "label:bounty state:open", "sort": "created", "order": "desc", "per_page": 30}
        resp = requests.get(url, params=params, headers={**HEADERS, "Accept": "application/vnd.github+json"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            if "pull_request" in item:
                continue  # GitHub's issue search mixes in PRs; we only want issues
            repo_url = item.get("repository_url", "")
            repo_full_name = repo_url.replace("https://api.github.com/repos/", "")
            posts.append({
                "source": "github_bounty",
                "id": str(item.get("id")),
                "title": item.get("title", ""),
                "url": item.get("html_url", ""),
                "body": (item.get("body") or "")[:1000],
                "num_comments": item.get("comments", 0),
                "created_utc": 0,
                "author": item.get("user", {}).get("login", ""),
                "repo_full_name": repo_full_name,
            })
    except Exception as e:
        print(f"[github_bounty] failed: {e}")
    return posts


def get_all_posts():
    all_posts = []
    all_posts.extend(get_hn_freelance_posts())
    all_posts.extend(get_remoteok_posts())
    all_posts.extend(get_wwr_posts())
    all_posts.extend(get_jobicy_posts())
    all_posts.extend(get_github_bounty_posts())
    return all_posts


if __name__ == "__main__":
    posts = get_all_posts()
    print(f"Pulled {len(posts)} total posts")
    for p in posts[:5]:
        print(p["source"], "-", p["title"])