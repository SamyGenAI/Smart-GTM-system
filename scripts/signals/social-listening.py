"""Social listening: recent posts from the watchlist, ranked (YouTube by date).

--source linkedin  Apify actor, bills per post scraped.
--source x         xAI Grok x_search, one call per run; -q for topic research.
--source reddit    keyless RSS + arctic-shift + shreddit; free, no API key.
--source youtube   yt-dlp; free, no API key. Transcripts + comments, newest first.
                   Gemini reads the caption-less ones when GEMINI_API_KEY is set.
--source web       Brave/Exa/Serper/Parallel if a key is set, else keyless DDG/Startpage.

Prints JSON to stdout. Run from the repo root.
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# Windows consoles default to cp1252 and mangle the JSON the agent reads.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ACTOR_URL = ("https://api.apify.com/v2/acts/supreme_coder~linkedin-post"
             "/run-sync-get-dataset-items")
XAI_URL = "https://api.x.ai/v1/responses"
XAI_MODEL = "grok-4.6"
MAX_HANDLES = 20  # x_search rejects more than this
WATCHLIST = os.path.join("context", "signals", "watchlist.md")
TIMEOUT = 600  # server-side search runs ~2min; actor runs can be slower

# Approximate USD. Keep these aligned with scripts/lib/costs.mjs.
APIFY_POST_USD = 0.005
XAI_CALL_USD = 0.05
GEMINI_VIDEO_USD = 0.01
WEB_QUERY_USD = 0.005
EXA_SEARCH_USD = 0.007


# Print the estimate. Return False when the caller should stop.
# Paid work continues only when --confirm is set and this is not a dry run.
def require_paid(args, payload):
    body = dict(payload)
    calls = dict(body.get("calls") or {})
    body["calls"] = calls
    body["calls_anthropic"] = calls.get("anthropic", 0)
    body["calls_exa"] = calls.get("exa", 0)
    body["calls_rapidapi"] = calls.get("rapidapi", 0)
    body["paid_calls"] = False
    body["confirmed"] = False
    if args.dry_run:
        body["dry_run"] = True
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return False
    if not args.confirm:
        body["dry_run"] = False
        print(json.dumps(body, indent=2, ensure_ascii=False))
        sys.stderr.write(
            "Refusing paid calls without --confirm. Re-run with --dry-run, then --confirm after review.\n")
        raise SystemExit(2)
    return True

X_POST_URL = re.compile(
    r"^https?://(?:www\.)?(?:x|twitter)\.com/[A-Za-z0-9_]{1,15}/(?:status|article)/\d+", re.I)

# An /article/ permalink IS an X article -- the URL is the fact, so it decides,
# not the model's self-reported post_type. Threads have ordinary /status/ URLs
# and can only be taken from the label.
X_ARTICLE_URL = re.compile(
    r"^https?://(?:www\.)?(?:x|twitter)\.com/[A-Za-z0-9_]{1,15}/article/\d+", re.I)


# Long-form ranks above short posts so substance leads over volume.
def x_is_longform(url, post_type):
    return bool(X_ARTICLE_URL.match(url or "")) or (post_type or "").lower() == "thread"

X_CONTRACT = """Return ONLY a JSON object of this exact shape:
{"posts":[{"entity":"watchlist name, or the handle when researching a topic",
"author":"display name","handle":"bare handle, no @","text":"full post text",
"url":"https://x.com/<handle>/status/<id>" or "https://x.com/<handle>/article/<id>","date":"ISO 8601",
"likes":0,"reposts":0,"replies":0,"post_type":"article|thread|post|reply|quote"}]}
Use "article" only for a real X article (an /article/ permalink), and "thread"
for a multi-post thread. Do not label a single short post as either.
likes/reposts/replies must be integers, or null when genuinely unknown.
Empty posts array if nothing relevant. No other keys, no markdown fences."""

X_INSTRUCTIONS = (
    "You are a social listening analyst. Report ONLY posts and articles you "
    "actually found via x_search. Never invent a post, URL, author, or count. "
    "Every post needs its real permalink: https://x.com/<handle>/status/<id> or https://x.com/<handle>/article/<id>  "
    "Report engagement counts as the search returned them; use null when a count "
    "is genuinely unknown, never 0 for unknown. Prefer substantive posts over "
    "pure retweets, one-word replies and giveaways. Favour long-form: include "
    "every relevant X article and multi-post thread you find, even when its "
    "engagement is lower than a short post's. Never invent an article to fill "
    "the quota -- if there are none, return posts. Return the JSON object only."
)


# Loads API keys from .env. Real env vars win.
def load_env():
    if not os.path.exists(".env"):
        return
    with open(".env", encoding="utf-8") as fh:
        for line in fh:
            key, sep, value = line.strip().partition("=")
            if sep and not key.startswith("#") and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip().strip("\"'")


# Reads WHO to watch from one '## <section>' of watchlist.md -> [{name, handle}].
# Lines starting > - * # are notes, skipped: on LinkedIn every entry costs credits.
def read_watchlist(section):
    if not os.path.exists(WATCHLIST):
        raise SystemExit(f"Missing {WATCHLIST}. Copy watchlist-template.md to it.")

    with open(WATCHLIST, encoding="utf-8") as fh:
        content = fh.read().replace("﻿", "")
    match = re.search(rf"^##\s+{re.escape(section)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)",
                      content, re.MULTILINE | re.DOTALL)
    if not match:
        return []

    entries = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ">", "-", "*", "<!--")):
            continue
        name, sep, handle = line.partition(":")
        if not sep or handle.lstrip().startswith("//"):
            name = handle = line  # bare url/handle, no "Name:" prefix
        entries.append({"name": name.strip(), "handle": handle.strip().rstrip("/")})
    return entries


# Prints the result as JSON on stdout -- this is what the agent reads.
def emit(source, signals, extra=None):
    payload = {"source": source, "count": len(signals), "signals": signals}
    payload.update(extra or {})
    print(json.dumps(payload, indent=2, ensure_ascii=False))


# Shared POST helper for both the Apify and xAI calls.
def post_json(url, body, headers):
    request = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              **headers})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


# --- LinkedIn ----------------------------------------------------------------


# Watchlist line -> LinkedIn URL, or None. Rejecting matters: each accepted
# line is billed for up to --per-source posts.
def linkedin_url(handle):
    if handle.startswith(("http://", "https://", "linkedin.com", "www.linkedin.com")):
        url = handle if "//" in handle else "https://" + handle.lstrip("/")
        return url if "linkedin.com/" in url.lower() else None
    if re.fullmatch(r"@?[A-Za-z0-9À-ÿ_.-]{3,100}", handle):
        return "https://www.linkedin.com/in/" + handle.lstrip("@/")
    return None


# Scrapes one profile. This is the step that bills. [] on failure so others run.
# Traps: batching URLs into one run silently drops some while billing for all.
# Setting numLikes/numComments to 0 returns an empty dataset -- omit them.
def call_actor(url, per_source, token):
    try:
        return post_json(f"{ACTOR_URL}?token={token}",
                         {"urls": [url], "limitPerSource": per_source}, {})
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:300]
        if err.code in (401, 403):  # account-wide: every other URL fails too
            raise SystemExit(f"Apify HTTP {err.code}: {detail}\n"
                             f"Check APIFY_API_KEY and your credit balance.")
        sys.stderr.write(f"HTTP {err.code} on {url} :: {detail}\n")
    except urllib.error.URLError as err:
        sys.stderr.write(f"could not reach Apify for {url} :: {err.reason}\n")
    return []


# Post within the -d window? Undated posts are kept.
def in_window(iso, days):
    if not iso:
        return True
    try:
        posted = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    return posted >= datetime.now(timezone.utc) - timedelta(days=days)


# Full LinkedIn run: resolve URLs, scrape each, sort by engagement, print.
def run_linkedin(args, entries):
    for entry in entries:
        entry["url"] = linkedin_url(entry["handle"])
    dropped = [e for e in entries if not e["url"]]
    entries = [e for e in entries if e["url"]]
    for entry in dropped:
        sys.stderr.write(f"skipping (not a LinkedIn target) :: {entry['handle'][:80]}\n")

    if not entries:
        return emit("linkedin", []) or sys.stderr.write(
            f"Nothing usable under '## LinkedIn' in {WATCHLIST}.\n")

    posts = len(entries) * args.per_source
    if not require_paid(args, {
        "source": "linkedin",
        "max_posts_scraped": posts,
        "estimated_usd": round(posts * APIFY_POST_USD, 4),
        "calls": {"anthropic": 0, "exa": 0, "rapidapi": 0, "apify": posts},
        "watching": [{"name": e["name"], "url": e["url"]} for e in entries],
        "note": "Apify bills per post scraped. The dollar figure is an approximation.",
    }):
        return

    if not os.environ.get("APIFY_API_KEY"):
        raise SystemExit("Missing APIFY_API_KEY. Add it to .env in the repo root.")
    token = os.environ["APIFY_API_KEY"]

    signals, seen = [], set()
    for entry in entries:
        items = call_actor(entry["url"], args.per_source, token)
        kept = 0
        for item in items:
            url = item.get("url")
            if not in_window(item.get("postedAtISO"), args.days) or url in seen:
                continue
            seen.add(url)
            reactions = item.get("numLikes") or 0
            comments = item.get("numComments") or 0
            shares = item.get("numShares") or 0
            signals.append({
                "entity": entry["name"],
                "author": item.get("authorName"),
                "author_url": entry["url"],  # actor's own is tracking-laden
                "text": (item.get("text") or "").strip(),
                "url": url,
                "date": item.get("postedAtISO"),
                "reactions": reactions,
                "comments": comments,
                "shares": shares,
                "engagement": reactions + comments + shares,
                "post_type": item.get("type"),
            })
            kept += 1
        # A silent profile is the main failure mode -- unreported, a broken
        # scrape reads as a quiet competitor.
        if not items:
            sys.stderr.write(f"{entry['name']}: no posts returned (unreachable or inactive)\n")
        elif not kept:
            sys.stderr.write(f"{entry['name']}: {len(items)} fetched, none in last {args.days}d\n")
        else:
            sys.stderr.write(f"{entry['name']}: {kept} post(s) in window\n")

    signals.sort(key=lambda s: s["engagement"], reverse=True)
    emit("linkedin", signals[:args.limit])


# --- X -----------------------------------------------------------------------


# Watchlist line -> bare X handle, or None.
def x_handle(raw):
    match = re.search(r"(?:^|//|\.)(?:x|twitter)\.com/@?([A-Za-z0-9_]{1,15})", raw, re.I)
    if match:
        reserved = {"search", "home", "i", "explore", "hashtag", "intent", "share"}
        return None if match.group(1).lower() in reserved else match.group(1)
    if raw.startswith(("http://", "https://")):
        return None  # a URL, but not an X profile
    raw = raw.lstrip("@")
    return raw if re.fullmatch(r"[A-Za-z0-9_]{1,15}", raw) else None


# Metric -> int ("1.2K" -> 1200), or None if unknown. None not 0: 0 would
# claim the post flopped, which is a different claim from not knowing.
def as_count(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) if value >= 0 else None
    if isinstance(value, str):
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([KkMm])?",
                             value.strip().replace(",", "").replace("+", ""))
        if match:
            return int(float(match.group(1))
                       * {"k": 1000, "m": 1000000}.get((match.group(2) or "").lower(), 1))
    return None


# Pulls the model's answer out of xAI's envelope. The output array interleaves
# tool calls with the message, so it can't be read positionally.
def x_text(response):
    if isinstance(response.get("output_text"), str) and response["output_text"].strip():
        return response["output_text"]
    chunks = []
    for item in response.get("output") or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if isinstance(content, str):
            chunks.append(content)
            continue
        for part in content or []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                chunks.append(part["text"])
    return "\n".join(chunks)


# Full X run: build the search, call xAI, validate posts, sort, print.
def run_x(args, entries):
    resolved = []
    for entry in entries:
        handle = x_handle(entry["handle"])
        if handle:
            resolved.append({"name": entry["name"], "handle": handle})
        else:
            sys.stderr.write(f"skipping (not an X handle) :: {entry['handle'][:80]}\n")

    if not resolved and not args.query:
        return emit("x", []) or sys.stderr.write(
            f"Nothing under '## X' in {WATCHLIST}, and no -q given.\n")
    if len(resolved) > MAX_HANDLES:
        sys.stderr.write(f"x_search accepts {MAX_HANDLES} handles; using the first {MAX_HANDLES}.\n")
        resolved = resolved[:MAX_HANDLES]

    if not require_paid(args, {
        "source": "x", "api_calls": 1, "estimated_usd": XAI_CALL_USD,
        "calls": {"anthropic": 0, "exa": 0, "rapidapi": 0, "xai": 1},
        "query": args.query, "watching": resolved,
        "note": "One xAI x_search call per run.",
    }):
        return

    if not os.environ.get("X_API_KEY"):
        raise SystemExit("Missing X_API_KEY. Add it to .env in the repo root.")

    names = ", ".join(f"{e['name']} (@{e['handle']})" for e in resolved)
    if args.query and resolved:
        task = f"Search X for posts about: {args.query}\nRestrict to: {names}"
    elif args.query:
        task = f"Search X for posts about: {args.query}"
    else:
        task = ("Find the most notable recent posts from these watched accounts. "
                "Cover as many as have posted; do not spend the whole result set "
                f"on one account.\nAccounts: {names}")

    today = datetime.now(timezone.utc).date()
    since = today - timedelta(days=args.days)
    prompt = (f"{task}\n\nOnly posts from the last {args.days} days "
              f"(on or after {since.isoformat()}).\n\n"
              "Prioritise X articles and long-form threads: search for them "
              "first and include all you find, then fill the rest with the "
              "highest-engagement regular posts.\n\n"
              f"Return at most {args.limit} items, articles and threads first, "
              f"each group highest-engagement first.\n\n{X_CONTRACT}")

    tool = {"type": "x_search", "from_date": since.isoformat(),
            "to_date": today.isoformat()}
    if resolved:  # omitted in pure query mode so the search spans all of X
        tool["allowed_x_handles"] = [e["handle"] for e in resolved]

    try:
        response = post_json(XAI_URL,
                             {"model": args.model, "instructions": X_INSTRUCTIONS,
                              "input": [{"role": "user", "content": prompt}],
                              "tools": [tool]},
                             {"Authorization": f"Bearer {os.environ['X_API_KEY']}"})
    except urllib.error.HTTPError as err:
        raise SystemExit(f"xAI HTTP {err.code}: {err.read().decode('utf-8','replace')[:300]}\n"
                         f"Check X_API_KEY, credit balance, and model access.")
    except urllib.error.URLError as err:
        raise SystemExit(f"could not reach api.x.ai :: {err.reason}")

    raw = x_text(response).strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise SystemExit(f"model did not return JSON :: {raw[:200]}")
        data = json.loads(raw[start:end + 1])
    posts = data if isinstance(data, list) else data.get("posts") or []

    by_handle = {e["handle"].lower(): e["name"] for e in resolved}
    signals, dropped = [], 0
    for post in posts:
        url = (post.get("url") or "").strip() if isinstance(post, dict) else ""
        # No usable permalink = the model likely invented the post.
        if not X_POST_URL.match(url):
            dropped += 1
            continue
        handle = (post.get("handle") or "").strip().lstrip("@")
        if not handle:
            found = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/(?:status|article)/",
                              url, re.I)
            handle = found.group(1) if found else ""
        likes = as_count(post.get("likes"))
        reposts = as_count(post.get("reposts"))
        replies = as_count(post.get("replies"))
        known = [v for v in (likes, reposts, replies) if v is not None]
        signals.append({
            "entity": by_handle.get(handle.lower()) or post.get("entity") or handle,
            "author": post.get("author"),
            "handle": handle,
            "author_url": f"https://x.com/{handle}" if handle else None,
            "text": (post.get("text") or "").strip(),
            "url": url,
            "date": post.get("date"),
            "likes": likes,
            "reposts": reposts,
            "replies": replies,
            "engagement": sum(known) if known else None,
            # The URL wins over the model's label: an /article/ permalink is an
            # article whatever it called itself.
            "post_type": ("article" if X_ARTICLE_URL.match(url)
                          else post.get("post_type")),
        })
    if dropped:
        sys.stderr.write(f"dropped {dropped} record(s) with no valid permalink.\n")
    articles = sum(1 for s in signals if X_ARTICLE_URL.match(s["url"]))
    longform = sum(1 for s in signals if x_is_longform(s["url"], s["post_type"]))
    sys.stderr.write(f"{len(signals)} item(s) returned "
                     f"({articles} article, {longform - articles} thread, "
                     f"{len(signals) - longform} post).\n")

    # Re-sorted rather than trusting the model's ordering. Long-form first, then
    # engagement within each group. Unknown engagement sorts last.
    signals.sort(key=lambda s: (x_is_longform(s["url"], s["post_type"]),
                                s["engagement"] is not None, s["engagement"] or 0),
                 reverse=True)
    emit("x", signals[:args.limit])


# --- Reddit -------------------------------------------------------------------
#
# Keyless and free, three public endpoints stitched together:
#   1. RSS       reddit.com/.../*.rss      -> discovery (titles + urls, no score)
#   2. listing   reddit.com/svc/shreddit/  -> discovery WITH live scores
#   3. arctic    arctic-shift.photon-...   -> archived counts by id (fallback)
#   4. shreddit  reddit.com/svc/shreddit/  -> top comments
# Reddit's .json API now answers 403 to anything without a key; these four
# still answer 200, so the whole source costs nothing.
#
# (2) complements (1) rather than replacing it: the listing partial server-
# renders each post's score but takes no query, while RSS searches but carries
# no engagement. Watchlist runs get both; query runs still lean on RSS search.
# Neither can be dropped -- if Reddit changes the listing markup, the source
# degrades to the original RSS+arctic path instead of going dark.

ATOM = "{http://www.w3.org/2005/Atom}"
ARCTIC_URL = "https://arctic-shift.photon-reddit.com/api/posts/ids"
SHREDDIT_URL = "https://www.reddit.com/svc/shreddit/comments/r/{sub}/t3_{post_id}?sort=top"
# The subreddit listing partial. Unlike the comments partial it renders whole
# post cards, each <shreddit-post> start tag carrying a live score.
LISTING_URL = "https://www.reddit.com/svc/shreddit/community-more-posts/{sort}/?name={sub}"
# "new" is the gap RSS+arctic leaves: a thread posted hours ago is absent from
# top/hot and too fresh for the arctic archive, so it scores as unknown today.
LISTING_SORTS = ("top", "hot", "new")
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
REDDIT_TIMEOUT = 20
# Reddit 429s a burst of feed requests, and a throttled run silently collapses to
# whichever feed happened to land -- one subreddit posing as the whole watchlist.
REDDIT_PACE = 2.0       # seconds between reddit.com requests
REDDIT_RETRIES = 2      # a 429 is transient; back off and try again
ARCTIC_BATCH = 50       # ids per lookup; arctic 422s ("slow down") if hammered
MAX_COMMENTS = 8        # top comments kept per enriched post
# A post matching one word of a four-word query is not on topic -- "hiring a
# ghostwriter for linkedin" must not surface a LinkedIn hiring thread with no
# ghostwriting in it. But a fixed fraction breaks both ways: at 0.5 a
# three-term query cut all 29 results, because no title pairs "ghostwriting"
# with "pricing". So the bar is a term count, not a ratio -- one term for a
# one-word query, two for anything longer, which is strict enough to stop the
# hijack and loose enough to return a run.
def relevance_floor(query):
    terms = query_terms(query)
    return (min(2, len(terms)) / len(terms)) if terms else 0.0

# The listing feeds carry no query, so a subreddit's viral off-topic post would
# otherwise outrank every on-topic one. Stopwords are dropped so "the"/"a" can't
# manufacture overlap.
STOPWORDS = {"the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "is",
             "it", "with", "my", "how", "what", "why", "do", "does", "i", "you",
             "we", "this", "that", "at", "by", "from", "are", "be", "as", "not"}

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_PARA = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL)
# The exact <shreddit-comment> start tag -- the lookahead stops it matching
# <shreddit-comment-tree> and friends.
_COMMENT_TAG = re.compile(r"<shreddit-comment(?=[\s>])[^>]*>")
_NEXT_BODY = re.compile(r'id="t1_[A-Za-z0-9]+-(?:comment|post)-rtjson-content"')
_POST_REF = re.compile(r"/r/([^/]+)/comments/([A-Za-z0-9]+)")
# The exact <shreddit-post> start tag; the lookahead keeps it off
# <shreddit-post-overflow-menu> and friends, same trick as _COMMENT_TAG.
_POST_CARD = re.compile(r"<shreddit-post(?=[\s>])[^>]*>")


# Bare GET returning text. Reddit 403s the default urllib agent, so every
# request here wears a browser UA, and 429s bursts, so calls are paced and
# retried. None on any failure -- one dead feed must never sink the run.
_last_request = [0.0]


def http_text(url, accept="*/*"):
    for attempt in range(REDDIT_RETRIES + 1):
        gap = REDDIT_PACE - (time.monotonic() - _last_request[0])
        if gap > 0:
            time.sleep(gap)
        _last_request[0] = time.monotonic()
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": BROWSER_UA, "Accept": accept})
            with urllib.request.urlopen(request, timeout=REDDIT_TIMEOUT) as response:
                return response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < REDDIT_RETRIES:
                time.sleep(REDDIT_PACE * (attempt + 2))  # back off, then retry
                continue
            sys.stderr.write(f"reddit fetch failed :: HTTP {err.code} :: {url[:100]}\n")
            return None
        except Exception as err:  # timeout, DNS, malformed response
            sys.stderr.write(f"reddit fetch failed :: {url[:100]} :: {err}\n")
            return None
    return None


# The query's meaningful words -- stopwords and one/two-letter noise dropped.
def query_terms(query):
    return {w for w in re.findall(r"[a-z0-9]+", (query or "").lower())
            if w not in STOPWORDS and len(w) > 2}


# Fraction of the query's meaningful words present in the title/body. Cheap,
# but enough to keep an off-topic viral post out of the brief.
def relevance(query, text):
    terms = query_terms(query)
    if not terms:
        return 1.0  # no query = watchlist mode, nothing to be irrelevant to
    words = set(re.findall(r"[a-z0-9]+", (text or "").lower()))
    return sum(1 for t in terms if t in words) / len(terms)


# The feeds RSS discovery fans out across: global search, per-sub search, and
# per-sub top/hot listings for volume.
def reddit_feeds(query, subs, days):
    window = "week" if days <= 7 else "month"
    quoted = urllib.parse.quote_plus(query) if query else ""
    urls = []
    if query:
        urls.append(f"https://www.reddit.com/search.rss?q={quoted}&sort=relevance&t={window}")
    for sub in subs:
        if query:
            urls.append(f"https://www.reddit.com/r/{sub}/search.rss"
                        f"?q={quoted}&restrict_sr=on&sort=relevance&t={window}")
        for sort in ("top", "hot"):
            urls.append(f"https://www.reddit.com/r/{sub}/{sort}.rss?t={window}")
    return urls


# Atom feed -> post dicts. RSS carries no engagement, so upvotes/comments are
# backfilled from arctic-shift later.
def parse_feed(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as err:
        sys.stderr.write(f"reddit feed parse error :: {err}\n")
        return []

    posts = []
    for entry in root.iter(f"{ATOM}entry"):
        def text_of(path):
            node = entry.find(path)
            return (node.text or "").strip() if node is not None else ""

        link = entry.find(f"{ATOM}link")
        url = (link.get("href") or "").strip() if link is not None else ""
        if "/comments/" not in url:
            continue

        author = text_of(f"{ATOM}author/{ATOM}name").lstrip("/").removeprefix("u/")
        category = entry.find(f"{ATOM}category")
        sub = category.get("term", "").strip() if category is not None else ""
        if not sub and "/r/" in url:
            sub = url.split("/r/", 1)[1].split("/", 1)[0]

        body = _WS.sub(" ", _TAG.sub(" ", text_of(f"{ATOM}content"))).strip()[:600]

        posts.append({
            "entity": f"r/{sub}",
            "author": author if author not in ("", "[deleted]") else "[deleted]",
            "title": text_of(f"{ATOM}title"),
            "text": html.unescape(body),
            "url": url,
            "date": text_of(f"{ATOM}updated") or None,
            "subreddit": sub,
        })
    return posts


# One <shreddit-post> start tag -> a post dict shaped like parse_feed's, so the
# two discovery sources can be merged without special-casing either. The card
# carries no body text (RSS does), but it does carry the live score.
def parse_listing(page, sub):
    posts = []
    for found in _POST_CARD.finditer(page or ""):
        tag = found.group(0)

        def attr(name):
            hit = re.search(rf'\b{name}="([^"]*)"', tag)
            return html.unescape(hit.group(1)) if hit else ""

        permalink = attr("permalink")
        if "/comments/" not in permalink:
            continue
        try:
            upvotes = int(attr("score") or 0)
        except ValueError:
            upvotes = 0
        try:
            comments = int(attr("comment-count") or 0)
        except ValueError:
            comments = 0

        author = attr("author") or "[deleted]"
        posts.append({
            "entity": f"r/{attr('subreddit-name') or sub}",
            "author": author if author not in ("[deleted]", "[removed]") else "[deleted]",
            "title": attr("post-title"),
            "text": "",
            "url": f"https://www.reddit.com{permalink}",
            "date": attr("created-timestamp") or None,
            "subreddit": attr("subreddit-name") or sub,
            # Live, unlike arctic's archive snapshot -- flagged so the merge
            # knows this number outranks anything arctic returns for the id.
            "live_upvotes": upvotes,
            "live_comments": comments,
        })
    return posts


# Scored discovery across the watchlist subs. One request per sub x sort, paced
# by http_text like every other reddit.com call -- the 429 that pacing exists to
# avoid would cost more than the parallelism would save.
def listing_posts(subs, sorts=LISTING_SORTS, days=7):
    window = "week" if days <= 7 else "month"
    posts = []
    for sub in subs:
        for sort in sorts:
            url = LISTING_URL.format(sort=sort, sub=sub)
            if sort == "top":
                url += f"&t={window}"
            found = parse_listing(http_text(url, accept="text/html") or "", sub)
            if not found:
                sys.stderr.write(f"no listing cards :: r/{sub} {sort}\n")
            posts.extend(found)
    return posts


# Point-in-time upvote/comment counts for a batch of base36 post ids. Arctic is
# a public archive, so counts lag live by a little -- fine for ranking.
def arctic_scores(post_ids):
    scores = {}
    for start in range(0, len(post_ids), ARCTIC_BATCH):
        batch = post_ids[start:start + ARCTIC_BATCH]
        raw = http_text(f"{ARCTIC_URL}?ids={','.join(batch)}")
        if not raw:
            break  # rate-limited or unreachable; keep what we already have
        try:
            rows = json.loads(raw).get("data")
        except (json.JSONDecodeError, AttributeError):
            break
        if not isinstance(rows, list):
            sys.stderr.write("arctic-shift returned no data (rate-limited?)\n")
            break
        for row in rows:
            if not isinstance(row, dict):
                continue
            post_id = str(row.get("id") or "").removeprefix("t3_")
            if post_id:
                scores[post_id] = {"upvotes": int(row.get("score") or 0),
                                   "comments": int(row.get("num_comments") or 0)}
    return scores


# One comment's body, anchored on its own thingId so a nested reply is never
# attributed to its parent. The slice stops at the next comment's anchor.
def comment_body(page, thing_id):
    anchor = f'id="{thing_id}-post-rtjson-content"'
    start = page.find(anchor)
    if start == -1:
        return ""
    window = page[start + len(anchor):start + len(anchor) + 8000]
    following = _NEXT_BODY.search(window)
    if following:
        window = window[:following.start()]
    text = " ".join(_TAG.sub("", p) for p in _PARA.findall(window))
    return _WS.sub(" ", html.unescape(text)).strip()


# Top comments for one thread, from the shreddit partial. [] on any failure.
def fetch_comments(url):
    match = _POST_REF.search(url)
    if not match:
        return []
    page = http_text(SHREDDIT_URL.format(sub=match.group(1), post_id=match.group(2)),
                     accept="text/html")
    if not page:
        return []

    comments = []
    for found in _COMMENT_TAG.finditer(page):
        tag = found.group(0)

        def attr(name):
            hit = re.search(rf'\b{name}="([^"]*)"', tag)
            return html.unescape(hit.group(1)) if hit else ""

        author = attr("author") or "[deleted]"
        body = comment_body(page, attr("thingId"))
        if author in ("[deleted]", "[removed]") or not body:
            continue
        try:
            score = int(attr("score") or 0)
        except ValueError:
            score = 0
        permalink = attr("permalink")
        comments.append({"author": author, "score": score, "text": body[:300],
                         "url": f"https://reddit.com{permalink}" if permalink else url})

    comments.sort(key=lambda comment: comment["score"], reverse=True)
    return comments[:MAX_COMMENTS]


# Full Reddit run: RSS discovery -> arctic scores -> relevance floor -> top
# comments on the leaders.
def run_reddit(args, entries):
    subs = []
    for entry in entries:
        sub = entry["handle"].strip().lstrip("/").removeprefix("r/").rstrip("/")
        if re.fullmatch(r"[A-Za-z0-9_]{2,21}", sub):
            subs.append(sub)
        else:
            sys.stderr.write(f"skipping (not a subreddit) :: {entry['handle'][:80]}\n")

    if not subs and not args.query:
        return emit("reddit", []) or sys.stderr.write(
            f"Nothing under '## Reddit' in {WATCHLIST}, and no -q given.\n")

    feeds = reddit_feeds(args.query, subs, args.days)
    if args.dry_run:
        return print(json.dumps({"source": "reddit", "dry_run": True, "cost": "free",
                                 "estimated_usd": 0,
                                 "calls": {"anthropic": 0, "exa": 0, "rapidapi": 0},
                                 "feeds": len(feeds),
                                 "listing_requests": len(subs) * len(LISTING_SORTS),
                                 "query": args.query,
                                 "watching": [f"r/{s}" for s in subs]},
                                indent=2, ensure_ascii=False))

    posts, seen = [], set()
    for feed in feeds:
        # Reddit already ranked search.rss hits against the query; the local
        # relevance floor below is for the listing feeds, which carry no query.
        from_search = "search.rss" in feed
        for post in parse_feed(http_text(feed, accept="application/atom+xml") or ""):
            if post["url"] in seen or not in_window(post["date"], args.days):
                continue
            seen.add(post["url"])
            post["from_search"] = from_search
            posts.append(post)
    # Scored discovery, merged into the RSS pool. On a URL collision the RSS
    # post wins the body text (listings carry none) but inherits the live
    # score, so neither source loses what only it has.
    by_url = {p["url"]: p for p in posts}
    listing_new = 0
    for found in listing_posts(subs, days=args.days):
        if not in_window(found["date"], args.days):
            continue
        existing = by_url.get(found["url"])
        if existing:
            existing["live_upvotes"] = found["live_upvotes"]
            existing["live_comments"] = found["live_comments"]
        else:
            by_url[found["url"]] = found
            posts.append(found)
            listing_new += 1
    scored_now = sum(1 for p in posts if p.get("live_upvotes") is not None)
    sys.stderr.write(f"listings added {listing_new} post(s) not in RSS; "
                     f"{scored_now} post(s) carry a live score\n")

    live = {p["subreddit"].lower() for p in posts}
    sys.stderr.write(f"{len(posts)} post(s) discovered across {len(feeds)} feed(s), "
                     f"{len(live)} subreddit(s)\n")
    # A subreddit that was asked for but returned nothing was throttled or is
    # unreachable -- never report that silence as a quiet week.
    missing = sorted({s.lower() for s in subs} - live)
    if missing:
        sys.stderr.write(f"no posts from {', '.join('r/' + s for s in missing)} "
                         f"(rate-limited or unreachable, not necessarily quiet)\n")
    if not posts:
        return emit("reddit", [])

    # A viral off-topic post would otherwise hijack the brief, so anything
    # sharing too few words with the query is cut before ranking.
    if args.query:
        for post in posts:
            post["relevance"] = round(
                relevance(args.query, f"{post['title']} {post['text']}"), 2)
        floor = relevance_floor(args.query)
        # Search hits pass on Reddit's ranking -- re-filtering them locally
        # discards good results whose wording differs from the query
        # ("AI agents..." for -q "AI trends"). Only unsearched posts are cut.
        kept = [p for p in posts
                if p.get("from_search") or p["relevance"] >= floor]
        sys.stderr.write(f"{len(posts) - len(kept)} of {len(posts)} post(s) cut "
                         f"below relevance floor {round(floor, 2)}\n")
        if not kept:
            # "Nothing found" and "found things, none on topic" are different
            # answers; the caller must be able to tell them apart and retry
            # with a looser query rather than report a quiet week.
            best = max((p["relevance"] for p in posts), default=0.0)
            sys.stderr.write(f"nothing cleared the floor (best was {best}); "
                             f"try a shorter or broader -q\n")
            return emit("reddit", [], {"filtered_out": len(posts),
                                       "best_relevance": best})
        posts = kept

    ids = [_POST_REF.search(p["url"]).group(2) for p in posts]
    # Arctic is only asked about posts the listing could not score -- it stays
    # the fallback for RSS-only finds (and for every post if the listing markup
    # ever changes), but it no longer overwrites a live number with a stale one.
    unscored = [pid for post, pid in zip(posts, ids)
                if post.get("live_upvotes") is None]
    scores = arctic_scores(unscored) if unscored else {}
    if unscored and not scores:
        sys.stderr.write("no scores from arctic-shift; "
                         "unscored posts ordered by recency\n")
    for post, post_id in zip(posts, ids):
        if post.get("live_upvotes") is not None:
            post["upvotes"] = post["live_upvotes"]
            post["comments"] = post["live_comments"]
            post["score_source"] = "listing (live)"
        else:
            found = scores.get(post_id)
            # None, not 0: an unscored post is unknown, not a flop.
            post["upvotes"] = found["upvotes"] if found else None
            post["comments"] = found["comments"] if found else None
            post["score_source"] = "arctic (archived)" if found else None
        post.pop("live_upvotes", None)
        post.pop("live_comments", None)
        post.pop("from_search", None)
        post["engagement"] = ((post["upvotes"] or 0) + (post["comments"] or 0)
                              if post["upvotes"] is not None else None)

    posts.sort(key=lambda p: (p["engagement"] is not None, p["engagement"] or 0,
                              p["date"] or ""), reverse=True)
    posts = posts[:args.limit]

    # Comments cost one request each, so only the leaders get them.
    for post in posts[:args.enrich]:
        post["top_comments"] = fetch_comments(post["url"])
        # Arctic scores are archive snapshots taken near posting time; comment
        # scores are live. On a thread that took off after archiving, the post
        # reads as under-scored -- a top comment can outscore its own post 2:1,
        # which makes the ranking look broken. The post is worth at least its
        # best comment, so raise the floor and say the number is a minimum.
        # A listing score is already live, so it needs no such correction --
        # applying one there would relabel a true number as a lagging estimate.
        top = max((c["score"] for c in post["top_comments"]), default=0)
        if (post["score_source"] == "arctic (archived)"
                and post["upvotes"] is not None and top > post["upvotes"]):
            post["upvotes_stale"] = post["upvotes"]
            post["upvotes"] = top
            post["engagement"] = top + (post["comments"] or 0)
            post["score_note"] = "minimum: archive snapshot lagged live comments"
    # Corrected scores can reorder the leaders, so sort again before emitting.
    posts.sort(key=lambda p: (p["engagement"] is not None, p["engagement"] or 0,
                              p["date"] or ""), reverse=True)
    sys.stderr.write(f"enriched {min(args.enrich, len(posts))} post(s) with comments\n")

    emit("reddit", posts)


# --- YouTube ------------------------------------------------------------------
#
# Keyless and free, one dependency: yt-dlp. Nothing here bills.
#
# Ranking is by DATE, not views. On the other sources engagement is the sort
# key; here a two-year-old video with 500k views is not a signal and this week's
# 400-view upload from a competitor is. Views are still reported, and only break
# ties between videos sharing a publish date.
#
# Three yt-dlp shapes, because no single one returns everything:
#   1. discovery  ytsearchN: / <channel>/videos  -> ids (flat: fast, but DATELESS)
#   2. hydrate    --dump-json on the ids         -> real dates + counts, batched
#   3. enrich     --write-auto-subs / --write-comments -> transcript + comments
# Flat discovery is the only affordable way to scan a channel, and it carries no
# upload date at all, so (2) is not an optimisation -- without it every video
# would sort as undated and the date ranking would be a lie.

YT_SEARCH_URL = "ytsearch{n}:{query}"
YT_WATCH_URL = "https://www.youtube.com/watch?v={vid}"
# yt-dlp is slow by nature (each call negotiates with YouTube), and these are
# generous rather than tight: a killed call loses the whole batch it was fetching.
YT_DISCOVER_TIMEOUT = 180
YT_HYDRATE_TIMEOUT = 300
YT_TRANSCRIPT_TIMEOUT = 120
YT_COMMENTS_TIMEOUT = 180
YT_HYDRATE_BATCH = 12    # ids per --dump-json call
MAX_YT_COMMENTS = 8      # top comments kept per enriched video
TRANSCRIPT_MAX_WORDS = 4000
# Asking for several languages in one call makes yt-dlp fetch them serially and
# YouTube 429s the extras -- observed live: `en` landed, `fr` came back 429 and
# the call exited non-zero with a perfectly good transcript already on disk.
# So a non-zero exit is never trusted over the file that is actually on disk.
YT_SUB_LANGS = "en.*,fr.*"

# Gemini fallback for the caption-less case, which is most of them: YouTube
# auto-captions only some uploads, and a video with no transcript is a video we
# cannot read. Gemini 2.5 ingests the YouTube URL directly and reports what was
# actually said, so `transcript_unavailable` stops meaning "unreadable".
# Only for videos yt-dlp came back empty on -- never a replacement for real
# captions, which are free, exact and unlimited.
GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              "{model}:generateContent")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT = 300      # video ingestion is slow; a short timeout wastes the call
GEMINI_MAX_FALLBACKS = 5  # per run, so one uncaptioned channel cannot drain the quota
# What comes back must be a transcript-equivalent, not a review: everything
# downstream reads this field exactly as it reads captions.
GEMINI_PROMPT = (
    "Transcribe and condense what is actually said in this video, for social "
    "listening research. Return plain prose only -- no preamble, no markdown, "
    "no timestamps. Open with a three-sentence summary of the core message, "
    "then give a dense account of the substance in the speaker's own terms, "
    "including the claims, numbers, product names and opinions stated. Report "
    "in English even when the video is not. Never state anything the video "
    "does not."
)

# Live/upcoming streams have no real publish date and no transcript; they are
# not signals yet.
YT_SKIP_LIVE = ("is_live", "is_upcoming")

_VTT_TIMING = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->.*$", re.MULTILINE)
_VTT_INLINE = re.compile(r"<[^>]+>")
_VTT_CUEHEAD = re.compile(r"^(WEBVTT|Kind:|Language:|NOTE\b).*$", re.MULTILINE)
_YT_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


# yt-dlp may be a real binary or only a python module; both are used the same way.
def ytdlp_base():
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--version"],
                       capture_output=True, timeout=60, check=True)
        return [sys.executable, "-m", "yt_dlp"]
    except Exception:
        return None


# Runs yt-dlp and returns (stdout, ok). Never raises: one dead video must not
# sink the run. ok is False only when the process itself failed -- callers that
# can salvage a partial result ignore it (see the 429 note above).
def run_ytdlp(args, timeout):
    base = ytdlp_base()
    if not base:
        return "", False
    try:
        done = subprocess.run(base + ["--ignore-config", "--no-warnings"] + args,
                              capture_output=True, timeout=timeout,
                              encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"yt-dlp timed out after {timeout}s\n")
        return "", False
    except Exception as err:
        sys.stderr.write(f"yt-dlp failed :: {err}\n")
        return "", False
    if done.returncode != 0:
        tail = (done.stderr or "").strip().splitlines()
        if tail:
            sys.stderr.write(f"yt-dlp :: {tail[-1][:180]}\n")
    return done.stdout or "", done.returncode == 0


# JSON-per-line stdout -> dicts, skipping the noise yt-dlp interleaves.
def parse_json_lines(raw):
    rows = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


# Watchlist line -> a /videos URL, or None. Accepts @handle, channel URL, or a
# bare handle.
def youtube_target(handle):
    raw = handle.strip().rstrip("/")
    if raw.startswith(("http://", "https://", "youtube.com", "www.youtube.com")):
        url = raw if "//" in raw else "https://" + raw.lstrip("/")
        if "youtube.com/" not in url.lower() and "youtu.be/" not in url.lower():
            return None
        # A bare channel URL defaults to the Home tab, which is a curated
        # shelf, not a feed -- ask for /videos explicitly so we get uploads.
        if re.search(r"/(videos|shorts|streams|playlists)$", url, re.I):
            return url
        if re.search(r"youtube\.com/(@[^/]+|c/[^/]+|channel/[^/]+|user/[^/]+)$", url, re.I):
            return url + "/videos"
        return url
    if re.fullmatch(r"@?[A-Za-z0-9_.-]{3,100}", raw):
        return f"https://www.youtube.com/@{raw.lstrip('@')}/videos"
    return None


# yt-dlp's `timestamp` is exact when present; upload_date is date-only, so it is
# the fallback rather than the first choice.
def youtube_date(video):
    stamp = video.get("timestamp")
    if isinstance(stamp, (int, float)) and stamp > 0:
        return datetime.fromtimestamp(stamp, timezone.utc).isoformat()
    raw = str(video.get("upload_date") or "")
    if re.fullmatch(r"\d{8}", raw):
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}T00:00:00+00:00"
    return None


# VTT -> plain text. Auto-captions repeat each line twice (once with per-word
# timing tags, once plain) and roll the previous line into the next cue, so
# naive stripping yields every sentence two or three times over.
def clean_vtt(vtt):
    text = _VTT_CUEHEAD.sub("", vtt or "")
    text = _VTT_TIMING.sub("\n", text)
    text = _VTT_INLINE.sub("", text)
    lines = []
    for line in text.splitlines():
        line = _WS.sub(" ", html.unescape(line)).strip()
        # Consecutive duplicates are the caption roll-up, not repetition in the
        # speech; a global set would wrongly cut a genuinely repeated phrase.
        if not line or (lines and lines[-1] == line):
            continue
        lines.append(line)
    out = _WS.sub(" ", " ".join(lines)).strip()
    words = out.split()
    if len(words) > TRANSCRIPT_MAX_WORDS:
        out = " ".join(words[:TRANSCRIPT_MAX_WORDS]) + " ..."
    return out


# One video's transcript, or None. Auto-generated captions count: the point is
# what was said, not whether the uploader typed it out.
def fetch_transcript(vid):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "%(id)s")
        # A non-zero exit here usually means "a later language 429'd", so the
        # file on disk decides, not the return code.
        run_ytdlp(["--skip-download", "--write-auto-subs", "--write-subs",
                   "--sub-lang", YT_SUB_LANGS, "--sub-format", "vtt",
                   "-o", out, YT_WATCH_URL.format(vid=vid)],
                  YT_TRANSCRIPT_TIMEOUT)
        try:
            found = sorted(f for f in os.listdir(tmp) if f.endswith(".vtt"))
        except OSError:
            return None
        if not found:
            return None
        # Prefer a real uploaded track (".en.vtt") over the auto one
        # (".en-orig.vtt") when both landed -- same content, cleaner text.
        found.sort(key=lambda f: ("-orig" in f, f))
        try:
            with open(os.path.join(tmp, found[0]), encoding="utf-8",
                      errors="replace") as fh:
                return clean_vtt(fh.read()) or None
        except OSError:
            return None


# Gemini watches the video when YouTube has no captions to give. Returns the
# transcript-equivalent text, or None -- a failure here is not fatal, the video
# just stays as unreadable as it already was.
def gemini_transcript(vid):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    body = {"contents": [{"parts": [
        {"text": GEMINI_PROMPT},
        {"file_data": {"file_uri": YT_WATCH_URL.format(vid=vid)}},
    ]}]}
    request = urllib.request.Request(
        GEMINI_URL.format(model=GEMINI_MODEL),
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        with urllib.request.urlopen(request, timeout=GEMINI_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        # 429 is the quota, 400 usually a private, age-gated or oversized video.
        detail = (err.read().decode("utf-8", "replace") or "")[:200]
        sys.stderr.write(f"gemini {err.code} on {vid} :: {detail}\n")
        return None
    except Exception as err:
        sys.stderr.write(f"gemini failed on {vid} :: {err}\n")
        return None

    parts = []
    for candidate in payload.get("candidates") or []:
        for part in (candidate.get("content") or {}).get("parts") or []:
            if isinstance(part.get("text"), str):
                parts.append(part["text"])
    text = _WS.sub(" ", " ".join(parts)).strip()
    if not text:
        return None
    words = text.split()
    if len(words) > TRANSCRIPT_MAX_WORDS:
        text = " ".join(words[:TRANSCRIPT_MAX_WORDS]) + " ..."
    return text


# Top comments for one video. Where the buying pain gets stated plainly, same as
# Reddit -- so this is enrichment worth its runtime, not a nice-to-have.
def fetch_youtube_comments(vid):
    # Four values, and the second (per-thread replies) must be non-zero or
    # yt-dlp returns nothing at all -- a 0 there silently empties the result.
    limit = MAX_YT_COMMENTS * 2
    raw, _ = run_ytdlp(
        ["--skip-download", "--write-comments",
         "--extractor-args",
         f"youtube:comment_sort=top;max_comments={limit},{limit},0,0",
         "--dump-single-json", YT_WATCH_URL.format(vid=vid)],
        YT_COMMENTS_TIMEOUT)
    start = (raw or "").find("{")
    if start == -1:
        return []
    try:
        payload = json.loads(raw[start:])
    except json.JSONDecodeError:
        return []

    comments = []
    for item in payload.get("comments") or []:
        if not isinstance(item, dict):
            continue
        body = _WS.sub(" ", (item.get("text") or "")).strip()
        author = (item.get("author") or "").lstrip("@")
        if not body or not author:
            continue
        comments.append({
            "author": author,
            "score": item.get("like_count") if isinstance(
                item.get("like_count"), int) else 0,
            "text": body[:300],
            "url": YT_WATCH_URL.format(vid=vid),
            "is_reply": item.get("parent") not in (None, "root"),
        })
    # Top-level comments before replies, then by likes.
    comments.sort(key=lambda c: (not c["is_reply"], c["score"]), reverse=True)
    return comments[:MAX_YT_COMMENTS]


# ids -> full metadata, batched. Flat discovery has no dates, so this is what
# makes date ranking possible at all.
def hydrate_videos(video_ids):
    hydrated = {}
    for start in range(0, len(video_ids), YT_HYDRATE_BATCH):
        batch = video_ids[start:start + YT_HYDRATE_BATCH]
        raw, _ = run_ytdlp(
            ["--no-download", "--dump-json"]
            + [YT_WATCH_URL.format(vid=v) for v in batch],
            YT_HYDRATE_TIMEOUT)
        for video in parse_json_lines(raw):
            vid = video.get("id")
            if vid:
                hydrated[vid] = video
        missing = [v for v in batch if v not in hydrated]
        if missing:
            # Private, deleted, region-locked or age-gated. Named, because a
            # silently shrinking result set reads as a quiet channel.
            sys.stderr.write(f"youtube: {len(missing)} video(s) unavailable "
                             f"({', '.join(missing[:3])})\n")
    return hydrated


# Discovery: ids only, cheap. Search and channel modes differ only in the URL.
def discover_videos(target, cap, label):
    raw, ok = run_ytdlp(["--no-download", "--flat-playlist", "--dump-json",
                         "--playlist-end", str(cap), target],
                        YT_DISCOVER_TIMEOUT)
    found = []
    for row in parse_json_lines(raw):
        vid = row.get("id") or ""
        if _YT_VIDEO_ID.fullmatch(vid):
            found.append(vid)
    if not found and not ok:
        sys.stderr.write(f"{label}: discovery failed (unreachable or renamed)\n")
    elif not found:
        sys.stderr.write(f"{label}: no videos returned\n")
    return found


# Full YouTube run: discover -> hydrate for real dates -> window -> relevance ->
# newest first -> transcripts and comments on the leaders.
def run_youtube(args, entries):
    channels = []
    for entry in entries:
        target = youtube_target(entry["handle"])
        if target:
            channels.append({"name": entry["name"], "target": target})
        else:
            sys.stderr.write(f"skipping (not a YouTube channel) :: {entry['handle'][:80]}\n")

    if not channels and not args.query:
        return emit("youtube", []) or sys.stderr.write(
            f"Nothing under '## YouTube' in {WATCHLIST}, and no -q given.\n")

    # Over-fetch: the date window and relevance floor both cut, and a channel
    # posting weekly needs headroom before -d 7 leaves anything standing.
    per_target = max(args.limit, 10) if args.query else max(args.per_source, 5)

    gemini = bool(os.getenv("GEMINI_API_KEY")) and not args.no_gemini
    if gemini:
        if not require_paid(args, {
            "source": "youtube",
            "cost": "gemini reads caption-less videos",
            "query": args.query,
            "discovery_calls": len(channels) + (1 if args.query else 0),
            "max_videos_examined": per_target * (len(channels) + (1 if args.query else 0)),
            "transcripts_and_comments": args.enrich,
            "gemini_fallback": True,
            "calls": {"anthropic": 0, "exa": 0, "rapidapi": 0, "gemini": args.enrich},
            "estimated_usd": round(args.enrich * GEMINI_VIDEO_USD, 4),
            "watching": [c["name"] for c in channels],
            "note": "Upper bound. Only videos without captions are sent to Gemini. yt-dlp itself is free.",
        }):
            return
    elif args.dry_run:
        return print(json.dumps(
            {"source": "youtube", "dry_run": True, "cost": "free",
             "estimated_usd": 0,
             "calls": {"anthropic": 0, "exa": 0, "rapidapi": 0},
             "query": args.query,
             "discovery_calls": len(channels) + (1 if args.query else 0),
             "max_videos_examined": per_target * (len(channels) + (1 if args.query else 0)),
             "transcripts_and_comments": args.enrich,
             "gemini_fallback": False,
             "watching": [c["name"] for c in channels]},
            indent=2, ensure_ascii=False))

    if not ytdlp_base():
        raise SystemExit(
            "yt-dlp not found. Install it with:  python -m pip install yt-dlp")

    # Discovery. Both modes feed one id pool, deduped -- a watched channel's
    # video that also matches the query must not appear twice.
    order, sources = [], {}

    def collect(vids, label):
        for vid in vids:
            if vid not in sources:
                sources[vid] = label
                order.append(vid)

    if args.query:
        collect(discover_videos(
            YT_SEARCH_URL.format(n=per_target, query=args.query),
            per_target, "search"), None)
        sys.stderr.write(f"search '{args.query}': {len(order)} video(s) found\n")
    for channel in channels:
        before = len(order)
        collect(discover_videos(channel["target"], per_target, channel["name"]),
                channel["name"])
        sys.stderr.write(f"{channel['name']}: {len(order) - before} new video(s)\n")

    if not order:
        return emit("youtube", [])

    hydrated = hydrate_videos(order)

    signals, out_of_window, live_skipped = [], 0, 0
    for vid in order:
        video = hydrated.get(vid)
        if not video:
            continue
        if any(video.get(flag) for flag in YT_SKIP_LIVE):
            live_skipped += 1
            continue
        date = youtube_date(video)
        # Undated videos are kept, matching in_window's contract elsewhere in
        # this file -- but they sort last, since date is the ranking key here.
        if not in_window(date, args.days):
            out_of_window += 1
            continue
        description = _WS.sub(" ", (video.get("description") or "")).strip()
        signals.append({
            "entity": sources.get(vid) or video.get("channel") or "search",
            "author": video.get("channel") or video.get("uploader"),
            "author_url": video.get("channel_url"),
            "title": video.get("title") or "",
            "text": description[:800],
            "url": YT_WATCH_URL.format(vid=vid),
            "date": date,
            "video_id": vid,
            "duration_seconds": video.get("duration"),
            "views": as_count(video.get("view_count")),
            "likes": as_count(video.get("like_count")),
            "comments": as_count(video.get("comment_count")),
            # Views, deliberately -- the best single indicator of reach on
            # YouTube. Never a sum: views dwarf likes by orders of magnitude, so
            # adding them would change nothing but the number's meaning. Still
            # only a tiebreaker behind date.
            "engagement": as_count(video.get("view_count")),
        })

    if live_skipped:
        sys.stderr.write(f"skipped {live_skipped} live/upcoming stream(s)\n")
    sys.stderr.write(f"{len(signals)} video(s) in the last {args.days}d "
                     f"({out_of_window} outside the window)\n")

    # Same guard as Reddit's: a search that matched on filler words would
    # otherwise fill the brief with off-topic videos. Titles and descriptions
    # only -- transcripts are not fetched yet, and fetching them all to filter
    # would cost far more than the filter saves.
    if args.query and signals:
        for signal in signals:
            signal["relevance"] = round(
                relevance(args.query, f"{signal['title']} {signal['text']}"), 2)
        floor = relevance_floor(args.query)
        # A watched channel's video is kept regardless: the user asked to watch
        # that channel, so it is on topic by definition.
        kept = [s for s in signals
                if sources.get(s["video_id"]) or s["relevance"] >= floor]
        cut = len(signals) - len(kept)
        if cut:
            sys.stderr.write(f"{cut} of {len(signals)} video(s) cut below "
                             f"relevance floor {round(floor, 2)}\n")
        if not kept:
            best = max((s["relevance"] for s in signals), default=0.0)
            sys.stderr.write(f"nothing cleared the floor (best was {best}); "
                             f"try a shorter or broader -q\n")
            return emit("youtube", [], {"filtered_out": len(signals),
                                        "best_relevance": best})
        signals = kept

    if not signals:
        return emit("youtube", [])

    # DATE first -- this is the whole point of the source. Views only separate
    # two videos published the same day.
    signals.sort(key=lambda s: (s["date"] or "", s["views"] or 0), reverse=True)
    signals = signals[:args.limit]

    # Transcripts and comments are the expensive part (2 yt-dlp calls each), so
    # only the leaders get them -- and they are the reason to use this source at
    # all, so --enrich 0 is a deliberate choice, not the default.
    enriched = 0
    fallbacks = 0
    use_gemini = bool(os.getenv("GEMINI_API_KEY")) and not args.no_gemini
    for signal in signals[:args.enrich]:
        transcript = fetch_transcript(signal["video_id"])
        if transcript:
            signal["transcript"] = transcript
            signal["transcript_source"] = "captions"
        elif use_gemini and fallbacks < GEMINI_MAX_FALLBACKS:
            # No captions -- have Gemini watch the video instead.
            fallbacks += 1
            transcript = gemini_transcript(signal["video_id"])
            if transcript:
                signal["transcript"] = transcript
                signal["transcript_source"] = "gemini"
            else:
                signal["transcript_unavailable"] = True
        else:
            # Captions genuinely absent, or YouTube throttled us. Either way the
            # analysis must not silently treat the video as having said nothing.
            signal["transcript_unavailable"] = True
        signal["top_comments"] = fetch_youtube_comments(signal["video_id"])
        enriched += 1
    if enriched:
        done = signals[:enriched]
        got = sum(1 for s in done if s.get("transcript"))
        via = sum(1 for s in done if s.get("transcript_source") == "gemini")
        pulled = sum(len(s.get("top_comments") or []) for s in done)
        extra = f" ({via} via gemini)" if via else ""
        sys.stderr.write(f"enriched {enriched} video(s): {got} transcript(s){extra}, "
                         f"{pulled} comment(s)\n")

    emit("youtube", signals)


# --- Web ----------------------------------------------------------------------
#
# Tier 3 of the ladder in skills/social-listening. Tier 1 is the agent's own web
# search tool, which a script cannot call; this file owns tiers 2 and 3:
#
#   keyed backends   BRAVE -> EXA -> SERPER -> PARALLEL, first key found wins
#   keyless floor    DuckDuckGo HTML -> Startpage HTML, no key, no account
#
# Unlike the other sources the open web reports no engagement, so results are
# ranked by date, newest first, same as YouTube -- an old page ranking well is
# not a signal.

WEB_TIMEOUT = 20
# Ladder order: whichever key is present first is used. Brave leads because its
# freshness filter is a real date range rather than a re-ranked relevance sort.
WEB_BACKENDS = (("brave", "BRAVE_API_KEY"), ("exa", "EXA_API_KEY"),
                ("serper", "SERPER_API_KEY"), ("parallel", "PARALLEL_API_KEY"))

DDG_HTML_URL = "https://html.duckduckgo.com/html/"
STARTPAGE_URL = "https://www.startpage.com/sp/search"

# Strip <style>/<script> with their contents before dropping tags, or inline CSS
# leaks into a title. Startpage's class names carry hashed suffixes, so the
# patterns match on the stable "result-title"/"description" substrings.
_STYLE_SCRIPT = re.compile(r"<(style|script)\b[^>]*>.*?</\1>", re.I | re.DOTALL)
_DDG_RESULT = re.compile(
    r'class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.I | re.DOTALL)
_DDG_SNIPPET = re.compile(r'class="result__snippet"[^>]*>(?P<snippet>.*?)</a>', re.I | re.DOTALL)
_SP_RESULT = re.compile(
    r'<a\b[^>]*class="[^"]*result-title[^"]*"[^>]*href="(?P<href>https?://[^"]+)"[^>]*>'
    r'(?P<inner>.*?)</a>', re.I | re.DOTALL)
_SP_H2 = re.compile(r"<h2\b[^>]*>(?P<title>.*?)</h2>", re.I | re.DOTALL)
_SP_DESC = re.compile(r'<p\b[^>]*class="[^"]*description[^"]*"[^>]*>(?P<snippet>.*?)</p>',
                      re.I | re.DOTALL)


# Markup fragment -> plain text.
def strip_html(fragment):
    return _WS.sub(" ", html.unescape(_TAG.sub("", _STYLE_SCRIPT.sub("", fragment or "")))).strip()


# Any date shape a search API returns -> YYYY-MM-DD, or None. Serper answers in
# prose ("Mar 4, 2026") and relative form ("3 days ago"); the rest use ISO.
def web_date(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    relative = re.fullmatch(r"(\d+)\s+(hour|day|week|month|year)s?\s+ago", raw, re.I)
    if relative:
        count = int(relative.group(1))
        days = {"hour": count / 24, "day": count, "week": count * 7,
                "month": count * 30, "year": count * 365}[relative.group(2).lower()]
        return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    iso = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if iso:
        return iso.group(1)
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def web_domain(url):
    return urllib.parse.urlparse(url or "").netloc.strip().lower().removeprefix("www.")


# One normalised result. Shared by every backend so the emitted shape never
# depends on which one ran.
def web_item(entity, title, url, snippet, date, backend):
    domain = web_domain(url)
    return {
        "entity": entity or domain,
        # True when this came from a site: query for a watchlist domain, which
        # exempts it from the relevance floor below.
        "watched": entity is not None,
        "author": domain,
        "author_url": f"https://{domain}" if domain else None,
        "title": strip_html(title)[:300],
        "text": strip_html(snippet)[:800],
        "url": url,
        "date": date,
        "source_domain": domain,
        "backend": backend,
        # The open web reports no engagement. null, not 0 -- 0 would claim the
        # page flopped, which is a different claim from there being no counter.
        "engagement": None,
    }


# GET returning text, browser UA. None on any failure -- one dead backend must
# never sink the run.
def web_text(url, headers=None):
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": BROWSER_UA, "Accept": "text/html", **(headers or {})})
        with urllib.request.urlopen(request, timeout=WEB_TIMEOUT) as response:
            return response.read().decode("utf-8", "replace")
    except Exception as err:
        sys.stderr.write(f"web fetch failed :: {url[:100]} :: {err}\n")
        return None


# GET/POST returning parsed JSON, or None. Same contract as web_text.
def web_json(url, headers, body=None):
    try:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json",
                     **headers})
        with urllib.request.urlopen(request, timeout=WEB_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:200]
        sys.stderr.write(f"web API HTTP {err.code} :: {url[:60]} :: {detail}\n")
    except Exception as err:
        sys.stderr.write(f"web API failed :: {url[:60]} :: {err}\n")
    return None


# --- keyed backends ---


def search_brave(query, entity, since, today, count, key):
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
        {"q": query, "count": count, "freshness": f"{since}to{today}"})
    data = web_json(url, {"X-Subscription-Token": key}) or {}
    return [web_item(entity, r.get("title"), r.get("url"), r.get("description"),
                     web_date(r.get("page_age")), "brave")
            for r in (data.get("web") or {}).get("results", [])[:count] if r.get("url")]


def search_exa(query, entity, since, today, count, key):
    data = web_json("https://api.exa.ai/search", {"x-api-key": key}, {
        "query": query, "type": "auto", "numResults": count,
        "startPublishedDate": f"{since}T00:00:00.000Z",
        "endPublishedDate": f"{today}T23:59:59.999Z",
        "contents": {"text": {"maxCharacters": 1000}},
    }) or {}
    return [web_item(entity, r.get("title"), r.get("url"), r.get("text"),
                     web_date(r.get("publishedDate")), "exa")
            for r in data.get("results", [])[:count] if isinstance(r, dict) and r.get("url")]


def search_serper(query, entity, since, today, count, key):
    def slashed(iso):
        year, month, day = iso.split("-")
        return f"{month}/{day}/{year}"
    data = web_json("https://google.serper.dev/search", {"X-API-KEY": key}, {
        "q": query, "num": count,
        "tbs": f"cdr:1,cd_min:{slashed(since)},cd_max:{slashed(today)}",
    }) or {}
    return [web_item(entity, r.get("title"), r.get("link"), r.get("snippet"),
                     web_date(r.get("date")), "serper")
            for r in data.get("organic", [])[:count] if r.get("link")]


def search_parallel(query, entity, since, today, count, key):
    data = web_json("https://api.parallel.ai/v1/search",
                    {"Authorization": f"Bearer {key}"},
                    {"search_queries": [query],
                     "advanced_settings": {"max_results": count}}) or {}
    items = []
    for r in data.get("results", [])[:count]:
        if not isinstance(r, dict) or not r.get("url"):
            continue
        excerpt = (r.get("excerpts") or [""])[0] or ""
        items.append(web_item(entity, r.get("title"), r.get("url"), excerpt,
                              web_date(r.get("publish_date")), "parallel"))
    return items


# --- keyless floor ---


# DuckDuckGo wraps results as //duckduckgo.com/l/?uddg=<encoded target>.
def unwrap_ddg(href):
    if "uddg=" not in href:
        return href if href.startswith("http") else (
            f"https:{href}" if href.startswith("//") else "")
    try:
        query = urllib.parse.urlparse(
            href if href.startswith("http") else f"https:{href}").query
        return urllib.parse.parse_qs(query).get("uddg", [""])[0]
    except ValueError:
        return ""


def search_ddg(query, entity, count):
    text = web_text(f"{DDG_HTML_URL}?{urllib.parse.urlencode({'q': query})}")
    if not text:
        return []
    items = []
    # Snippets are matched inside each result's own window, not zipped: some
    # anchors (news/video modules) carry no snippet, and a global zip would
    # shift every later snippet onto the wrong result.
    matches = list(_DDG_RESULT.finditer(text))
    for index, match in enumerate(matches):
        if len(items) >= count:
            break
        target = unwrap_ddg(match.group("href"))
        if not target.startswith("http"):
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        snippet = _DDG_SNIPPET.search(text[match.end():end])
        items.append(web_item(entity, match.group("title"), target,
                              snippet.group("snippet") if snippet else "", None, "duckduckgo"))
    return items


# Rung 2. DuckDuckGo answers a datacenter IP with a 202 challenge page and no
# results; Startpage still serves organic hits to a plain browser UA, so it is
# the working floor wherever DuckDuckGo refuses.
def search_startpage(query, entity, count):
    text = web_text(f"{STARTPAGE_URL}?{urllib.parse.urlencode({'query': query})}")
    if not text:
        return []
    items, descriptions = [], list(_SP_DESC.finditer(text))
    for match in _SP_RESULT.finditer(text):
        if len(items) >= count:
            break
        target = html.unescape(match.group("href"))
        heading = _SP_H2.search(match.group("inner"))
        title = strip_html(heading.group("title") if heading else match.group("inner"))
        if not target.startswith("http") or not title:
            continue
        snippet = next((d.group("snippet") for d in descriptions if d.start() > match.end()), "")
        items.append(web_item(entity, title, target, snippet, None, "startpage"))
    return items


# Picks the backend once per run -> (name, key). Keyed backends win in ladder
# order; the keyless floor is what is left when no key is set.
def web_backend(requested):
    for name, key_var in WEB_BACKENDS:
        if requested in (name, "auto") and os.environ.get(key_var):
            return name, os.environ[key_var]
        if requested == name:
            raise SystemExit(f"--web-backend {name} needs {key_var} in .env.")
    return "keyless", None


# One query against the chosen backend. The keyless floor tries DuckDuckGo, then
# Startpage; keyed backends get no fallback, since a failing key is worth seeing.
def web_search(query, entity, backend, key, since, today, count):
    if backend == "keyless":
        return search_ddg(query, entity, count) or search_startpage(query, entity, count)
    runner = {"brave": search_brave, "exa": search_exa,
              "serper": search_serper, "parallel": search_parallel}[backend]
    return runner(query, entity, since, today, count, key)


# Full web run: build queries, search each, dedupe by URL, sort by date, print.
def run_web(args, entries):
    today = datetime.now(timezone.utc).date()
    since = today - timedelta(days=args.days)
    backend, key = web_backend(args.web_backend)

    # A watchlist line is a domain to monitor: "Name: taplio.com" becomes a
    # site: query, so the run surfaces what that competitor published. -q
    # searches the open web, and the two combine when both are given.
    targets = []
    if args.query:
        targets.append({"query": args.query, "entity": None})
    for entry in entries:
        raw = entry["handle"]
        domain = web_domain(raw if "//" in raw else f"//{raw}")
        if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", domain):
            sys.stderr.write(f"skipping (not a domain) :: {raw[:80]}\n")
            continue
        scoped = f"site:{domain} {args.query}" if args.query else f"site:{domain}"
        targets.append({"query": scoped, "entity": entry["name"]})

    if not targets:
        return emit("web", []) or sys.stderr.write(
            f"Nothing under '## Web' in {WATCHLIST}, and no -q given.\n")

    query_count = len(targets)
    if backend != "keyless":
        exa_calls = query_count if backend == "exa" else 0
        each = EXA_SEARCH_USD if backend == "exa" else WEB_QUERY_USD
        if not require_paid(args, {
            "source": "web",
            "backend": backend,
            "calls": {"anthropic": 0, "exa": exa_calls, "rapidapi": 0, backend: query_count},
            "estimated_usd": round(query_count * each, 4),
            "queries": [t["query"] for t in targets],
            "note": "One paid search call per query.",
        }):
            return
    elif args.dry_run:
        return print(json.dumps(
            {"source": "web", "dry_run": True, "backend": backend,
             "cost": "free", "estimated_usd": 0,
             "calls": {"anthropic": 0, "exa": 0, "rapidapi": 0},
             "queries": [t["query"] for t in targets]}, indent=2, ensure_ascii=False))

    sys.stderr.write(f"backend: {backend} ({len(targets)} query/queries)\n")
    signals, seen = [], set()
    for target in targets:
        found = web_search(target["query"], target["entity"], backend, key,
                           since.isoformat(), today.isoformat(), args.per_source)
        kept = 0
        for item in found:
            if item["url"] in seen:
                continue
            # Dates here are bare YYYY-MM-DD, so they are compared as strings
            # rather than through in_window, which expects a tz-aware timestamp.
            # Undated (keyless) results are kept, matching in_window's contract.
            if item["date"] and item["date"] < since.isoformat():
                continue
            seen.add(item["url"])
            signals.append(item)
            kept += 1
        label = target["entity"] or f"'{target['query'][:40]}'"
        if not found:
            sys.stderr.write(f"{label}: no results (blocked, or nothing indexed)\n")
        else:
            sys.stderr.write(f"{label}: {kept} of {len(found)} result(s) in window\n")

    if not signals:
        return emit("web", [], {"backend": backend})

    # Same guard as Reddit's and YouTube's: a query matching on filler words
    # would otherwise fill the brief. site: results are exempt -- a watched
    # domain is on topic by definition.
    if args.query:
        for signal in signals:
            signal["relevance"] = round(
                relevance(args.query, f"{signal['title']} {signal['text']}"), 2)
        floor = relevance_floor(args.query)
        kept = [s for s in signals if s["watched"] or s["relevance"] >= floor]
        if len(kept) < len(signals):
            sys.stderr.write(f"{len(signals) - len(kept)} of {len(signals)} result(s) "
                             f"cut below relevance floor {round(floor, 2)}\n")
        if not kept:
            best = max((s["relevance"] for s in signals), default=0.0)
            sys.stderr.write(f"nothing cleared the floor (best was {best}); "
                             f"try a shorter or broader -q\n")
            return emit("web", [], {"filtered_out": len(signals),
                                    "best_relevance": best, "backend": backend})
        signals = kept

    # DATE first, like YouTube: the open web has no engagement count, and an old
    # page ranking well is not a signal. Undated (keyless) results sort last.
    signals.sort(key=lambda s: s["date"] or "", reverse=True)
    undated = sum(1 for s in signals if not s["date"])
    if undated:
        sys.stderr.write(f"{undated} result(s) carry no date "
                         f"({backend} reports none); they sort last\n")
    emit("web", signals[:args.limit], {"backend": backend})


# Parses flags and hands off to the chosen source.
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source",
                        choices=("linkedin", "x", "reddit", "youtube", "web"),
                        required=True)
    parser.add_argument("-d", "--days", type=int, default=7)
    parser.add_argument("-n", "--limit", type=int, default=25)
    parser.add_argument("-q", "--query",
                        help="X, Reddit, YouTube and Web: free-text topic research")
    parser.add_argument("--per-source", type=int, default=10,
                        help="LinkedIn: max posts per watchlist line (this is the bill). "
                             "YouTube: how many recent videos to examine per channel (free). "
                             "Web: max results per query")
    parser.add_argument("--enrich", type=int, default=5,
                        help="Reddit: how many top posts get their comments fetched. "
                             "YouTube: how many top videos get transcript + comments")
    parser.add_argument("--model", default=XAI_MODEL, help=f"X only (default {XAI_MODEL})")
    parser.add_argument("--web-backend", default="auto",
                        choices=("auto", "brave", "exa", "serper", "parallel", "keyless"),
                        help="Web: force a backend. Default auto -- first key found "
                             "in .env, else the keyless floor")
    parser.add_argument("--no-gemini", action="store_true",
                        help="YouTube: skip the Gemini fallback that reads "
                             "caption-less videos (on whenever GEMINI_API_KEY is set)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print call counts and approximate cost, then stop")
    parser.add_argument("--estimate", action="store_true",
                        help="Same as --dry-run")
    parser.add_argument("--confirm", action="store_true",
                        help="Required before LinkedIn, X, a keyed web backend, or YouTube with Gemini")
    args = parser.parse_args()
    if args.estimate:
        args.dry_run = True

    load_env()
    if args.source == "linkedin":
        if args.query:
            raise SystemExit("-q is X, Reddit and YouTube only; LinkedIn reads the watchlist.")
        run_linkedin(args, read_watchlist("LinkedIn"))
    elif args.source == "youtube":
        # In query mode a missing watchlist must not be fatal.
        entries = [] if (args.query and not os.path.exists(WATCHLIST)) else read_watchlist("YouTube")
        run_youtube(args, entries)
    elif args.source == "web":
        # In query mode a missing watchlist must not be fatal.
        entries = [] if (args.query and not os.path.exists(WATCHLIST)) else read_watchlist("Web")
        run_web(args, entries)
    elif args.source == "reddit":
        # In query mode a missing watchlist must not be fatal.
        entries = [] if (args.query and not os.path.exists(WATCHLIST)) else read_watchlist("Reddit")
        run_reddit(args, entries)
    else:
        # In query mode a missing watchlist must not be fatal.
        entries = [] if (args.query and not os.path.exists(WATCHLIST)) else read_watchlist("X")
        run_x(args, entries)


if __name__ == "__main__":
    main()
