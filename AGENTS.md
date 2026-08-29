# AGENTS.md

Persistent GTM context for this repo. Full details live in `context/`.

> **New user?** Run setup first:
> `Read skills/setup/SKILL.md and set up this repo for [your-domain.com]`

## Company

**[YOUR_COMPANY]** helps [who] do [what outcome].

GTM motion: [e.g. founder-led LinkedIn outreach]
Primary channel: [e.g. LinkedIn DM]
Core offer: [e.g. premium content + qualified founder conversations]

## Stack

- **EXA**: lead + company discovery
- **Codex Haiku**: lead scoring and qualification
- **Codex Haiku**: deep prospect enrichment (with web search)
- **RapidAPI (`linkedin-api8`)**: setup profile extraction and post-engagers extraction
- **Python (stdlib only)**: signal watching scripts in `scripts/signals/`

## Workflow

```text
1) Setup profile, website URL, and LinkedIn URL         -> skills/setup
2) Find leads with EXA                    -> skills/find-leads
3) Score leads with Codex Haiku          -> skills/score-leads
4) Enrich leads with Haiku + Web Search   -> skills/enrich-leads
5) Export outreach list CSV               -> skills/export-leads

Warm source path:
RapidAPI post engagers -> skills/post-engagers -> skills/score-leads

Signal watching path (runs on its own, reports in chat):
context/signals/watchlist.md -> skills/social-listening
context/signals/watchlist.md -> skills/intent-signals
```

## Quick Commands

```text
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]

Read skills/find-leads/SKILL.md and find 25 Tier 1 leads in [your target geography/segment]

Read skills/score-leads/SKILL.md and score this lead list with Codex Haiku

Read skills/post-engagers/SKILL.md and pull engagers from my last 10 posts

Read skills/enrich-leads/SKILL.md and enrich tier1/tier2 leads with Haiku web research

Read skills/export-leads/SKILL.md and export outputs/[date]-[campaign]-leads.csv

Read skills/social-listening/SKILL.md and check what my watchlist has been posting this week

Read skills/intent-signals/SKILL.md and check buying signals for my watchlist
```

## Signals

Two separate context files, copied from their `-template.md` siblings:

- `context/signals/watchlist.md` — WHO to watch. One line per entity,
  `Name: handle`, grouped by platform. Reddit is just `r/subreddit`.
  Read directly by the scripts.
- `context/signals/signals.md` — WHAT counts as a signal and how to rank it.
  Read by the skills, not the scripts. Optional but sharpens results.

Listening runs from one script, `scripts/signals/social-listening.py`,
with `--source linkedin` (Apify, bills per post), `--source x` (xAI Grok
`x_search`, one call per run), or `--source reddit` (keyless RSS + arctic-shift
scores + shreddit comments; free, but paced ~2s per request so a multi-subreddit
run takes a couple of minutes). All three return real engagement counts and sort
by them. Intent sources live in `scripts/signals/intent/`.

Both skills ALWAYS ask which sources to run before running anything. They
never run every source by default, and they report conversationally in chat
rather than writing a CSV.

## Current Priorities

- [Your top GTM priority this quarter]
- [Second priority]
- [Third priority]
