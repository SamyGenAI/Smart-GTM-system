---
name: export-leads
description: Export final leads list to a clean CSV.
---

# Skill: Export Leads

## Purpose

Create one final CSV for outreach.

## Output Path

`outputs/[date]-[campaign]-leads.csv`

## Columns

`lead_id,name,company,title,linkedin_url,score,tier,dm_angle,personalization_hook,source`

## Rules

1. Keep all rows (including `exclude`)
2. Empty values stay empty, not `null`
3. UTF-8 CSV

## Run Summary

```
Export complete.
CSV: outputs/[date]-[campaign]-leads.csv
Rows: {N}
```
