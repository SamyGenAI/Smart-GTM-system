---
name: find-leads
description: Search for people or companies matching a query using EXA. Use to build a prospect list, find ICP-matching leads, or discover companies in a target segment. Requires EXA_API_KEY. Triggers on /find-leads or any message like "find leads", "find companies", "build a prospect list", or "search for [type of person/company]".
---

# Skill: Find Leads

Read `## ICP` in `brain/raw/me/offer.md` before choosing the query. Do not copy that section into this repo. The script searches the query only.

Paid call: print the estimate, wait for approval, then add `--confirm`.

## Quick Start

```bash
node scripts/find_leads_exa.mjs -q "founders who want time off the screen" -n 25 --estimate
node scripts/find_leads_exa.mjs -q "founders who want time off the screen" -n 25 --confirm
```

## Purpose

Find leads or companies from one query with EXA.  
Category is auto-detected from the query, or forced with `-c people|company`.

## Required Env

- `EXA_API_KEY`

## Commands

People/company auto:

```bash
node scripts/find_leads_exa.mjs -q "founders who want time off the screen" -n 25 --estimate
```

Force company:

```bash
node scripts/find_leads_exa.mjs -q "creator businesses that sell a high-ticket offer" -c company -n 25 --confirm
```

Write CSV:

```bash
node scripts/find_leads_exa.mjs -q "founders who want time off the screen" -n 25 --confirm -o outputs/2026-04-25-find-leads.csv
```

## Output

Script prints JSON to stdout:

- `query`
- `category` (`people` or `company`)
- `count`
- `rows[]` with `title`, `url`, `snippet`, `highlights`

Optional CSV output columns:

`rank,category,query,title,url,snippet,highlights`

## Next Step

```
Read skills/score-leads/SKILL.md and score this list with Claude Haiku API.
```
