"""Source: demo | Kind: intent | Env: (none)

REFERENCE IMPLEMENTATION. Copy this file to add a real intent signal.

Returns fabricated data, every field prefixed [DEMO]. It exists so the intent
flow is runnable and inspectable before any real API is connected, and so
every future signal script has a concrete file to copy.

Self-contained: stdlib only, zero local imports. Nothing in scripts/signals/
imports anything else in scripts/signals/. Duplicating the helpers below into
each new script is deliberate — hiring scrapes careers pages, funding reads
news, job-change watches profiles. A shared module would either become a
grab-bag or force a new API into an abstraction chosen before anyone knew
its shape.

Reads the "## Companies" section of context/signals/watchlist.md. Most intent
scripts read this same section, since intent is tracked per company rather
than per platform. Job-change and engagement read "## LinkedIn" instead.

Two context files, kept separate on purpose:
    watchlist.md — WHO to watch. Dead simple, one line per entity.
    signals.md   — WHAT counts as a signal and how to rank it. Read by the
                   skill, not by this script.

Usage:
    python scripts/signals/intent/demo.py -d 7 -n 25
    python scripts/signals/intent/demo.py --dry-run

Flags:
    -d, --days     lookback window in days (default 7)
    -n, --limit    max signals to return (default 25)
    --dry-run      print the resolved watchlist and exit, no fetching

Structure every intent script follows:
    1. load_env()               parse .env from cwd
    2. read_watchlist(section)  rows from that ### section of the signals file
    3. fetch loop               per-company try/except, log to stderr, continue
    4. print JSON to stdout     {"source", "count", "signals": [...]}
    5. tail handler             stderr + exit 1

    (Step 2 reads lines under that ## section of watchlist.md.)

Set SIGNAL_TYPE to one of: hiring, website_visit, funding, engagement,
product_launch, job_change. Claude uses it to group findings and to apply the
strength definitions from the Signal Rules section of the signals file.

Output keys are a recommendation, NOT a contract. Add whatever the signal
needs (role_title, round_size, previous_company...), omit what does not apply.
"""

import argparse
import json
import os
import re
import sys

# Windows consoles default to cp1252, which mangles em-dashes and accents in
# the JSON the agent reads. Force UTF-8 on both streams.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# --- Config: the only lines that change when copying this file ---------------

SOURCE = "demo"
SIGNAL_TYPE = "demo"  # hiring | website_visit | funding | engagement | product_launch | job_change
WATCHLIST_SECTION = "Companies"  # or "LinkedIn" for job_change / engagement
REQUIRED_ENV = []  # e.g. ["EXA_API_KEY"]

WATCHLIST_PATH = os.path.join("context", "signals", "watchlist.md")
TEMPLATE_PATH = os.path.join("context", "signals", "watchlist-template.md")


# --- Helpers (duplicated per script by design) -------------------------------


def load_env():
    """Parse .env from the current working directory into os.environ.

    Existing environment variables win. Scripts are run from the repo root.
    """
    if not os.path.exists(".env"):
        return
    with open(".env", "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


def require_env(keys):
    """Exit with a clear message naming any missing required key."""
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise SystemExit(
            f"Missing required env var(s): {', '.join(missing)}\n"
            f"Add them to .env in the repo root. See .env.example."
        )


def read_watchlist(section):
    """Return entries under the '## <section>' heading of the watchlist file.

    Each line is either "Name: handle" or a bare handle. Returns dicts of
    {"name", "handle"}; for a bare handle both keys hold the same value.
    Blank lines, comments and prose are skipped.
    """
    if not os.path.exists(WATCHLIST_PATH):
        raise SystemExit(
            f"Missing {WATCHLIST_PATH}\n"
            f"Copy {TEMPLATE_PATH} to {WATCHLIST_PATH} and list who you want to watch."
        )

    with open(WATCHLIST_PATH, "r", encoding="utf-8") as fh:
        content = fh.read().replace("﻿", "")

    # Everything under "## <section>" up to the next heading.
    pattern = rf"^##\s+{re.escape(section)}\s*$(.*?)(?=^#{{1,6}}\s|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return []

    entries = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ">", "-", "*", "<!--")):
            continue
        # "Name: handle" — split on the first colon that is not part of a URL.
        name, sep, handle = line.partition(":")
        if sep and not handle.lstrip().startswith("//"):
            name, handle = name.strip(), handle.strip()
        else:
            name = handle = line  # bare handle
        if not handle:
            sys.stderr.write(f"[{SOURCE}] skipping line with no handle :: {line}\n")
            continue
        entries.append({"name": name, "handle": handle})
    return entries


def emit(signals):
    """Print the run result as JSON on stdout for the agent to read."""
    print(json.dumps({
        "source": SOURCE,
        "signal_type": SIGNAL_TYPE,
        "count": len(signals),
        "signals": signals,
    }, indent=2, ensure_ascii=False))


# --- Fetch: the part every real signal script rewrites -----------------------


def fetch_entry(entry, days, limit):
    """Return a list of signal dicts for one watched company.

    entry is {"name": ..., "handle": ...}. A real script calls its API or
    scrapes here. This demo fabricates entries so the flow can be exercised
    end to end. Raising is fine — the caller catches per company.
    """
    company = entry["name"]
    return [
        {
            "entity": f"[DEMO] {company}",
            "company": f"[DEMO] {company}",
            "domain": entry["handle"],
            "signal_type": SIGNAL_TYPE,
            "strength": "medium",
            "title": f"[DEMO] intent signal for {company} in the last {days} days",
            "text": (
                "[DEMO] This is fabricated placeholder text. No API was called. "
                "Replace fetch_entry() with a real implementation."
            ),
            "url": f"https://example.com/demo/{company.lower().replace(' ', '-')}",
            "date": "[DEMO] 2026-01-01",
        }
    ][:limit]


def main():
    parser = argparse.ArgumentParser(description=f"Collect {SIGNAL_TYPE} intent signals.")
    parser.add_argument("-d", "--days", type=int, default=7, help="lookback window in days")
    parser.add_argument("-n", "--limit", type=int, default=25, help="max signals to return")
    parser.add_argument("--dry-run", action="store_true", help="show watchlist and exit")
    args = parser.parse_args()

    load_env()
    require_env(REQUIRED_ENV)

    entries = read_watchlist(WATCHLIST_SECTION)
    if not entries:
        emit([])
        sys.stderr.write(
            f"[{SOURCE}] no companies watched. "
            f"Add lines under '## {WATCHLIST_SECTION}' in {WATCHLIST_PATH}.\n"
        )
        return

    if args.dry_run:
        print(json.dumps({
            "source": SOURCE,
            "signal_type": SIGNAL_TYPE,
            "dry_run": True,
            "watching": entries,
        }, indent=2, ensure_ascii=False))
        return

    signals = []
    for entry in entries:
        if len(signals) >= args.limit:
            break
        try:
            signals.extend(fetch_entry(entry, args.days, args.limit - len(signals)))
        except Exception as err:  # one bad company must not kill the run
            sys.stderr.write(f"[{SOURCE}] {entry['name']} error :: {err}\n")

    emit(signals[:args.limit])


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)
