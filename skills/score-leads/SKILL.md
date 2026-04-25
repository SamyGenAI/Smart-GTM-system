---
name: score-leads
description: Score and qualify leads with Claude Haiku API.
---

# Skill: Score Leads

## Model

- Claude Haiku API

## Input

- Lead list from `skills/find-leads` or `skills/post-engagers`
- Context files (for now): `context/icp-definition.md`, `context/positioning.md`

## Output Contract (strict)

For each lead, return:

- `score` (0-100)
- `tier` (`tier1`, `tier2`, `tier3`, `exclude`)
- `qualification_reason`
- `disqualifier_flags` (array)
- `dm_angle`

## Tier Mapping

- 80-100 -> `tier1`
- 60-79 -> `tier2`
- 40-59 -> `tier3`
- 0-39 -> `exclude`

## Required Table

| Name | Company | Score | Tier | DM Angle | Reason |
|------|---------|-------|------|----------|--------|

## Next Step

```
Read skills/enrich-leads/SKILL.md and run deep research with Claude Web Search (Sonnet) for tier1/tier2.
```
