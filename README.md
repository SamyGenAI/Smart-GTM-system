# GTM Starter Kit

Built by [The Revenue Architects](https://www.the-revenue-architects.com) — a GTM engineering firm based in San Francisco. We work with growth-stage B2B SaaS companies to design and build their revenue systems: signal infrastructure, CRM architecture, data pipelines, AI-powered workflows, and the operational layer that connects them.

This repo is the open-source version of what we build with clients. Clone it, fill in your context files once, and run AI-powered GTM tasks from a single prompt — no rebuilding context every session.

---

## How It Works

Claude Code reads `CLAUDE.md` automatically at the start of every session. That file contains your company overview, ICP, signals, personas, and current priorities. Once it's filled in, you can run any task with a one-line prompt — no re-explaining your context each time.

```
Read skills/account-research/SKILL.md and research stripe.com
```

Claude reads your ICP, signals, and personas from the repo and produces a full account research brief. You didn't paste any context. It was already there.

---

## What's Inside

```
gtm-starter-kit/
│
├── CLAUDE.md                           ← Fill this in first. Claude reads it every session.
│
├── context/                            ← Your GTM institutional knowledge
│   ├── profile.md                      ← Company overview, product, team, reference customers
│   ├── icp-definition.md              ← ICP tiers, filters, anti-ICP, qualification criteria
│   ├── signal-library.md              ← Signals with scoring, detection methods, hooks
│   ├── positioning.md                 ← Value pillars, competitive positioning, what not to say
│   ├── competitor-radar.md            ← Battlecards, win/loss patterns
│   └── personas/
│       └── template.md                ← Persona template — duplicate for each buyer role
│
├── skills/                             ← Claude executes these. One-line prompts.
│   ├── setup/SKILL.md                 ← Run first. Provide domain → repo auto-populated.
│   ├── account-research/SKILL.md      ← Deep company research (EXA primary, WebSearch fallback)
│   ├── people-research/SKILL.md       ← Deep person research (EXA primary, WebSearch fallback)
│   ├── post-engagers/SKILL.md  ← Source leads from reactors on your own LinkedIn posts
│   ├── icp-scoring/SKILL.md           ← Score accounts against your ICP, assign tiers
│   ├── lead-enrichment/SKILL.md       ← Enrich approved leads: LinkedIn + email/phone + signals
│   ├── lead-sequence/SKILL.md         ← Write per-lead DM/email sequences from the enriched list
│   ├── export-list/SKILL.md           ← Export final list to CSV (always) + Notion (optional)
│   └── signal-to-sequence/SKILL.md    ← Campaign-scale: one signal across many accounts
│
├── .env.example                        ← Copy to .env and fill in provider keys
│
└── outputs/                            ← All skill outputs land here
    ├── scoring/                        ← ICP scoring outputs
    └── campaigns/                      ← Campaign briefs and sequences
```

---

## Getting Started in 3 Steps

### Step 1: Clone and open

```bash
git clone https://github.com/KarlRaf/gtm-starter-kit.git
cd gtm-starter-kit
claude .
```

---

### Step 2: Run setup with your domain (15–30 min)

```
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]
```

Claude researches your company — website, Crunchbase, LinkedIn, G2, job postings — and writes every context file immediately from public data. No questions asked upfront. You see the repo populate in real time.

When it's done, it shows you what was filled and what was inferred — then offers a 3-minute refinement pass (5 questions) to replace inferred fields with your actual win patterns, ACV range, and signals. Optional. The repo works either way.

---

### Step 3: Run your first skill

```
Read skills/account-research/SKILL.md and research [company.com]
```

Your context is already there. Claude knows your ICP, your signals, your personas. The output is a full research brief — not a generic summary.

**Other skills to run next:**
```
# Research a person (founder, stakeholder)
Read skills/people-research/SKILL.md and research [LinkedIn URL]

# Score a list against your ICP
Read skills/icp-scoring/SKILL.md and score these companies: [paste list]

# Enrich approved leads
Read skills/lead-enrichment/SKILL.md and enrich outputs/[date]-scored.csv

# Build a campaign from a signal
Read skills/signal-to-sequence/SKILL.md.
Build a Tier 2 campaign for accounts triggering [signal name]. Target [persona].
```

All outputs land in `outputs/` — see the naming convention below.

---

## Workflow

End-to-end, one skill per step:

```
1. ICP definition                    →  context/icp-definition.md   (manual, editable)
2. Find leads matching ICP           →  skills/people-research  +  skills/account-research
   Or source from your own audience  →  skills/post-engagers (optional)
3. Score the leads                   →  skills/icp-scoring
4. Enrich approved leads             →  skills/lead-enrichment
5. Write per-lead DM / email sequences → skills/lead-sequence
6. Export list (CSV always, Notion optional) → skills/export-list
```

### Data providers

| Provider | Used by | What it does | Credential |
|---|---|---|---|
| **EXA** (MCP) | people-research, account-research | Company + people discovery with `web_search_advanced_exa`. Falls back to built-in web search if MCP not connected. | MCP connection |
| **RapidAPI** (`linkedin-api8`) | lead-enrichment | LinkedIn profile scrape — headline, positions, followers, posts | `RAPIDAPI_KEY` |
| **Orthogonal** (`@orth/cli`) | lead-enrichment | Email and phone discovery via the `orthogonal/lead-enrichment` sub-skill | `ORTHOGONAL_API_KEY` + `orth` CLI installed |
| **Crustdata** | lead-enrichment | Person enrichment (`/person/enrich`), company resolution by domain (`/company/search`), job-posting signals (`/job/search`) | `CRUSTDATA_API_KEY` |
| **Notion** (MCP, optional) | export-list | Upsert the final list into a master Notion database | MCP connection |

Each skill uses a **Step 0 detection pattern**: check which providers are configured, pick the path up front, stamp the choice in the output. Missing providers degrade gracefully — the skill never hard-fails on a missing credential, it just leaves those fields null and notes the skip.

### Credential setup

```bash
cp .env.example .env
# fill in RAPIDAPI_KEY, CRUSTDATA_API_KEY, ORTHOGONAL_API_KEY as you acquire them
```

`.env` is gitignored. Missing keys are fine — `lead-enrichment` runs on whichever subset you've configured.

---

## Output Naming Convention

```
outputs/YYYY-MM-DD-[type]-[name].md

Examples:
outputs/2024-03-15-research-northstar-analytics.md
outputs/2024-03-01-scoring-q1-prospect-list.md
outputs/campaigns/2024-03-01-series-b-revops-tier2/brief.md
```

---

## Keeping It Current

| Cadence | What to update |
|---------|---------------|
| After every win/loss | Update `context/competitor-radar.md` win/loss patterns |
| Quarterly | Review `context/icp-definition.md` — add an entry to the ICP evolution log |

---

## What Not to Put in This Repo

- **CRM data or contact lists** — never commit customer or prospect data to git
- **API keys or credentials** — use environment variables, never hardcode
- **Raw meeting transcripts** — summarize and synthesize into the relevant context file
- **Pricing** — keep commercial terms out of the repo

---

## License

MIT
