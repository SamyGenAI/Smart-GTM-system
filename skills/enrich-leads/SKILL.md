---
name: enrich-leads
description: Enrich qualified leads with Haiku + Web Search. Adds outreach angle and DM copy. CSV-only.
---

# Skill: Enrich Leads

Generic skill: works for any company. Company specifics are loaded at runtime from a SHORT `context/brief.md` (offer + ICP only, max ~150 words). The long `positioning.md` and `icp-definition.md` files are NOT sent to the API.

## Model + Source

- Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
- Claude Web Search

## Purpose

Research `tier1` / `tier2` leads (score >= 60) and write post-connection LinkedIn DMs framed as research, not pitches. The frame: "I'm researching how [type of company] handles [specific process]. Is that something you deal with, or someone else on your team?" — adapted with real specifics from the prospect's world.

## Input

- Scored leads CSV from `skills/score-leads` (must already include `score` column).
- `context/brief.md` (REQUIRED). Hard cap: 1500 chars sent to the model. Per-lead fields are clipped before sending (`title` 300, `snippet` 300, `highlights` 500, `why_match` 240) to keep prompts small.

## Output (strict, CSV-only)

Append exactly 3 new columns to the input CSV:

1. `outreach_angle` — one sentence describing the specific real thing you're anchoring on.
2. `dm_sequence_1` — first DM, ready to send.
3. `dm_sequence_2` — follow-up DM, ready to send.

If no real, specific signal can be found, leave all 3 columns empty. Lacking information is better than fabricating it.

## What makes a good DM

Treat every DM as a post-connection note, not a cold pitch. Frame it as research so the prospect doesn't wonder "why is this stranger asking me?".

Adapt this frame with real specifics:

```
Hey [first_name], thanks for connecting. I'm researching how [type of company they run] handle [specific process from their world]. Is that something you deal with, or someone else on your team?
```

Research is for YOU only. Read the prospect's posts, bio, website, articles to identify the right type-of-company and the right specific process. The research itself never appears in the DM. No "saw your post", "noticed your", "your point about", "since reading your".

`[type of company]` must be specific (e.g. "B2B SEO agencies", "ABM consultancies for SaaS", "AI-content studios"), not generic.
`[specific process]` must come from real research: a methodology they use, a metric they track, a transition their industry is in, a tradeoff they wrestle with.

Length: max 2 short sentences, around 30 words. If a sentence has more than one comma, it is too long.

Vary the type-of-company and the process across leads. Don't reuse the exact same wording.

## Hard rules

- Use the prospect's real first name (auto-extracted from the `title` column). No `{{first_name}}` / `[first_name]` placeholders in the output.
- Never invent facts. If no real process or angle shows up in research, leave all 3 columns empty.
- Never cite a LinkedIn post or article in the DM text. Treat all post/article content as background research only.
- Never use the em dash character (`—`). Use a period or comma.
- No buzzwords. No pleasantries beyond a simple "thanks for connecting". Don't pitch, ask a question.
- DM2 opens directly with a new angle and never references the previous DM. Banned phrases (even softened): "follow-up", "follow up", "following up", "Quick follow-up", "Just following up", "circling back", "bumping this", "to add to my last message", "one more thing". DM2 should give the prospect something worth their time: a sharp observation, a tension worth their take, or a related angle that opens a new thread.

## Quick Start

```bash
node scripts/enrich_leads_sonnet.mjs \
  -i outputs/leads-scored.csv \
  -o outputs/leads-enriched.csv \
  -s 60 \
  --sleep-ms 15000 \
  --web-searches 1
```

Defaults: model = `claude-haiku-4-5-20251001`, `--web-searches 1`. Override with `-m claude-sonnet-4-6` if you want Sonnet. Bump `--web-searches` only if angles consistently come back as `NO_SIGNAL`.

## Next Step

```
Read skills/export-leads/SKILL.md and export the final outreach list.
```
