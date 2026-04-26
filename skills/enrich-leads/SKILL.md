---
name: enrich-leads
description: Enrich qualified leads with Sonnet + Claude Web Search. Adds outreach angle and DM templates. CSV-only.
---

# Skill: Enrich Leads

## Model + Source

- Claude Sonnet
- Claude Web Search

## Purpose

Do deeper research on `tier1` / `tier2` leads (score >= 60) and produce ready-to-send outreach copy.

## Input

- Scored leads CSV from `skills/score-leads` (must already include `score` and `why_match`)
- Context files: `context/icp-definition.md`, `context/positioning.md`
- Optional user constraints (region, vertical, competitor focus)

## Output (strict, CSV-only)

Append exactly **3 new columns** to the input CSV:

1. `outreach_angle` — 1 sentence. The specific personalization angle for this lead (the trigger/signal you noticed).
2. `dm_sequence_1` — first DM in the sequence, ready to send.
3. `dm_sequence_2` — follow-up DM, ready to send.

No JSON output. CSV only.

## DM Sequence Templates

Use these exact structures, filled in with real context for the lead.

**DM sequence 1** (opener, question-led):

```
Hey {{first_name}}, [give a compliment / something you noticed / connect genuinely]. I'm researching how [ICP role] like you handle [problem I'm solving]. Does it take [pain point] and how do you ensure [specific result]?
```

**DM sequence 2** (follow-up, value-add):

```
Reply with genuine interest, I'd love to learn more about it to help me refine my offer and positioning. Would you be open for a quick chat (not a sales call, just want to learn)?
```

## DM Generation Rules (strict)

1. **The first sentence must be about THEM.** Not your company, not your product, not your excitement about reaching out. Them.
2. **Reference the specific trigger signal.** If the signal is a fundraise, mention the round. If it's a LinkedIn post, reference exactly the core message or something specific. If it is a job posting, mention the role. Generic messages fail.
3. **No buzzwords.** Banned list: synergy, leverage, touch base, circle back, ping, loop in, alignment, move the needle, low-hanging fruit, deep dive, bandwidth, at the end of the day, innovative, cutting-edge, best-in-class, world-class, game-changing, disruptive.
4. **No pleasantries that waste the first line.** No "I hope this email finds you well." No "I hope you are having a great week." No "Happy [day of week]."
5. **Ask a question, do not make a pitch.** Questions create engagement. Pitches create delete buttons.
6. **Each follow-up must add NEW value.** New information, a new angle, a new resource, a new comparison. Never write "just following up" or "bumping this to the top of your inbox" or "wanted to circle back." If you have nothing new to add, do not send the message.
7. **Every message must be READY TO SEND.** No placeholder brackets like `[Company Name]` or `[Pain Point]`. Fill in everything from the loaded context. The only acceptable variable is the prospect's first name, written as `{{first_name}}`.

## Operational Rules

- Only enrich leads with `score >= 60` (tier1 + tier2). Skip tier3/exclude.
- Keep `outreach_angle` to one specific, concrete signal — not a generic descriptor.
- Prefer recent public signals (last 90 days) over evergreen biography.
- If no real trigger signal can be found, leave `outreach_angle` empty and skip DM generation rather than fabricate.

## Next Step

```
Read skills/export-leads/SKILL.md and export the final outreach list.
```
