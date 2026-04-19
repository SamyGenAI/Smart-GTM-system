# CLAUDE.md

This file is the persistent context layer for Igentiv's GTM repository. Claude Code reads it automatically at the start of every session. The full context lives in `context/`.

---

## Company

**Igentiv** helps B2B founders build a premium LinkedIn presence and generate qualified leads — without stitching together a ghostwriter, a designer, and an SDR agency.

Stage: Bootstrapped boutique studio — founder-led, just starting
HQ: [inferred] | Website: studio.igentiv.com

GTM motion: Founder-led (inbound from Samy's own LinkedIn + outbound DMs)
ACV: $800–$1,000/month retainer | Sales cycle: [inferred] 7–21 days
Primary channels: LinkedIn (inbound + outbound DM), Substack, peer referrals

---

## ICP

Full definition: `context/icp-definition.md`

**Who we sell to:** Experienced B2B founders (EU or US, 1–30 employees, early-stage startup or boutique agency) who already post on LinkedIn inconsistently with low engagement — belief is there, execution isn't. They have a solid, defined business and real revenue.

**Tier 1 (Top 150):** Experienced B2B founders (prior operator or agency owner 3+ yrs), 5–30 employees, Seed–Series A or profitable bootstrapped, 1K–10K LinkedIn followers, posts 3–15 times per 90 days with sub-100 avg reactions, EU or US based.
**Tier 2 (500–1,000):** B2B founder or agency owner posting monthly but inconsistently, clear defined offer, no existing content agency retainer.
**Tier 3 (1,000–3,000):** Any B2B founder / agency owner EU or US with defined ICP and occasional LinkedIn activity.

**Never target:**
- **Creators without a real business** (personal brand only, no product/service) — no retainer budget sustainability
- **Founders who don't post on LinkedIn at all** — we amplify, we don't manufacture voice from zero
- **Founders with weak/no online presence** (sub-500 followers, no digital footprint)
- **First-time founders with no track record** — over-deliberate, price-shop, don't recognize production quality
- B2C / DTC / consumer brands — wrong channel
- Agencies selling content/LinkedIn services — competitors
- Enterprise (500+ employees) — procurement kills a $1k/mo retainer

---

## Personas

Full profiles: `context/personas/`

| Role | Title(s) | Primary concern | Best channel |
|------|----------|----------------|-------------|
| Champion + Economic buyer | B2B Founder / CEO / Agency owner | Pipeline and brand reach, without spending their own time | LinkedIn DM (founder-to-founder) |
| Secondary buyer | Head of Growth / Marketing | Founder-sourced pipeline without production overhead | LinkedIn, warm intro via GTM community |
| Gatekeeper | Chief of Staff / Founder's Associate | Reliable vendor that doesn't eat founder time | LinkedIn or email |

---

## Positioning

Full document: `context/positioning.md`

**We win when:** Founder values direct access, speed, and quality-per-dollar over brand halo. Experienced founders who've been burned by "famous vendor, junior execution" and want proximity instead.
**We lose when:** Founder is buying a big creator's brand halo — they want the name on their vendor list. We can't out-creator them yet; we reframe to proximity/speed/quality or lose.

vs. **Agencies led by big creators (PRIMARY LOSS PATTERN):** "Work with the founder, not a junior in their queue — 3–5x cheaper, days not weeks, direct Slack access."
vs. Ghostwriting agencies: Premium design + leads bundled — text is the floor, not the ceiling.
vs. Design-only agencies: We bundle pipeline, not just impressions.
vs. DIY + AI tools: Human taste on top of AI efficiency — output a founder is proud to post.

**Voice:** Direct, founder-to-founder. Show the work, skip the deck. Never attack big creators personally — respect the brand, reframe the choice.

---

## Signals

Full library: `context/signal-library.md`

**Act immediately (Tier 1):**
1. **Inconsistent LinkedIn posts with low engagement** — 3–15 posts in 90 days, gaps 10+ days, <100 avg reactions, 500+ followers. Our exact unlock.
2. **Experienced founder in EU or US running a B2B business** — prior founder/operator or 3+ yr agency owner, defined B2B offer with real revenue.
3. **Early-stage startup or agency (1–30 employees)** — founder is still the face, no full marketing team yet.

**Add to sequence (Tier 2):**
1. Founder hiring Content / Marketing / Growth / Founder's Associate role
2. Recent Seed/Series A funding or public revenue milestone in last 60 days

---

## Team

| Name | Role | Owns |
|------|------|------|
| Samy Chouaf | Founder | Sales, strategy, creative direction, client relationships — everything |

---

## This Week

*Just starting — no active campaigns yet. Priority order:*

- [ ] Build first target list of 150 Tier 1 accounts using the 3 Tier 1 signals
- [ ] Draft and test 3 outbound DM variants (one per competitive angle: proximity, speed, quality/$)
- [ ] Create 2–3 carousel mockups from real Tier 1 founders' existing posts as personalized outreach assets
- [ ] Grow Samy's own LinkedIn (4K → ongoing) and Substack (200+) — still the primary proof and inbound engine

---

## Quick Commands

```
# Research an account (company)
Read skills/account-research/SKILL.md and research [founder-company.com]

# Research a person (founder, stakeholder)
Read skills/people-research/SKILL.md and research [LinkedIn URL or "Name, Company"]

# Source leads from engagers on your own LinkedIn posts
Read skills/post-engagers/SKILL.md and pull engagers from my last [N] posts

# Score a list against ICP
Read skills/icp-scoring/SKILL.md and score these accounts: [paste list]

# Enrich approved leads (LinkedIn scrape + email/phone + company signals)
Read skills/lead-enrichment/SKILL.md and enrich outputs/[date]-[campaign]-scored.csv

# Write per-lead sequences on the enriched list
Read skills/lead-sequence/SKILL.md and write sequences for outputs/[date]-[campaign]-enriched.json

# Export the final list (CSV always, Notion optional)
Read skills/export-list/SKILL.md and export outputs/[date]-[campaign]-sequenced.json

# Build a campaign (many-accounts, shared trigger — different use case from lead-sequence)
Read skills/signal-to-sequence/SKILL.md — build a Tier 1 campaign for
experienced EU/US B2B founders posting inconsistently on LinkedIn,
leading with the proximity/speed/quality angle vs. big-creator agencies
```

---

## Workflow

```
1. ICP definition / segmentation     →  context/icp-definition.md
2. Find leads matching ICP           →  skills/people-research, skills/account-research
   Or source from own audience       →  skills/post-engagers (optional)
3. Score the leads                   →  skills/icp-scoring
4. Enrich approved leads             →  skills/lead-enrichment
5. Write per-lead DM / email sequences → skills/lead-sequence
6. Export list (CSV always, Notion optional) → skills/export-list
```

## Stack

- **EXA** — company + people discovery (`web_search_advanced_exa`). Falls back to built-in web search if MCP not connected.
- **RapidAPI** (`linkedin-api8`) — LinkedIn profile scrape in lead-enrichment.
- **Orthogonal** (`@orth/cli` + `orthogonal/lead-enrichment` skill) — email and phone enrichment.
- **Crustdata** — person enrichment, company resolution by domain, and job-posting signals for lead refinement (annotation only).
- **Notion** (MCP, optional) — final list push.

All credentials live in `.env` (see `.env.example`). Every enrichment field in the output carries a `*_source` pointer so downstream consumers can audit provenance.
