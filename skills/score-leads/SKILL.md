---
name: score-leads
description: Score and qualify leads with Claude Haiku API. CSV-only output.
---

# Skill: Score Leads

## Model

- Claude Haiku (`claude-haiku-4-5-20251001`)

## Input

Any of the following CSV sources (the script auto-normalizes LinkedIn export columns):

- Pipeline output from `skills/find-leads` (`outputs/`)
- LinkedIn Connections export → drop in `inputs/connections/`
- Post-engagers export → drop in `inputs/post-engagers/`

Context files: `context/icp-definition.md`, `context/positioning.md`

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
# Pipeline output
node scripts/score_leads_haiku.mjs \
  -i outputs/2026-04-26-leads.csv \
  -o outputs/2026-04-26-leads-scored.csv \
  -b 8

# LinkedIn connections export
node scripts/score_leads_haiku.mjs \
  -i inputs/connections/my-connections.csv \
  -o outputs/connections-scored.csv \
  -b 8

# Post-engagers export
node scripts/score_leads_haiku.mjs \
  -i inputs/post-engagers/engagers.csv \
  -o outputs/engagers-scored.csv \
  -b 8
```

## Next Step

```
Read skills/enrich-leads/SKILL.md and run deep research with Claude Web Search (Sonnet) for tier1/tier2 leads.
```
