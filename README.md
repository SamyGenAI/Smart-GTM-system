# GTM Starter Kit

AI-powered LinkedIn outreach system for B2B founders. Find leads, score them, enrich with personalized DM copy, and export a clean outreach list — all from the command line.

## Stack

- **EXA** — people and company discovery
- **Claude Haiku** — lead scoring and qualification
- **Claude Haiku + Web Search** — deep prospect enrichment and DM generation
- **RapidAPI (`linkedin-api8`)** — LinkedIn profile pull and post-engager extraction

## Workflow

```text
1) Setup profile, website, ICP          -> skills/setup
2) Find leads (EXA)                     -> skills/find-leads
3) Score leads (Haiku)                  -> skills/score-leads
4) Enrich leads (Haiku + Web Search)    -> skills/enrich-leads
5) Export outreach list (CSV)           -> skills/export-leads

Warm source path:
Post-engagers (RapidAPI)                -> skills/post-engagers -> skills/score-leads
```

## Quick Start

```
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]
```

Then follow the prompts. Setup takes 10-15 minutes and fills in your context files. Every other skill builds on top of that.

## Skills

| Skill | What it does |
|-------|-------------|
| `skills/setup/` | Onboards your company, ICP, positioning, and competitors into `context/` |
| `skills/find-leads/` | Searches EXA for people or companies matching a query |
| `skills/score-leads/` | Scores leads 0-100 against your ICP using Haiku |
| `skills/enrich-leads/` | Researches each lead and writes two personalized LinkedIn DMs |
| `skills/export-leads/` | Exports a clean, normalized outreach CSV |
| `skills/post-engagers/` | Pulls warm leads from your LinkedIn post reactions via RapidAPI |

## Context Files

Setup populates these files — they drive every downstream skill:

```
context/
├── brief/
│   ├── brief-template.md           <- structure reference (do not edit)
│   └── brief.md                    <- your offer + ICP, used by enrichment script
├── profile/
│   ├── profile-template.md
│   └── profile.md                  <- your LinkedIn profile + company details
├── icp-definition/
│   ├── icp-definition-template.md
│   └── icp-definition.md           <- tier definitions + qualification framework
├── positioning/
│   ├── positioning-template.md
│   └── positioning.md              <- value pillars + messaging matrix
└── competitor-radar/
    ├── competitor-radar-template.md
    └── competitor-radar.md         <- battlecards + win/loss patterns
```

The `*-template.md` files are committed and distributed with the repo. The adapted `*.md` files are gitignored — they contain your data and never leave your machine.

## Environment

Copy `.env.example` to `.env` and fill in the keys you use:

```
ANTHROPIC_API_KEY=   # required for scoring and enrichment
EXA_API_KEY=         # required for find-leads
RAPIDAPI_KEY=        # optional, for setup profile pull and post-engagers
```

## License

MIT
