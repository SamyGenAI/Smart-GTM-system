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
│   ├── account-research/SKILL.md      ← Deep research on any account before outreach
│   ├── signal-to-sequence/SKILL.md    ← Turn a signal into LinkedIn DM outreach
│   └── icp-scoring/SKILL.md          ← Score accounts against your ICP, assign tiers
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
# Score a list against your ICP
Read skills/icp-scoring/SKILL.md and score these companies: [paste list]

# Build a campaign from a signal
Read skills/signal-to-sequence/SKILL.md.
Build a Tier 2 campaign for accounts triggering [signal name]. Target [persona].
```

All outputs land in `outputs/` — see the naming convention below.

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
