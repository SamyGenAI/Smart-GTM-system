# Skill: Account Research

**Duration:** 20–40 minutes per account
**Output:** `outputs/[date]-[account]-research.md`

---

## Quick Start

```
Read skills/account-research/SKILL.md and research [company.com]
```

That's it. Claude will read your ICP, signals, and competitor context automatically and produce a structured research brief. See `examples/sample-company/outputs/2024-03-15-research-northstar-analytics.md` for what the output looks like.

---

## Purpose

Build a complete intelligence brief on a target account before any outreach. The goal is not a company summary you could get from their About page. The goal is to find the specific trigger — the moment, the hire, the product shift, the funding event — that makes this the right time to reach out, and the right angle to use.

---

## When to Run This Skill

- Before any Tier 1 outreach (always)
- Before a discovery call (refresh if research is older than 2 weeks)
- When a signal fires and you need to build a personalized first touch
- When an account enters the pipeline and the AE needs full context

---

## Inputs

- Account name and domain
- `context/icp-definition.md` — to score fit
- `context/signal-library.md` — to check for active signals
- `context/competitor-radar.md` — to flag competitive context
- `context/personas/` — to identify the right stakeholders

---

## Data Source Priority

**Step 0 — Detect EXA availability (do this before any search).**

Check whether `web_search_advanced_exa` is present in the available tool list for this session.
- If **yes** → use EXA path for the whole run.
- If **no** → use WebSearch path for the whole run. Do not attempt `web_search_advanced_exa` — the call will fail. Optionally tell the user: "EXA MCP is not connected — falling back to web search. Connect EXA for richer company metadata."

Note the chosen path at the top of the output file: `Data source: EXA` or `Data source: WebSearch (EXA not connected)`.

**EXA path** (via `web_search_advanced_exa`)
- **Only** use `web_search_advanced_exa`. Never `web_search_exa` or other Exa tools.
- **Never** run Exa searches in the main context. Spawn a Task/Agent subagent per search. The subagent runs the search, processes results, and returns compact JSON or brief markdown.
- **Tune numResults** to intent: "a few" → 10–20, "comprehensive" → 50–100, specific number → match it.
- **Generate 2–3 query variations** and run in parallel for coverage, then dedupe.
- **Category choice:**
  - `company` → homepage, headcount, location, funding, revenue (use for Step 1 snapshot)
  - `news` → press coverage, funding announcements, product launches (use for Step 1 + Step 3)
  - `people` → public LinkedIn profiles (use for Step 2 stakeholder map)
  - no category (`type: "auto"` or `"deep"`) → tech stack, blogs, competitor mentions, broader context
- **Category restrictions:**
  - `category: "company"` → no `includeDomains`/`excludeDomains`, no date filters
  - `includeText` / `excludeText` → single-item arrays only, across all categories
  - `category: "news"` and no-category → date filters and domain filters work

**WebSearch path** (via built-in `WebSearch`)
- Target queries at the specific sources you want: `site:crunchbase.com`, `site:linkedin.com/company`, `site:linkedin.com/in`, `site:builtwith.com`, company blog, changelog URLs.
- Spawn a subagent per search for token isolation, same as the EXA path.

**Mid-run fallback:** if the chosen path returns 0 useful results for a specific query, switch that single query to the other path and note it inline. Do not silently retry the same tool.

**Auth-gated content** (private LinkedIn sections, paid Crunchbase, paid news) → Claude in Chrome, regardless of path.

---

## Research Steps

### Step 1: Company Snapshot (5 min)

Pull the basics. Don't stop here — this is table stakes.

- **Funding history:** Last round, amount, date, lead investors. Calculate months since last raise.
- **Headcount and growth:** Current size, growth rate over last 12 months. Is it accelerating?
- **Recent hires:** What roles have they added in the last 90 days? Especially in GTM, ops, data, or the function your product serves.
- **Product updates:** Recent changelog, press releases, or product announcements. Are they expanding into an area relevant to your product?
- **Tech stack:** What tools are they using? Identify integration opportunities and displacement signals.

Sources: LinkedIn, Crunchbase, BuiltWith, their own blog and changelog.

