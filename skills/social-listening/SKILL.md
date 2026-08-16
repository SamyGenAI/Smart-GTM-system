---
name: social-listening
description: Monitor what watched competitors, companies, and people are saying and publishing across LinkedIn, X, Reddit, Substack, YouTube, newsletters, and web/news. Reads context/signals/watchlist.md, asks which sources to run, and reports findings conversationally. Triggers on /social-listening or any message like "what are my competitors posting", "check social listening", "monitor my watchlist", or "what did [competitor] publish this week".
---

# Skill: Social Listening

**Duration:** 1-5 minutes depending on how many sources are selected
**Output:** A conversational digest in chat. No file is written.

## Quick Start

```
Read skills/social-listening/SKILL.md and check what my watchlist has been posting this week.
```

## Purpose

Watch what a defined set of competitors, companies, and people are **saying and publishing**. This is the listening half of the signal system — for what they are *doing* (hiring, funding, launching), use `skills/intent-signals`.

## Dependencies

Two context files, deliberately separate:

- `context/signals/watchlist.md` — **who** to watch, one line per entity, grouped by platform. Required. If missing, copy `context/signals/watchlist-template.md` and help the user fill it in.
- `context/signals/signals.md` — **what** counts as a signal and how to rank it. Optional; if missing, use your own judgement and mention that filling it in will sharpen results.

Also needed:

- Python 3 available as `python` on PATH.
- Per-source API keys in `.env` — see the Requires column below.

## Available Sources

Each source is a standalone script. Nothing is shared between them, so a source that is not built yet simply does not exist as a file.

| Source | Script | Status | Requires | Watchlist section |
|---|---|---|---|---|
| Demo | `scripts/signals/listening/demo.py` | ✅ built | — | `## Demo` |
| LinkedIn | `scripts/signals/listening/linkedin.py` | ⬜ not built | `RAPIDAPI_KEY` | `## LinkedIn` |
| X | `scripts/signals/listening/x.py` | ⬜ not built | TBD | `## X` |
| Reddit | `scripts/signals/listening/reddit.py` | ⬜ not built | — | `## Reddit` |
| Substack | `scripts/signals/listening/substack.py` | ⬜ not built | TBD | `## Substack` |
| YouTube | `scripts/signals/listening/youtube.py` | ⬜ not built | TBD | `## YouTube` |
| Newsletters | `scripts/signals/listening/newsletters.py` | ⬜ not built | TBD | `## Newsletters` |
| Web / News | `scripts/signals/listening/websearch.py` | ⬜ not built | `EXA_API_KEY` | `## Web` |

The Demo source returns fabricated `[DEMO]`-prefixed data and calls no API. Use it only to verify the flow works — never present its output as real findings.

## Hard rules

- **NEVER run every source by default.** Running all sources burns API quota and takes minutes.
- **ALWAYS ask which sources to run before running anything**, using AskUserQuestion with `multiSelect: true`. Offer only sources that are ✅ built AND whose section in `context/signals/watchlist.md` has at least one line.
- **The one exception:** the user already named the sources in their message ("check Reddit and X for me"). Then run exactly those and skip the question.
- If a requested source is ⬜ not built, say so plainly and offer the built ones instead. **Never fabricate a result.**
- If a source's required env key is missing from `.env`, exclude it from the options and tell the user which key it needs.
- Never present `[DEMO]` output as real. If a run returns demo data, say explicitly that it is placeholder output.

## Step 1 — Ask Which Sources

Before running anything:

1. Read `context/signals/watchlist.md`. If it does not exist, stop and help the user create it from `watchlist-template.md`.
2. Check which sections have at least one line under them.
3. Check `.env` for each candidate source's required key.
4. Ask with AskUserQuestion, `multiSelect: true`, listing only the sources that pass all three checks. In each option's description, say how many entities are watched on that platform — e.g. "4 entities watched".

Skip this step only when the user already named the sources.

## Step 2 — Run

One command per selected source. Run independent sources in parallel:

```bash
python scripts/signals/listening/demo.py -d 7 -n 25
```

Flags every source script accepts:

| Flag | Default | Description |
|---|---|---|
| `-d`, `--days` | 7 | Lookback window in days |
| `-n`, `--limit` | 25 | Max signals returned |
| `--dry-run` | off | Print the resolved watchlist and exit without fetching |

Run from the repo root — scripts resolve `.env` and `context/` relative to the working directory.

Each script prints JSON to stdout: `{"source", "count", "signals": [...]}`. Warnings and per-entity errors go to stderr; a failed entity does not stop the run. If a script exits non-zero, report what failed and continue with the sources that succeeded.

## Step 3 — Report

Read the JSON from every script and compose **one merged digest** — not one section per script. The JSON is for you, not the user; never paste it into chat.

Judge relevance against `context/signals/signals.md` if it exists:
- Use **What to surface** to decide what is worth reporting.
- Use **How to rank** to decide ordering.

If that file is missing, use your own judgement and say once that filling it in will sharpen future runs.

## Output (conversational — no file written)

This skill does NOT write a CSV. Present the findings in whatever shape fits what came back:

- A markdown table when signals are uniform and comparable
- Grouped bullets when they span several entities or platforms
- Short prose when there are only one or two things worth saying

Lead with what matters most, not with what arrived first. Group by theme when several entities are circling the same topic — that pattern is usually the real finding.

Always include the source URL so the user can verify. Say plainly when a run found nothing — do not pad. **Never invent a signal that was not in the JSON.**

Close with one line on what is worth acting on, if anything is.

## Adding a new source

1. Copy `scripts/signals/listening/demo.py` to `scripts/signals/listening/<source>.py`.
2. Update the header docstring, `SOURCE`, `WATCHLIST_SECTION`, and `REQUIRED_ENV`.
3. Rewrite `fetch_entry()` to call the real API. Leave the rest alone.
4. Flip that row to ✅ built in the table above and fill in its Requires column.

Each script is fully self-contained — stdlib only, no local imports. Duplicated helpers are intentional: nothing shared means nothing to break elsewhere.

## Next Step

```
Read skills/intent-signals/SKILL.md and check buying signals for the companies on my watchlist.
```
