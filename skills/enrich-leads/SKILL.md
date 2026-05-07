---
name: enrich-leads
description: Research scored leads with Claude Haiku + Web Search and write two personalized LinkedIn DMs per lead. Only processes leads at or above a score threshold (default 60). Appends outreach_angle, dm_sequence_1, dm_sequence_2 columns. Requires ANTHROPIC_API_KEY and context/brief/brief.md. Triggers on /enrich-leads or any message like "enrich leads", "write DMs", "research these prospects", or "add outreach copy".
---

# Skill: Enrich Leads

Generic skill: works for any company. Company specifics are loaded at runtime from a SHORT `context/brief/brief.md` (offer + ICP only, max ~150 words). The long `positioning.md` and `icp-definition.md` files are NOT sent to the API.

## Model + Source

- Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
- Claude Web Search

## Purpose

Research `tier1` / `tier2` leads (score >= 60) and write post-connection LinkedIn DMs framed as research around the problem you're solving, not pitches.

## Input

All inputs **must be scored first** with `skills/score-leads`. The `score` column is required — only leads at or above `--min-score` (default 60) are enriched.

### Supported upstream sources

| Source | Drop raw CSV in | Then score with |
|---|---|---|
| Pipeline (`find-leads`) | `outputs/` | `score_leads_haiku.mjs` |
| LinkedIn Connections export | `inputs/connections/` | `score_leads_haiku.mjs` |
| Post-engagers (RapidAPI) | `inputs/post-engagers/` | `score_leads_haiku.mjs` |

**`inputs/connections/`** — drop your LinkedIn connections CSV here (exported from linkedin.com/mynetwork/invite-connect/connections/). LinkedIn exports: `First Name`, `Last Name`, `URL`, `Email Address`, `Company`, `Position`, `Connected On`. Both scoring and enrichment scripts auto-normalize these columns.

**`inputs/post-engagers/`** — drop post-engager CSVs here (from `skills/post-engagers`). Columns: `profile_name`/`name`, `profile_url`/`url`, `headline`. Both scripts auto-normalize these columns.

Also required: `context/brief/brief.md`. Hard cap: 1500 chars sent to the model. Per-lead fields are clipped before sending (`title` 300, `snippet` 300, `highlights` 500, `why_match` 240) to keep prompts small.

## Output (strict, CSV-only)

Append exactly 3 new columns to the input CSV:

1. `outreach_angle` — one sentence describing the specific real thing you're anchoring on.
2. `dm_sequence_1` — first DM, ready to send.
3. `dm_sequence_2` — follow-up DM, ready to send.

If no real, specific signal can be found, leave all 3 columns empty. Lacking information is better than fabricating it.

## What makes a good DM

Treat every DM as a post-connection note, not a cold pitch. Frame it as research so the prospect doesn't wonder "why is this stranger asking me?".

Here are some examples (not templates) :

> "Saw your post on [specific topic], the hook was the best thing in my feed this week. Have you thought about [specific improvement related to topic] ?"

> "Reaching out because you likely run [Founder]'s vendor stack, we build [solution to their problem] for founders in your stage without eating their calendar. Happy to send a sample onboarding plan if useful."

> "Noticed [Founder Name]'s [growth lever] is a growth lever for you, we run [service or offer] for [company type] so the in-house team can stay on [more important task]. Worth a 20-min comparison to what you've got now ?"


Length: max 2 short sentences.

## Hard rules

- Use the prospect's real first name (auto-extracted from the `title` column). No `{{first_name}}` / `[first_name]` placeholders in the output.
- Never use templates, adapt DMs to every prospect
- Never invent facts. If no real process or angle shows up in research, leave all 3 columns empty.
- Never cite a LinkedIn post or article in the DM text. Treat all post/article content as background research only.
- Never use the em dash character (`—`). Use a comma instead.
- No buzzwords. No pleasantries beyond a simple "thanks for connecting". Don't pitch, ask a question.
- DM2 opens directly with a new angle and never references the previous DM. Banned phrases (even softened): "follow-up", "follow up", "following up", "Quick follow-up", "Just following up", "circling back", "bumping this", "to add to my last message", "one more thing". DM2 should give the prospect something worth their time: a sharp observation, a tension worth their take, or a related angle that opens a new thread.

## Quick Start

**From pipeline output:**
```bash
# Step 1 — score
node scripts/score_leads_haiku.mjs \
  -i outputs/leads.csv \
  -o outputs/leads-scored.csv

# Step 2 — enrich
node scripts/enrich_leads_haiku.mjs \
  -i outputs/leads-scored.csv \
  -o outputs/leads-enriched.csv \
  -s 60 --sleep-ms 15000 --web-searches 1
```

**From LinkedIn connections (`inputs/connections/`):**
```bash
# Step 1 — score
node scripts/score_leads_haiku.mjs \
  -i inputs/connections/my-connections.csv \
  -o outputs/connections-scored.csv

# Step 2 — enrich
node scripts/enrich_leads_haiku.mjs \
  -i outputs/connections-scored.csv \
  -o outputs/connections-enriched.csv \
  -s 60 --sleep-ms 15000 --web-searches 1
```

**From post-engagers (`inputs/post-engagers/`):**
```bash
# Step 1 — score
node scripts/score_leads_haiku.mjs \
  -i inputs/post-engagers/engagers.csv \
  -o outputs/engagers-scored.csv

# Step 2 — enrich
node scripts/enrich_leads_haiku.mjs \
  -i outputs/engagers-scored.csv \
  -o outputs/engagers-enriched.csv \
  -s 60 --sleep-ms 15000 --web-searches 1
```

Defaults: model = `claude-haiku-4-5-20251001`, `--web-searches 1`. Override with `-m claude-sonnet-4-6` if you want Sonnet. Bump `--web-searches` only if angles consistently come back as `NO_SIGNAL`.

## Next Step

```
Read skills/export-leads/SKILL.md and export the final outreach list.
```