EXA query shapes:
```
web_search_advanced_exa {
  "query": "[Company] headcount funding revenue",
  "category": "company",
  "numResults": 10,
  "type": "auto"
}
```
```
web_search_advanced_exa {
  "query": "[Company] funding round announcement",
  "category": "news",
  "numResults": 10,
  "startPublishedDate": "[today minus 18 months]"
}
```

---

### Step 2: Stakeholder Map (10 min)

Identify the 2–3 people to reach. Reference `context/personas/` for titles and roles to target.

For each stakeholder:
- Full name and current title
- Time in role (shorter tenure = more likely to be making changes)
- Recent activity: LinkedIn posts, conference talks, published content — what are they thinking about?
- Mutual connections or shared context (alumni, past companies, investors in common)
- Best channel based on their activity patterns

EXA query shape:
```
web_search_advanced_exa {
  "query": "[Title] [Company] LinkedIn",
  "category": "people",
  "numResults": 15
}
```

For deeper per-person research, hand off to `skills/people-research/SKILL.md`.

---

### Step 3: Signal Check (5 min)

Reference `context/signal-library.md`. For each Tier 1 and Tier 2 signal:

- Is this signal present for this account?
- When did it fire?
- What's the current signal score?

If score ≥ 60: outreach should go out within 48 hours.
If score < 40: note the gap and flag what would change the picture.

---

### Step 4: Competitive Context (5 min)

Reference `context/competitor-radar.md`.

- Is there any evidence they use a competitor? (Job postings, tech stack, content)
- If yes: which competitive angle applies?
- Are they evaluating alternatives? (Job postings for vendor evaluation, RFP language on LinkedIn)

EXA query shape (no category — enables date + domain filters):
```
web_search_advanced_exa {
  "query": "[Company] [competitor name]",
  "numResults": 15,
  "type": "auto",
  "startPublishedDate": "[today minus 12 months]"
}
```

---

### Step 5: The Angle (10 min)

This is the only thing that matters. Everything above was research. This step is judgment.

Answer these questions:

1. **Why now?** What's the specific event or condition that makes this the right moment to reach out? If you can't answer this, don't reach out yet.

2. **Why us?** What's the specific capability or outcome that maps to their current situation — not our general value prop, but the specific thing they need right now?

3. **What's the hook?** The first line of the email. It should reference something specific — a recent hire, a product move, a funding event — and connect it to a relevant insight. Not "I saw you raised Series B." Something they'd actually want to read.

4. **Who leads?** Which stakeholder gets the first touch, and in what channel?

---

## Output Format

```markdown
# Account Research: [Company Name]
Date: [YYYY-MM-DD]
Researched by: [Claude / Name]
Signal score: [X/100]
Recommended action: [Immediate outreach / Sequence / Monitor / Skip]

## Company Snapshot
[2–3 sentences: what they do, stage, recent momentum]

## Funding & Growth
- Last round: [Amount, Date, Lead]
- Headcount: [X, growth rate]
- Key recent hires: [Roles, dates]

## Tech Stack
- [Tools identified]
- Integration opportunities: [List]
- Displacement signals: [List]

## Stakeholder Map
| Name | Title | Tenure | Reach via | Notes |
|------|-------|--------|-----------|-------|
| [Name] | [Title] | [X months] | [Channel] | [Key context] |

## Active Signals
| Signal | Status | Fired | Score contribution |
|--------|--------|-------|-------------------|
| [Signal] | Active/Inactive | [Date] | +[X] pts |

## Competitive Context
[Any competitor usage or evaluation signals]

## The Angle
**Why now:** [Specific trigger]
**Why us:** [Specific fit]
**Hook:** [Proposed first line]
**Recommended sender:** [Name / Role]

## Suggested Next Action
[Specific: which sequence, which template, which stakeholder, which channel]
```

---

## Quality Check

Before filing the output, confirm:

- [ ] The "why now" is specific — a datable event or observable condition, not a generic assumption
- [ ] The stakeholder map has at least 2 people with contact info
- [ ] Signal score is calculated and recorded
- [ ] The hook would make sense to someone who doesn't know our product
- [ ] Competitive context has been checked
- [ ] The data source chosen at Step 0 (EXA or WebSearch) is noted at the top of the output
