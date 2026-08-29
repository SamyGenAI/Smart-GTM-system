# CLAUDE.md

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
- **Claude Haiku**: lead scoring and qualification
- **Claude Haiku**: deep prospect enrichment (with web search)
- **RapidAPI (`linkedin-api8`)**: setup profile extraction and post-engagers extraction
- **Apify (`supreme_coder/linkedin-post`)**: LinkedIn post listening (bills per post)
- **xAI Grok (`x_search`)**: X/Twitter listening + free-text X research
- **yt-dlp**: YouTube listening — search, channels, transcripts, comments (free, keyless)
- **Web search**: harness-native search first, then Brave/EXA/Serper/Parallel by key, then keyless DuckDuckGo/Startpage
- **Gmail connector (MCP)**: read-only newsletter digest — no script, no key
- **Python (stdlib only)**: signal watching scripts in `scripts/signals/`

## Workflow

```text
1) Setup profile, website URL, and LinkedIn URL         -> skills/setup
2) Find leads with EXA                    -> skills/find-leads
3) Score leads with Claude Haiku          -> skills/score-leads
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

Read skills/score-leads/SKILL.md and score this lead list with Claude Haiku

Read skills/post-engagers/SKILL.md and pull engagers from my last 10 posts

Read skills/enrich-leads/SKILL.md and enrich tier1/tier2 leads with Haiku web research

Read skills/export-leads/SKILL.md and export outputs/[date]-[campaign]-leads.csv

Read skills/social-listening/SKILL.md and check what my watchlist has been posting this week

Read skills/social-listening/SKILL.md and search X for what people say about [topic]

Read skills/social-listening/SKILL.md and check Reddit for what people say about [topic]

Read skills/social-listening/SKILL.md and check YouTube for what people say about [topic]

Read skills/social-listening/SKILL.md and check the web for what people say about [topic]

Read skills/social-listening/SKILL.md and digest this week newsletters from Gmail

Read skills/intent-signals/SKILL.md and check buying signals for my watchlist
```

## Signals

Two separate context files, copied from their `-template.md` siblings:

- `context/signals/watchlist.md` — WHO to watch. One line per entity,
  `Name: handle`, grouped by platform. Reddit is just `r/subreddit`; YouTube
  takes `Name: @handle` or a channel URL; Web takes `Name: domain.com`; Gmail
  takes just the newsletter's name.
  Read directly by the scripts.
- `context/signals/signals.md` — WHAT counts as a signal and how to rank it.
  Read by the skills, not the scripts. Optional but sharpens results.

Listening runs from one script, `scripts/signals/social-listening.py`,
with `--source linkedin` (Apify, bills per post), `--source x` (xAI Grok
`x_search`, one call per run), `--source reddit` (keyless RSS + arctic-shift
scores + shreddit comments; free, but paced ~2s per request so a multi-subreddit
run takes a couple of minutes), `--source youtube` (yt-dlp; free and keyless,
but needs `pip install yt-dlp` — searches topics or watched channels and pulls
transcripts + top comments), or `--source web` (Brave/EXA/Serper/Parallel when
a key is set, else a free keyless DuckDuckGo/Startpage floor). The first three
return real engagement counts and sort by them; **YouTube and Web sort by date,
newest first**, since an old video or page is not a signal.

**Gmail is the one source with no script.** It runs through the Gmail MCP
connector, strictly read-only — search and read, never send, label or delete.
Free, no key: authorize the connector in claude.ai settings. `## Gmail` holds
newsletter **names**, not addresses — Claude resolves each to its real sending
addresses at run time, catching the several a writer with multiple publications
uses. It reads only those plus the promotions/updates categories, so the primary
inbox — personal and client mail — is never in scope. Sorted by
date, newest first, since a newsletter has no engagement count, and reported as
one line per issue rather than per story.

Intent sources live in `scripts/signals/intent/`.

The web source is the bottom two rungs of a three-rung ladder: the agent's own
web search tool comes first when it has one, since a script cannot call it.
See `skills/social-listening/SKILL.md`.

Both skills ALWAYS ask which sources to run before running anything. They
never run every source by default, and they report conversationally in chat
rather than writing a CSV.

## Current Priorities

- [Your top GTM priority this quarter]
- [Second priority]
- [Third priority]
