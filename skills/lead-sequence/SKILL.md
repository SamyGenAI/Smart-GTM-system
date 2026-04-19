# Skill: Lead Sequence

**Duration:** 2–5 minutes per lead
**Output:** sequences written into a new column (or columns) on the enriched list — one short multi-touch sequence per lead, ready to paste into LinkedIn / Gmail.

---

## Quick Start

```
Read skills/lead-sequence/SKILL.md and write sequences for outputs/[date]-[campaign]-enriched.json
```

One per-lead sequence, personalized from the enriched data, written directly into the lead record. Whatever `run_mode` the enrichment used decides the channels here.

---

## Purpose

Step 5 in the workflow. Takes the output of `skills/lead-enrichment/` and writes the actual messages each lead will receive. Unlike `skills/signal-to-sequence/` — which is campaign-scale, built around one shared trigger across many accounts — this skill is lead-scale. Every lead gets its own short sequence grounded in their own data.

Three rules the output must obey:

1. **Be direct.** Name the intent in the first message. No throat-clearing.
2. **Show we did the work.** Reference something specific from the enriched record — a post, a hire, a funding event, a position — that the lead would recognize as theirs.
3. **Keep it short.** First message ≤ 50 words. Follow-ups ≤ 30 words. No multi-paragraph pitches.

---

## Inputs

- Enriched lead list from `skills/lead-enrichment/` (JSON conforming to `schema/enriched-lead.json`)
- `context/positioning.md` — value pillars, proof points, what the user sells
- `context/personas/` — one persona file per target role, including primary concerns and voice
- `context/icp-definition.md` — tier-specific angles if relevant
- `context/competitor-radar.md` (optional) — if the lead's angle touches a competitive loss pattern
- `context/profile.md` — the user's company and product facts, and their voice (founder-led vs. team-led, first-person vs. third, formal vs. casual)

**This skill is context-driven.** Nothing about the user is hardcoded in this file. The tone, the angles, the proof points all come from the user's `context/` folder.

---

## Step 0: Read the context and ask the user what to emphasize

Before writing any sequence, do two things:

1. **Read the context files** so the sequences sound like this user, not like a generic cold-email template. Pay attention to:
   - `context/profile.md` — voice: first/third person, formal/casual, founder-led or team-led
   - `context/positioning.md` — which value pillar maps to each persona
   - `context/personas/*.md` — primary concern per persona, best channel, what to never say

2. **Ask the user (once per run):**
   > "Quick check before I write:
   >  - **Angle to lead with** for most of these leads? (e.g. proximity/speed vs. big agencies, pipeline-not-just-impressions, specific value pillar) — or let me pick per-lead from the signals?
   >  - **Sender signature** (name + title as it should appear)?
   >  - **CTA preference** — soft ('worth 15 min?') or specific ('sending you a mockup, want it?')?"

If the prompt already specifies these, skip the question.

Channels to write come from the enriched record's `run_mode`:

| `run_mode` | Channels to produce |
|---|---|
| `linkedin` | LinkedIn DM touch 1–3 |
| `email` | Email touch 1–3 |
| `phone` | One email opener + one voicemail talk track |
| `multi` / `full` | LinkedIn DM touch 1, Email touch 2, LinkedIn follow-up touch 3 |

---

## Step 1: Per-Lead Signal Selection (30 sec / lead)

For each lead, pick the *one* specific thing the first message will reference. Order of preference:

1. A `signals.tier1_*` annotation that fired — e.g. inconsistent-poster, hiring-content-role — because these are the user's defined unlocks.
2. A recent `signals.recent_company_jobs` entry (datable, verifiable).
3. A `linkedin.summary` or `headline` phrase worth reacting to.
4. `company.total_funding_usd` or `company.year_founded` if nothing else is strong.

One hook per lead. Never stack two ("I saw you raised AND you're hiring AND…") — readers smell the research dump.

If nothing specific is available (enrichment mostly empty), **flag the lead** in the output with `sequence_status: "insufficient_data"` and do not write a message. Short is fine; fake-personalized is not.

---

## Step 2: Write the First Touch (60 sec / lead)

The first message carries the whole sequence. Get it right.

**Structure — any channel:**

```
[Hook: one specific observation from the enriched data, datable when possible]
[Connection: one sentence tying it to what the user sells, phrased as relevant — not as a pitch]
[CTA: one ask, frictionless]
```

