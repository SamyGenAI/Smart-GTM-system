---
name: find-leads
description: Search for people or companies matching a query using EXA. Use to build a prospect list, find ICP-matching leads, or discover companies in a target segment. Requires EXA_API_KEY. Triggers on /find-leads or any message like "find leads", "find companies", "build a prospect list", or "search for [type of person/company]".
---

# Skill: Find Leads

## Quick Start

```bash
node scripts/find_leads_exa.mjs -q "B2B AI founders in San Francisco" -n 25 -o outputs/find-leads.csv
```

## Purpose

Find leads or companies from one query with EXA.  
Category is auto-detected from the query, or forced with `-c people|company`.

## Required Env

- `EXA_API_KEY`

## Commands

People/company auto:

```bash
node scripts/find_leads_exa.mjs -q "B2B AI founders in San Francisco" -n 25
```

Force company:

```bash
node scripts/find_leads_exa.mjs -q "B2B AI startups in San Francisco" -c company -n 25
```

Write CSV:

```bash
node scripts/find_leads_exa.mjs -q "B2B AI founders in San Francisco" -n 25 -o outputs/2026-04-25-find-leads.csv
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
