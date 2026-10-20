---
name: score-leads
description: Score and qualify a lead CSV against the ICP using Claude Haiku. Appends a score (0-100) and why_match column to the input CSV. Works with pipeline output, LinkedIn connections exports, and post-engager CSVs. Requires ANTHROPIC_API_KEY. Triggers on /score-leads or any message like "score these leads", "qualify this list", or "run scoring".
---

# Skill: Score Leads

## Model

- Claude Haiku (`claude-haiku-4-5-20251001`)

## Input

Any of the following CSV sources (the script auto-normalizes LinkedIn export columns):

- Pipeline output from `skills/find-leads` (`outputs/`)
- LinkedIn Connections export → drop in `inputs/connections/`
- Post-engagers export → drop in `inputs/post-engagers/`

ICP source: `brain/raw/me/offer.md` headings `## ICP`, `## Anti-ICP`, `## Positioning`. Optional `## Geography`, `## Buyer`, `## Scoring`. See `context/README.md`. Do not keep a local copy.

## Output Contract (strict)

The script appends two new columns to the existing input CSV:

- `score` (0-100, integer)
- `why_match` — short sentence explaining concretely why this lead matches (or does not match) the ICP. Header in spreadsheets: **"Why it's a match"**.

No JSON output. CSV only.

`why_match` must NOT contain outreach copy, DM angles, or pitches. That is produced in `skills/enrich-leads`.

## Tier Mapping (derived from score, not stored in CSV)

- 80-100 -> `tier1`
- 60-79 -> `tier2`
- 40-59 -> `tier3`
- 0-39 -> `exclude`

## Quick Start

```bash
# Estimate first. Add --confirm only after approval.
node scripts/score_leads_haiku.mjs \
  -i outputs/2026-04-26-leads.csv \
  -o outputs/2026-04-26-leads-scored.csv \
  -b 8 \
  --estimate

# LinkedIn connections export (same --estimate, then --confirm)
node scripts/score_leads_haiku.mjs \
  -i inputs/connections/my-connections.csv \
  -o outputs/connections-scored.csv \
  -b 8 \
  --estimate

# Post-engagers export
node scripts/score_leads_haiku.mjs \
  -i inputs/post-engagers/engagers.csv \
  -o outputs/engagers-scored.csv \
  -b 8 \
  --estimate
```

## Next Step

```
Read skills/enrich-leads/SKILL.md and run deep research with Claude Web Search (Sonnet) for tier1/tier2 leads.
```
