"""Social listening: recent posts from the watchlist, sorted by engagement.

--source linkedin  Apify actor, bills per post scraped.
--source x         xAI Grok x_search, one call per run; -q for topic research.
--source reddit    keyless RSS + arctic-shift + shreddit; free, no API key.

Prints JSON to stdout. Run from the repo root.
"""

import argparse
import html
import json
import os
import re
import sys
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

    if args.dry_run:
        return print(json.dumps(
            {"source": "linkedin", "dry_run": True,
             "max_posts_scraped": len(entries) * args.per_source,
             "watching": [{"name": e["name"], "url": e["url"]} for e in entries]},
            indent=2, ensure_ascii=False))

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

    if args.dry_run:
        return print(json.dumps({"source": "x", "dry_run": True, "api_calls": 1,
                                 "query": args.query, "watching": resolved},
                                indent=2, ensure_ascii=False))

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
                                 "feeds": len(feeds),
                                 "listing_requests": len(subs) * len(LISTING_SORTS),
                                 "query": args.query,
                                 "watching": [f"r/{s}" for s in subs]},
                                indent=2, ensure_ascii=False))

    posts, seen = [], set()
    for feed in feeds:
        for post in parse_feed(http_text(feed, accept="application/atom+xml") or ""):
            if post["url"] in seen or not in_window(post["date"], args.days):
                continue
            seen.add(post["url"])
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
        kept = [p for p in posts if p["relevance"] >= floor]
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


# Parses flags and hands off to the chosen source.
def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", choices=("linkedin", "x", "reddit"), required=True)
    parser.add_argument("-d", "--days", type=int, default=7)
    parser.add_argument("-n", "--limit", type=int, default=25)
    parser.add_argument("-q", "--query", help="X and Reddit: free-text topic research")
    parser.add_argument("--per-source", type=int, default=10,
                        help="LinkedIn only: max posts per watchlist line (this is the bill)")
    parser.add_argument("--enrich", type=int, default=5,
                        help="Reddit only: how many top posts get their comments fetched")
    parser.add_argument("--model", default=XAI_MODEL, help=f"X only (default {XAI_MODEL})")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    if args.source == "linkedin":
        if args.query:
            raise SystemExit("-q is X and Reddit only; LinkedIn reads the watchlist.")
        run_linkedin(args, read_watchlist("LinkedIn"))
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