**Constraints:**
- ≤ 50 words total for LinkedIn DM or email body.
- First line must reference something the lead would recognize as specifically theirs.
- Never "I came across your profile" / "loved your post" / "hope you're well" — these burn the "we did the work" signal.
- Never name-drop the user's product in the first sentence. The hook is about *them*, not about *us*.
- Use the voice the user's `context/profile.md` specifies. If it says founder-led first-person, write that way. If it says team-led third-person, write that way.

### Examples (structure only — fill from the user's actual context)

The examples from `skills/signal-to-sequence/SKILL.md` are the gold standard for tone. Keep that same directness and signal-first shape — trimmed to the per-lead length budget here. For instance, the pattern:

```
[Company] just posted for a Senior [Role] — third ops hire in 90 days.
Teams at that growth rate typically hit the same wall: [insight].
[One-sentence connection to what we do.]
Worth 20 minutes to compare notes?
```

…transposes to a LinkedIn DM for a founder lead as:

```
Saw [Company]'s 3rd ops hire in 90 days — tooling that worked at 50 breaks at 150.
We've helped [similar company] avoid exactly that. Worth 15 min?
```

Same shape, half the words. The *content* of the hook and insight always comes from the user's `context/positioning.md` and the lead's enriched data — never hardcoded in this skill.

---

## Step 3: Write Follow-ups (30 sec / lead, × 2 touches)

**Touch 2 (day 3–5):** different angle, not a repeat. If touch 1 led with a signal, touch 2 can lead with a proof point or a question. ≤ 30 words.

**Touch 3 (day 7–10):** the close or the break-up. One of:
- Specific ask ("can I send you the mockup?")
- Break-up ("not going to keep nudging — if [trigger] changes, ping me")
- Pivot to another channel ("if LinkedIn isn't the right place, happy to email [address]")

Pick per lead based on what feels honest for *this* lead's response pattern (if they opened but didn't reply, go for the specific ask; if they ghosted, break up).

**Never re-use the hook from touch 1.** If you only have one thing to say, send one message — don't pad.

---

## Step 4: The "Did We Actually Do the Work?" Check

Before marking a sequence as ready, confirm for every lead:

- [ ] Touch 1 references something from the enriched record — a post count, a hire, a funding number, a company name, a headline phrase. If touch 1 would work equally well for any other lead, it's generic — rewrite.
- [ ] The intent is stated in touch 1, not deferred to touch 3. The lead should know by word 30 what we want.
- [ ] Total length: touch 1 ≤ 50 words, touches 2–3 ≤ 30 words each.
- [ ] No phrases from the banned list: "hope you're well", "came across your profile", "following your work", "building something adjacent", "quick question".
- [ ] The voice matches `context/profile.md`.
- [ ] If `run_mode: linkedin`, no email-specific phrasing ("saw your inbox is busy"). Vice versa.

Leads that fail any check: mark `sequence_status: "needs_rewrite"` with the failure reason. Don't ship them.

---

## Output Format

Write sequences back to the same enriched JSON file (or a copy at `outputs/[date]-[campaign]-sequenced.json`), adding per-lead fields:

```jsonc
{
  // ... existing enriched fields ...
  "sequence_status": "ready" | "insufficient_data" | "needs_rewrite",
  "sequence_hook": "One sentence describing the specific thing touch 1 references",
  "sequence_angle": "Which value pillar / competitive angle this sequence uses",
  "touches": [
    {
      "n": 1,
      "channel": "linkedin_dm" | "email" | "voicemail",
      "day": 0,
      "subject": "(email only)",
      "body": "..."
    },
    { "n": 2, "channel": "...", "day": 3, "body": "..." },
    { "n": 3, "channel": "...", "day": 7, "body": "..." }
  ]
}
```

Also emit a run summary:

```
Sequences written — 147 leads
  ready:             128
  insufficient_data: 11  (enrichment too thin, skipped)
  needs_rewrite:     8   (failed the did-we-do-the-work check)
Angle breakdown: proximity 54, pipeline 38, speed 22, quality-per-$ 14
Avg touch-1 length: 38 words
```

Downstream (`export-csv`, `push-notion`) will flatten the `touches` array into columns.

---

## Quality Check

- [ ] Every `ready` lead has 2–3 touches, each obeying the length budget
- [ ] Every `ready` lead's touch 1 references something specific from the enriched record
- [ ] `sequence_status` is set for every lead — no nulls
- [ ] The run summary is printed, the angle breakdown is visible (so the user can tell if the skill defaulted to one angle across everyone)
- [ ] Nothing in the generated sequences hardcodes company names, products, or voice — all of that came from `context/`
