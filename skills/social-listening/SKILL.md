---
name: social-listening
description: Monitor what watched competitors and creators are posting on LinkedIn and X. Reads context/signals/watchlist.md, asks which sources to run, reports conversationally in chat. Triggers on /social-listening or "what are my competitors posting", "check social listening", "what did [competitor] publish this week", "what is X saying about [topic]".
---

# Social Listening

What the watchlist is **saying**. For what they are **doing** (hiring, funding,
launching), use `skills/intent-signals`.

Output is a conversational digest in chat. No file is written.

## Sources

One script, `scripts/signals/social-listening.py`, with `--source`:

| Source | Cost | Needs |
|---|---|---|
| `linkedin` | bills per post scraped | `APIFY_API_KEY` |
| `x` | one API call per run, `-n` is ~free | `X_API_KEY` |

Who to watch: `context/signals/watchlist.md`, under `## LinkedIn` / `## X`.
What counts as a signal: `context/signals/signals.md` if it exists — use it to
judge relevance and ordering. If missing, use judgement and say once that
filling it in sharpens future runs.

## Step 1 — Ask first

**Never run both sources by default.** Ask with AskUserQuestion
(`multiSelect: true`), offering only sources whose watchlist section has entries
and whose key is in `.env`. Say how many entities each watches.

Skip the question when the user named the source ("check LinkedIn"), or asked a
topic question — that is always X query mode, run it directly.

## Step 2 — Run

```bash
python scripts/signals/social-listening.py --source linkedin -d 7 -n 25 --per-source 10
python scripts/signals/social-listening.py --source x -d 7 -n 25
python scripts/signals/social-listening.py --source x -q "AI ghostwriting pricing"
```

Both print `{"source","count","signals":[...]}` to stdout, **already sorted by
engagement, highest first**. Per-entity notes go to stderr. The JSON is for you;
never paste it into chat. Sources are independent — run them in parallel.

**LinkedIn** — `--per-source` (default 10) caps posts per watchlist line; one run
scrapes at most `lines x --per-source`, and that is the bill. `-d` filters after
fetching, so narrowing it saves nothing — lower `--per-source` instead.
`--dry-run` is free and prints `max_posts_scraped`; use it when the section is
long. Read the stderr lines: a profile returning nothing means unreachable or
inactive, never "quiet".

**X** — `-q` researches a topic across all of X (no watchlist needed); with a
watchlist it narrows that topic to those accounts. Takes ~2 minutes, one call
regardless of `-n`. Caps at 20 handles.

## Step 3 — Report

One merged digest across whatever ran, not a section per source.

**Lead with engagement.** Both sources return real counts, so rank by what
actually landed, not by what arrived first. Quote the numbers — "758 likes, 24
replies" — and say what the top performer was about; that is usually the finding.
Group by theme when several entities circle the same topic.

`engagement` is `likes + reposts + replies` on X, `reactions + comments + shares`
on LinkedIn. A **null** engagement means the count was unknown, not zero — say
"engagement unknown", never that it flopped.

Always include the source URL. Say plainly when a run found nothing; do not pad.
**Never invent a signal that was not in the JSON.** Close with one line on what
is worth acting on.

## Next

```
Read skills/intent-signals/SKILL.md and check buying signals for my watchlist.
```
