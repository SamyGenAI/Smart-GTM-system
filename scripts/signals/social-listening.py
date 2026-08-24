"""Social listening: pull recent posts from the accounts in the watchlist.

Reads context/signals/watchlist.md. Two sources, pick with --source:

    linkedin  Apify actor `supreme_coder/linkedin-post`. Bills per post.
    x         xAI Grok `x_search`. One API call per run, so -n is ~free.
              Also does free-text topic research via -q, no watchlist needed.

Prints JSON to stdout for the agent, signals sorted by engagement.

Usage:
    python scripts/signals/social-listening.py --source linkedin -d 7 -n 25
    python scripts/signals/social-listening.py --source x -d 7 -n 25
    python scripts/signals/social-listening.py --source x -q "AI ghostwriting pricing"
    python scripts/signals/social-listening.py --source x --dry-run

Cost: LinkedIn bills per post -- one run scrapes at most
(watchlist lines) x --per-source, and -d filters after fetching, so lower
--per-source to spend less. X bills per request, not per post. --dry-run is free.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
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
    r"^https?://(?:www\.)?(?:x|twitter)\.com/[A-Za-z0-9_]{1,15}/status/\d+", re.I)

X_CONTRACT = """Return ONLY a JSON object of this exact shape:
{"posts":[{"entity":"watchlist name, or the handle when researching a topic",
"author":"display name","handle":"bare handle, no @","text":"full post text",
"url":"https://x.com/<handle>/status/<id>","date":"ISO 8601",
"likes":0,"reposts":0,"replies":0,"post_type":"post|reply|quote|thread"}]}
likes/reposts/replies must be integers, or null when genuinely unknown.
Empty posts array if nothing relevant. No other keys, no markdown fences."""

X_INSTRUCTIONS = (
    "You are a B2B go-to-market social listening analyst. Report ONLY posts you "
    "actually found via x_search. Never invent a post, URL, author, or count. "
    "Every post needs its real permalink: https://x.com/<handle>/status/<id>. "
    "Report engagement counts as the search returned them; use null when a count "
    "is genuinely unknown, never 0 for unknown. Prefer substantive posts over "
    "pure retweets, one-word replies and giveaways. Return the JSON object only."
)


def load_env():
    """Parse .env from the repo root into os.environ. Real env vars win."""
    if not os.path.exists(".env"):
        return
    with open(".env", encoding="utf-8") as fh:
        for line in fh:
            key, sep, value = line.strip().partition("=")
            if sep and not key.startswith("#") and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip().strip("\"'")


def read_watchlist(section):
    """Return [{name, handle}] from the '## <section>' heading.

    Lines are `Name: handle-or-url`. Notes must start with > - * or # so they
    are never sent to an API -- on LinkedIn every accepted line costs credits.
    """
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


def emit(source, signals, extra=None):
    payload = {"source": source, "count": len(signals), "signals": signals}
    payload.update(extra or {})
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def post_json(url, body, headers):
    request = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              **headers})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


# --- LinkedIn ----------------------------------------------------------------


def linkedin_url(handle):
    """Coerce a watchlist line to a LinkedIn URL, or None to drop it.

    Dropping matters here: every accepted line is billed for up to
    --per-source posts, so prose left in the section must not reach the actor.
    """
    if handle.startswith(("http://", "https://", "linkedin.com", "www.linkedin.com")):
        url = handle if "//" in handle else "https://" + handle.lstrip("/")
        return url if "linkedin.com/" in url.lower() else None
    if re.fullmatch(r"@?[A-Za-z0-9À-ÿ_.-]{3,100}", handle):
        return "https://www.linkedin.com/in/" + handle.lstrip("@/")
    return None


def call_actor(url, per_source, token):
    """Run the actor for ONE url. Returns [] on failure so others still run.

    One URL per run on purpose: a batched run silently returns posts for only
    some URLs while billing for all of them.

    numLikes/numComments are omitted from the payload rather than set to 0 --
    passing 0 makes this actor return an empty dataset (verified live).
    """
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


def in_window(iso, days):
    """True if the post is recent enough. Undated posts are kept."""
    if not iso:
        return True
    try:
        posted = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return True
    return posted >= datetime.now(timezone.utc) - timedelta(days=days)


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
        # A silent profile is this source's main failure mode -- say so, or a
        # broken scrape reads as a quiet competitor.
        if not items:
            sys.stderr.write(f"{entry['name']}: no posts returned (unreachable or inactive)\n")
        elif not kept:
            sys.stderr.write(f"{entry['name']}: {len(items)} fetched, none in last {args.days}d\n")
        else:
            sys.stderr.write(f"{entry['name']}: {kept} post(s) in window\n")

    signals.sort(key=lambda s: s["engagement"], reverse=True)
    emit("linkedin", signals[:args.limit])


# --- X -----------------------------------------------------------------------


def x_handle(raw):
    """Reduce a watchlist line to a bare X handle, or None if it is not one."""
    match = re.search(r"(?:^|//|\.)(?:x|twitter)\.com/@?([A-Za-z0-9_]{1,15})", raw, re.I)
    if match:
        reserved = {"search", "home", "i", "explore", "hashtag", "intent", "share"}
        return None if match.group(1).lower() in reserved else match.group(1)
    if raw.startswith(("http://", "https://")):
        return None  # a URL, but not an X profile
    raw = raw.lstrip("@")
    return raw if re.fullmatch(r"[A-Za-z0-9_]{1,15}", raw) else None


def as_count(value):
    """Coerce a reported metric to int, or None when genuinely unknown.

    None is deliberate: 0 would assert a post flopped, which is a different
    claim from not knowing. Unknowns sort last.
    """
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


def x_text(response):
    """Pull the assistant message out of the /v1/responses envelope.

    The output array interleaves tool calls with the message, so the message
    has to be picked out rather than read positionally.
    """
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
              f"Return at most {args.limit} posts, highest-engagement first.\n\n{X_CONTRACT}")

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
        # No usable permalink is the clearest tell the model produced something
        # it did not actually find.
        if not X_POST_URL.match(url):
            dropped += 1
            continue
        handle = (post.get("handle") or "").strip().lstrip("@")
        if not handle:
            found = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/", url, re.I)
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
            "post_type": post.get("post_type"),
        })
    if dropped:
        sys.stderr.write(f"dropped {dropped} record(s) with no valid permalink.\n")
    sys.stderr.write(f"{len(signals)} post(s) returned.\n")

    # Re-sorted here rather than trusting the model's ordering. Unknown
    # engagement sorts last -- unknown is not the same as zero.
    signals.sort(key=lambda s: (s["engagement"] is not None, s["engagement"] or 0),
                 reverse=True)
    emit("x", signals[:args.limit])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--source", choices=("linkedin", "x"), required=True)
    parser.add_argument("-d", "--days", type=int, default=7)
    parser.add_argument("-n", "--limit", type=int, default=25)
    parser.add_argument("-q", "--query", help="X only: free-text topic research")
    parser.add_argument("--per-source", type=int, default=10,
                        help="LinkedIn only: max posts per watchlist line (this is the bill)")
    parser.add_argument("--model", default=XAI_MODEL, help=f"X only (default {XAI_MODEL})")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    if args.source == "linkedin":
        if args.query:
            raise SystemExit("-q is X only; LinkedIn reads the watchlist.")
        run_linkedin(args, read_watchlist("LinkedIn"))
    else:
        # In query mode a missing watchlist must not be fatal.
        entries = [] if (args.query and not os.path.exists(WATCHLIST)) else read_watchlist("X")
        run_x(args, entries)


if __name__ == "__main__":
    main()
