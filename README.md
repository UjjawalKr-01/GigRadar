# GigRadar

Scrapes Reddit, Hacker News, RemoteOK, and WeWorkRemotely for small, well-scoped,
paid coding gigs, filters out noise, drafts a pitch for each match, and sends
you a digest on Telegram — free, on a schedule, no server needed.

## What it does (recap)
1. `scraper.py` — pulls new posts from Reddit (r/forhire, r/slavelabour, r/webdev,
   r/smallbusiness, r/Wordpress), HN's monthly freelance thread, RemoteOK, and WWR.
2. `filter.py` — scores each post (mentions a budget? scoped task? low competition?)
   and drops vague/equity-only/too-big posts.
3. `pitch.py` — drafts a short opening message for each good match (uses the
   Anthropic API if you provide a key; falls back to a simple template otherwise).
4. `notifier.py` — sends the digest to your phone via Telegram.
5. `main.py` — runs the whole pipeline end to end.
6. `.github/workflows/digest.yml` — runs `main.py` automatically twice a day,
   for free, using GitHub Actions.

## One-time setup (about 10 minutes)

### 1. Get a Telegram bot token (2 min)
1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`, give it a name and username.
3. BotFather gives you a token like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`. Save it.
4. Send your new bot **any message** (e.g. "hi") so it can message you back.
5. Get your chat ID: visit
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   in a browser after messaging the bot — look for `"chat":{"id":123456789,...}`.
   That number is your `TELEGRAM_CHAT_ID`.

### 2. (Optional but recommended) Get an Anthropic API key
For better auto-drafted pitches. Get one at https://console.anthropic.com —
without it, the bot still works, just uses a generic pitch template.

### 3. Put this code in a GitHub repo
1. Create a new (private is fine) repo on GitHub.
2. Push this folder's contents to it.

### 4. Add your secrets to the repo
In your repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ANTHROPIC_API_KEY` (optional)

### 5. Done
The workflow in `.github/workflows/digest.yml` runs automatically at 08:00 and
18:00 UTC every day. You can also trigger it manually anytime from your repo's
**Actions** tab → "GigRadar Digest" → "Run workflow".

## Running it locally instead (optional)
```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export ANTHROPIC_API_KEY="your_key"   # optional
python main.py
```

## Tuning it over time
- **Adjust schedule:** edit the `cron` line in `digest.yml` (uses UTC time).
- **Adjust filter strictness:** in `main.py`, change `min_score` (higher = stricter)
  and `top_n` (how many posts per digest) in the `filter_and_rank(...)` call.
- **Add/remove subreddits:** edit `REDDIT_SUBS` in `scraper.py`.
- **Add more sources later:** each source is its own function in `scraper.py` —
  new ones just need to return the same post dict shape and get added to `get_all_posts()`.

## Notes & limits
- All sources here use public APIs/RSS feeds (no ToS-violating scraping).
- Reddit's public JSON endpoint is rate-limited; the script already adds small
  delays between subreddit calls to stay well under that.
- This surfaces leads — it doesn't send pitches automatically. You still review
  and send each one yourself, which keeps you in control and avoids spammy
  auto-replies that hurt response rates.
