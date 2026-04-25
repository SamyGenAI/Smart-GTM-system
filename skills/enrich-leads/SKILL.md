---
name: enrich-leads
description: Enrich qualified leads using Claude Web Search with Sonnet.
---

# Skill: Enrich Leads

## Model + Source

- Sonnet model
- Claude Web Search API

## Purpose

Do deeper research for qualified leads (`tier1`/`tier2`) and produce personalization-ready context.

## Input

- Scored leads from `skills/score-leads`
- Optional user constraints (region, vertical, competitor focus)

## Output Per Lead

- `company_summary` (1-2 lines)
- `person_summary` (1-2 lines)
- `recent_signals` (3 bullets max)
- `personalization_hook` (1 sentence)
- `risk_notes` (optional)

## Rule

- Keep it concise and outreach-ready
- Skip heavy biographies
- Prefer recent public signals over generic descriptors

## Next Step

```
Read skills/export-leads/SKILL.md and export the final outreach list.
```
