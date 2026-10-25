---
name: intent-signals
description: Detect buying-intent signals from watched companies and people — hiring a role, website visits, funding, engagement, product launches, and job changes. Reads context/signals/watchlist.md, asks which signals to check, and reports findings conversationally with a suggested next action. Triggers on /intent-signals or any message like "check intent signals", "who is showing buying intent", "any funding or hiring signals", or "who changed jobs".
---

# Skill: Intent Signals

**Duration:** 1-5 minutes depending on how many signals are selected
**Output:** A conversational digest in chat. No file is written.

## Quick Start

```
Read skills/intent-signals/SKILL.md and check buying signals for my watchlist this week.
```

## Purpose

Detect what watched companies and people are **doing** that implies buying readiness.

## Dependencies

Two context files, deliberately separate:

- `context/signals/watchlist.md` — **who** to watch, one line per entity, grouped by platform. Required. If missing, copy `context/signals/watchlist-template.md` and help the user fill it in.
- `context/signals/signals.md` — **what** counts as a signal and how to rank it. Optional; if missing, fall back to the table below.

Also needed:

- `brain/raw/me/offer.md` heading `## ICP` — judge whether a signal matters. Do not copy it locally.
- Python 3 available as `python` on PATH.
- Per-signal API keys in `.env` — see the Requires column below.

## Available Signals

Each signal is a standalone script. Nothing is shared between them, so a signal that is not built yet simply does not exist as a file.

| Signal | Script | Status | Requires | Watchlist section |
|---|---|---|---|---|
| Demo | `scripts/signals/intent/demo.py` | ✅ built | — | `## Companies` |
| Hiring a role | `scripts/signals/intent/hiring.py` | ⬜ not built | TBD | `## Companies` |
| Funding | `scripts/signals/intent/funding.py` | ⬜ not built | `EXA_API_KEY` | `## Companies` |
| Product launch | `scripts/signals/intent/product_launch.py` | ⬜ not built | TBD | `## Companies` |
| Job change | `scripts/signals/intent/job_change.py` | ⬜ not built | `RAPIDAPI_KEY` | `## LinkedIn` |
| Engagement | `scripts/signals/intent/engagement.py` | ⬜ not built | `RAPIDAPI_KEY` | `## LinkedIn` |
| Website visit | `scripts/signals/intent/website_visit.py` | ⬜ not built | Vendor — see below | n/a |

The Demo signal returns fabricated `[DEMO]`-prefixed data and calls no API. Use it only to verify the flow works — never present its output as real findings.

### Website visit is vendor-dependent

The other five signals are observable from public data. Website visit is not: it requires a tracking pixel on the user's own site plus a deanonymization vendor (RB2B, Vector, Clearbit Reveal, Leadfeeder). If the user asks for it and no vendor is configured, explain this plainly rather than attempting a workaround. Everything else in this skill works without it.

## The Six Signals

Definitions live in `context/signals/signals.md` — the user's own definitions there always win over what follows. This table is the default when that file is missing or thin.

| Signal | Strong instance | Weak instance | Suggested next action |
|---|---|---|---|
| **Hiring a role** | Opens a role that owns the problem you solve, at a company matching the ICP | Generic backfill, or a role unrelated to your buyer | Reach the hiring manager, not HR. Reference the gap the role admits. |
| **Website visit** | Repeat visits to pricing or case-study pages by an ICP-fit company | One-off homepage visit, or a non-ICP company | Warm outreach referencing the topic, never the visit itself |
| **Funding** | Raise at a stage where they build the function you serve | Large late-stage raise with no relevance to your offer | Wait 2-4 weeks, then reach the new function owner |
| **Engagement** | Same person engages repeatedly over a short window | Single passive reaction | Reply in-thread first; DM only after a second touch |
| **Product launch** | Target launches something needing the capability you provide | Minor changelog entry | Reference the launch as timing, not as flattery |
| **Job change** | Known contact moves into a buying seat at an ICP-fit company | Lateral move outside your buying centre | Congratulate early, pitch later — first 90 days is the window |

Two signals on the same company inside one week matter more than either alone. Always say so when you see it.

## Hard rules

- **NEVER run every signal by default.** Running all of them burns API quota and takes minutes.
- **ALWAYS ask which signals to check before running anything**, using AskUserQuestion with `multiSelect: true`. Offer only signals that are ✅ built AND whose section in `context/signals/watchlist.md` has at least one line.
- **The one exception:** the user already named the signals in their message ("any funding or hiring news?"). Then run exactly those and skip the question.
- If a requested signal is ⬜ not built, say so plainly and offer the built ones instead. **Never fabricate a result.**
- If a signal's required env key is missing from `.env`, exclude it from the options and tell the user which key it needs.
- Never present `[DEMO]` output as real. If a run returns demo data, say explicitly that it is placeholder output.
- A signal is not a qualified lead. Report what was observed and let the user decide — do not assert intent the data does not support.

## Step 1 — Ask Which Signals

Before running anything:

1. Read `context/signals/watchlist.md`. If it does not exist, stop and help the user create it from `watchlist-template.md`.
2. Check which sections have at least one line under them.
3. Check `.env` for each candidate signal's required key.
4. Ask with AskUserQuestion, `multiSelect: true`, listing only the signals that pass all three checks. In each option's description, note what that signal implies — e.g. "Strong: implies budget and an admitted gap".

Skip this step only when the user already named the signals.

## Step 2 — Run

One command per selected signal. Run independent signals in parallel:

```bash
python scripts/signals/intent/demo.py -d 7 -n 25
```

Flags every signal script accepts:

| Flag | Default | Description |
|---|---|---|
| `-d`, `--days` | 7 | Lookback window in days |
| `-n`, `--limit` | 25 | Max signals returned |
| `--dry-run` | off | Print the resolved watchlist and exit without fetching |

Run from the repo root — scripts resolve `.env` and `context/` relative to the working directory.

Each script prints JSON to stdout: `{"source", "signal_type", "count", "signals": [...]}`. Warnings and per-entity errors go to stderr; a failed entity does not stop the run. If a script exits non-zero, report what failed and continue with the signals that succeeded.

## Step 3 — Report

Read the JSON from every script and compose **one merged digest** — not one section per script. The JSON is for you, not the user; never paste it into chat.

Group by **company**, not by signal type. The user cares which accounts are heating up, not which script found what. Apply `## How to rank` from `context/signals/signals.md` for ordering, and check findings against `## ICP` in `brain/raw/me/offer.md`.

## Output (conversational — no file written)

This skill does NOT write a CSV. Present the findings in whatever shape fits what came back:

- A markdown table when several companies each have comparable signals
- Grouped bullets when one company has several signals worth unpacking
- Short prose when there are only one or two things worth saying

For each finding worth acting on, give the observation, why it matters, and the suggested next action. Keep the action concrete.

Always include the source URL so the user can verify. Say plainly when a run found nothing — do not pad. **Never invent a signal that was not in the JSON.**

## Adding a new signal

1. Copy `scripts/signals/intent/demo.py` to `scripts/signals/intent/<signal>.py`.
2. Update the header docstring, `SOURCE`, `SIGNAL_TYPE`, `WATCHLIST_SECTION`, and `REQUIRED_ENV`.
3. Rewrite `fetch_entry()` to call the real API. Leave the rest alone.
4. Flip that row to ✅ built in the table above and fill in its Requires column.

Each script is fully self-contained — stdlib only, no local imports. Duplicated helpers are intentional: nothing shared means nothing to break elsewhere.

## Next Step

```
Read skills/enrich-leads/SKILL.md and enrich the companies showing the strongest signals.
```
