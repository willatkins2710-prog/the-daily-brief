#!/usr/bin/env python3
"""Refresh a factual, source-linked RSS news index; no AI rewriting or API keys."""
import datetime as dt
import email.utils
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

NOW = dt.datetime.now(dt.timezone.utc)
ROOT = Path(__file__).resolve().parents[1]

def google(query):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "en-GB", "gl": "GB", "ceid": "GB:en"
    })

FEEDS = [
    ("UK News", "UK news", "BBC News", "https://feeds.bbci.co.uk/news/uk/rss.xml"),
    ("UK News", "Politics", "BBC News", "https://feeds.bbci.co.uk/news/politics/rss.xml"),
    ("World", "World", "BBC News", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Business", "Companies & markets", "BBC News", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Economy", "UK & global economy", "Google News", google("UK global economy inflation interest rates growth when:7d")),
    ("Business", "Supermarkets", "Google News", google("UK supermarkets Tesco Sainsbury's Morrisons Asda Aldi Lidl food retail when:7d")),
    ("Business", "Supermarkets", "Google News", google("UK grocery retailers results prices food inflation when:7d")),
    ("AI", "Major developments", "Google News", google("artificial intelligence AI models OpenAI Google Anthropic Microsoft when:7d")),
    ("AI", "Risks & regulation", "Google News", google("artificial intelligence risks AI regulation safety jobs when:7d")),
    ("Sport", "Across sport", "BBC Sport", "https://feeds.bbci.co.uk/sport/rss.xml"),
    ("Sport", "Football", "BBC Sport", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("Sport", "Cricket", "BBC Sport", "https://feeds.bbci.co.uk/sport/cricket/rss.xml"),
    ("Sport", "Golf", "BBC Sport", "https://feeds.bbci.co.uk/sport/golf/rss.xml"),
    ("Sport", "Rugby union", "BBC Sport", "https://feeds.bbci.co.uk/sport/rugby-union/rss.xml"),
    ("Sport", "Rugby league", "BBC Sport", "https://feeds.bbci.co.uk/sport/rugby-league/rss.xml"),
    ("Sport", "Tennis", "BBC Sport", "https://feeds.bbci.co.uk/sport/tennis/rss.xml"),
    ("Sport", "Sports business", "Google News", google("sports business broadcasting rights club finances sports ownership when:7d")),
    ("Money", "Personal finance", "Google News", google("UK personal finance mortgage savings pensions ISA taxes when:7d")),
    ("Health", "Health & wellbeing", "BBC News", "https://feeds.bbci.co.uk/news/health/rss.xml"),
    ("Culture", "Arts & culture", "BBC News", "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml"),
    ("TV & Film", "TV & film", "Google News", google("UK television series film streaming reviews releases when:7d")),
    ("Travel", "Travel", "Google News", google("travel destinations tourism UK Europe long haul when:7d")),
    ("Technology", "Technology", "BBC News", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
]

def tidy(value, length=280):
    value = re.sub(r"<[^>]*>", " ", str(value or ""))
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:length].rstrip()

def find_text(elem, name):
    item = elem.find(name)
    return (item.text or "").strip() if item is not None else ""

def parse_date(raw):
    try:
        d = email.utils.parsedate_to_datetime(raw)
        return (d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)).astimezone(dt.timezone.utc)
    except (ValueError, TypeError, IndexError):
        return None

def download(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "TheDailyBriefPersonalRSSReader/1.0 (+https://github.com/)",
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8"
    })
    with urllib.request.urlopen(req, timeout=16) as response:
        return response.read(2_000_000)

def load_feed(cat, sub, source, url):
    root = ET.fromstring(download(url))
    result = []
    for item in root.findall(".//channel/item")[:35]:
        title = tidy(find_text(item, "title"), 230)
        link = find_text(item, "link")
        if not title or not link.startswith("https://"):
            continue
        publisher = tidy(find_text(item, "source"), 80) or source
        if source == "Google News" and title.endswith(" - " + publisher):
            title = title[:-(len(publisher) + 3)]
        published = parse_date(find_text(item, "pubDate"))
        if not published or published > NOW + dt.timedelta(minutes=20) or published < NOW - dt.timedelta(days=7):
            continue
        desc = tidy(find_text(item, "description"), 260)
        if desc.lower() == title.lower() or len(desc) < 25:
            desc = ""
        result.append({
            "cat": cat, "sub": sub, "title": title, "dek": desc,
            "url": link, "source": publisher,
            "published": published.isoformat().replace("+00:00", "Z")
        })
    return result

def main():
    story_map = {}
    failed = []
    success = 0
    for cat, sub, source, url in FEEDS:
        try:
            stories = load_feed(cat, sub, source, url)
            if stories:
                success += 1
            else:
                failed.append(f"{cat}/{sub}: no recent items")
            for item in stories:
                key = re.sub(r"[^a-z0-9]+", "", item["title"].lower())[:140]
                if key not in story_map or (
                    item["sub"] in ("Supermarkets", "Sports business") and
                    story_map[key]["sub"] not in ("Supermarkets", "Sports business")
                ):
                    story_map[key] = item
            print(f"{cat:12} {sub:23} {len(stories):3} stories")
        except Exception as exc:
            failed.append(f"{cat}/{sub}: {type(exc).__name__}")
            print(f"Warning: {cat}/{sub} feed unavailable: {exc}")
        time.sleep(0.15)
    if success == 0:
        raise SystemExit("No usable news feeds; preserving previous news.json")
    stories = sorted(story_map.values(), key=lambda s: s["published"], reverse=True)
    percat = {}
    selected = []
    for item in stories:
        cat = item["cat"]
        if percat.get(cat, 0) >= 35:
            continue
        selected.append(item)
        percat[cat] = percat.get(cat, 0) + 1
    payload = {
        "generated_at": NOW.isoformat().replace("+00:00", "Z"),
        "feed_count": success,
        "feed_errors": failed,
        "stories": selected[:240]
    }
    (ROOT / "news.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved {len(payload['stories'])} stories from {success} feeds")

if __name__ == "__main__":
    main()
