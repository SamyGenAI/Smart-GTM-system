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

Append exactly 4 new columns to the input CSV:

1. `outreach_angle` — one sentence describing the specific real thing you're anchoring on.
2. `dm_sequence_1` — first DM, ready to send.
3. `dm_sequence_2` — follow-up DM, ready to send.
4. `evidence` — audit trail: each concrete fact used and its source, plus a `Searched:` line listing every URL the model actually fetched via web search. Review this to confirm nothing was fabricated and that quotes attributed to the prospect are real. The export keeps this column.

If no real, specific signal can be found, leave the first 3 columns empty. Lacking information is better than fabricating it.

**Attribution rule:** the model only states something as the prospect's own words ("your point that...", "your take that...") if it is a near-verbatim quote from a real source. Paraphrases and inferences are framed as neutral observations instead. When reviewing, cross-check any attributed quote against the URLs in the `evidence` column.

## What makes a good DM

Treat every DM as a post-connection note, not a cold pitch. Frame it as research so the prospect doesn't wonder "why is this stranger asking me?".

### Core principles

1. **Make it about them.** People don't care how clever you are, they care that you noticed them. Lead with something true about their world, never about you.
2. **Keep it short.** The shorter the opener, the more weight each word carries. Cut every word that isn't pulling its weight.
3. **Serve, don't take.** Lead with a genuine observation, a helpful question, or a thoughtful comment. They should think "this person gets it", not "this person wants something".
4. **One focused question.** Ask exactly one clear question per message so it's effortless to reply. Never stack two or three.

### How to personalize

Personalization is not dropping their name into a message. It's proving you stepped into their world and actually see them. The deeper you go, the stronger the pull. Anchor on one of these, in rough order of strength:

- **Their activity** — a recent post, comment, or take of theirs. Align with what's clearly on their mind. (Background only, never quote or cite the post in the DM text.)
- **Their problems** — a challenge they stated outright or one you inferred from their activity. Their challenges are the entry point.
- **Shared connections or clients** — a mutual contact or client builds trust fast with one line.
- **Their work** — a specific project, result, or client focus. Show you understand what matters to them, not that you skimmed the profile.

### How to ask the question

- **One at a time.** "What's been your biggest focus this week?" beats "How's business? What's challenging? What's your strategy?"
- **Make it specific.** A focused question proves you were paying attention. "What's been the hardest part of solving [specific problem] so far?" beats "What's the biggest challenge in your business?"
- **Frame it as curiosity, not prying.** Offer an easy fork: "Was it more about [option 1] or [option 2]?" This steers toward a real insight while staying easy to answer.

### Examples (not templates)

Each one is about them, under two sentences, ends on one specific question, and never pitches:

> "Saw your take on [specific topic], the hook was the best thing in my feed this week. What got you onto [specific angle] in the first place ?"

> "Noticed you've been scaling [specific thing they're working on] lately. Is the harder part right now the [option 1] or the [option 2] ?"

> "Your point about [specific belief they stated] stuck with me. When you ran into [specific problem], was it more of a process thing or a people thing ?"

Length: max 2 short sentences, exactly one question.

## Hard rules

- Use the prospect's real first name (auto-extracted from the `title` column). No `{{first_name}}` / `[first_name]` placeholders in the output.
- Never use templates, adapt DMs to every prospect.
- Make it about them, not about you. Lead with something true about their world.
- Max 2 short sentences per DM. Shorter is better. If it reads like a paragraph, cut it.
- Exactly one question per DM. Never stack questions.
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
