<div align="center">

# 📡 GigRadar

**Automated gig-finding for freelancers — scrapes, filters, and pitches small paid jobs straight to your phone.**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Telegram](https://img.shields.io/badge/Telegram-Notifications-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)
[![Anthropic Claude](https://img.shields.io/badge/Claude_API-Pitch_Drafting-D97757?style=for-the-badge&logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![GitHub API](https://img.shields.io/badge/GitHub_API-Bounty_Search-181717?style=for-the-badge&logo=github&logoColor=white)](https://docs.github.com/en/rest/search)

</div>

---

## 🧭 What it does

GigRadar runs on a free schedule (via GitHub Actions) and:

1. **Scrapes** new posts from Hacker News's monthly freelance thread, RemoteOK, WeWorkRemotely, Jobicy (freelance-filtered listings), and GitHub issues tagged `bounty`.
2. **Filters & scores** each post — surfacing well-scoped, paid, low-competition gigs and burying vague "build me an app," full-time/internship, or equity-only posts.
3. **Drafts a pitch** for each good match using the Anthropic API (falls back to a simple template if no API key is set).
4. **Sends you a digest** on Telegram, twice a day, so you can review and send the pitches you like.

You stay in control — nothing is sent to a client automatically. GigRadar only surfaces leads and drafts; you decide what goes out.

> **Note:** Reddit was originally a source but was removed. Its public JSON endpoint blocks requests from cloud/CI IPs (which is what GitHub Actions runners look like to it), and getting proper API access now effectively requires a moderation-tool use case — so it wasn't reliable to keep.

---

## 🗂️ Project structure

```
GigRadar/
├── .github/workflows/digest.yml   # Scheduled automation (runs twice daily, free)
├── scraper.py                     # Pulls posts from HN, RemoteOK, WWR, Jobicy, GitHub bounties
├── filter.py                      # Scores & ranks posts
├── pitch.py                       # Drafts opening pitches via Claude
├── notifier.py                    # Sends the digest to Telegram
├── state.py                       # Tracks already-seen posts
├── main.py                        # Orchestrates the full pipeline
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Get a Telegram bot token
1. Message **[@BotFather](https://t.me/BotFather)** on Telegram → `/newbot` → follow the prompts.
2. Send your new bot any message so it can reply to you.
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and grab your `chat_id`.

### 2. (Optional) Get an Anthropic API key
For sharper, more personalized pitches — grab one at [console.anthropic.com](https://console.anthropic.com). Without it, GigRadar still works using a generic pitch template.

### 3. Add secrets to this repo
Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Required |
|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ |
| `TELEGRAM_CHAT_ID` | ✅ |
| `ANTHROPIC_API_KEY` | Optional |

### 4. Run it
The workflow runs automatically at **08:00 and 18:00 UTC** daily. To test immediately: go to the **Actions** tab → **GigRadar Digest** → **Run workflow**.

---

## 🖥️ Run locally (optional)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export ANTHROPIC_API_KEY="your_key"   # optional
python main.py
```

---

## 🔧 Tuning

- **Schedule** — edit the `cron` line in `.github/workflows/digest.yml` (UTC time).
- **Strictness** — adjust `min_score` / `top_n` in the `filter_and_rank(...)` call in `main.py`.
- **Sources** — each source is its own function in `scraper.py`. Adjust the `count`/`per_page` params on `get_jobicy_posts()` or `get_github_bounty_posts()`, or add a new source function and register it in `get_all_posts()`.

---

<div align="center">

Built with ☕ and a bit of automation by **Ujjawal Kumar**

</div>