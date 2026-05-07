---
name: export-leads
description: Export final enriched leads to a clean CSV ready for Notion or CRM.
---

# Skill: Export Leads

## Purpose

Take any enriched CSV and produce one clean, normalized outreach list.

## Quick Start

```bash
node scripts/export_leads.mjs \
  -i outputs/[date]-leads-enriched.csv \
  -c [campaign-name]
```

## Options

| Flag | Default | Description |
|---|---|---|
| `-i` / `--input` | required | Enriched CSV from `enrich_leads_haiku.mjs` |
| `-o` / `--out` | `outputs/[date]-[campaign]-leads.csv` | Output path |
| `-s` / `--min-score` | `0` (all rows) | Only export leads at or above this score |
| `-c` / `--campaign` | `leads` | Label used in the output filename |

## Output Columns

`lead_id, name, headline, linkedin_url, score, tier, why_match, outreach_angle, dm_sequence_1, dm_sequence_2, source`

- `tier` is auto-derived from `score` (80-100 → tier1, 60-79 → tier2, 40-59 → tier3, 0-39 → exclude)
- Works with all upstream sources: find-leads, connections, post-engagers

## Run Summary

```
Export complete.
CSV  : outputs/[date]-[campaign]-leads.csv
Rows : {N}
```
