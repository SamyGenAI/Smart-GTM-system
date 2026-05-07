# CLAUDE.md

Persistent GTM context for this repo. Full details live in `context/`.

## Company

**Igentiv** helps B2B founders build a premium LinkedIn presence and generate qualified leads.

GTM motion: founder-led LinkedIn outreach  
Primary channel: LinkedIn DM  
Core offer: premium content + qualified founder conversations

## Stack

- **EXA**: lead + company discovery
- **Claude Haiku**: lead scoring and qualification
- **Claude Haiku**: deep prospect enrichment (with web search)
- **RapidAPI (`linkedin-api8`)**: setup profile extraction and post-engagers extraction

## Workflow

```text
1) Setup profile, website URL, and LinkedIn URL         -> skills/setup
2) Find leads with EXA                    -> skills/find-leads
3) Score leads with Claude Haiku          -> skills/score-leads
4) Enrich leads with Haiku + Web Search   -> skills/enrich-leads
5) Export outreach list CSV               -> skills/export-leads

Warm source path:
RapidAPI post engagers -> skills/post-engagers -> skills/score-leads
```

## Quick Commands

```text
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]

Read skills/find-leads/SKILL.md and find 25 Tier 1 leads in EU/US B2B

Read skills/score-leads/SKILL.md and score this lead list with Claude Haiku

Read skills/post-engagers/SKILL.md and pull engagers from my last 10 posts

Read skills/enrich-leads/SKILL.md and enrich tier1/tier2 leads with Haiku web research

Read skills/export-leads/SKILL.md and export outputs/[date]-[campaign]-leads.csv
```

## Current Priorities

- Build first 150 Tier 1 LinkedIn leads
- Score and prioritize with Haiku
- Send personalized DMs
