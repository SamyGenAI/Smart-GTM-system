# GTM Starter Kit

This repo is optimized for one thing: LinkedIn outreach with minimal moving parts.

## Stack

- EXA API for people/company search
- Claude Haiku API for scoring
- Claude Web Search API with Sonnet for deep enrichment
- RapidAPI (`linkedin-api8`) for setup profile pull + post-engagers

## Workflow

```text
1) Setup                              -> skills/setup
2) Find leads (EXA)                   -> skills/find-leads
3) Score leads (Haiku)                -> skills/score-leads
4) Enrich leads (Web Search + Sonnet) -> skills/enrich-leads
5) Export leads (CSV)                 -> skills/export-leads

Optional warm-source:
post-engagers (RapidAPI)              -> skills/post-engagers
```

## Quick Start

```text
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]
Read skills/find-leads/SKILL.md and find 25 Tier 1 leads
Read skills/score-leads/SKILL.md and score this list with Claude Haiku
Read skills/enrich-leads/SKILL.md and enrich tier1/tier2 with Sonnet web research
Read skills/export-leads/SKILL.md and export the final CSV
```

## Skills

- `skills/setup/` - onboarding and LinkedIn profile bootstrap
- `skills/find-leads/` - EXA people/company search
- `skills/score-leads/` - Haiku scoring contract
- `skills/enrich-leads/` - Sonnet web-search enrichment
- `skills/export-leads/` - final CSV export
- `skills/post-engagers/` - RapidAPI warm lead extraction

## Environment

Copy `.env.example` to `.env` and fill what you use.

## License

MIT
