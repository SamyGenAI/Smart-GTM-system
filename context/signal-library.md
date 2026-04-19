# Signal Library

Last updated: 2026-04-19

---

## Signal Scoring Model

| Score | Tier | Action |
|-------|------|--------|
| 80–100 | Hot | Samy DMs founder within 2 hours. Personalized carousel mockup within 24 hours. |
| 60–79 | Warm | Add to Tier 2 LinkedIn + email sequence within 48 hours. |
| 40–59 | Cool | Add to Tier 3 automated sequence. |
| 0–39 | Cold | Log and monitor. No outreach. |

---

## Tier 1 Signals — Act Immediately

### Signal: Inconsistent LinkedIn Posts With Low Engagement
**Category:** Behavioral
**Points:** 40
**Source:** LinkedIn profile scrape (Taplio, Favikon, or manual)
**Refresh cadence:** Weekly

**Definition:** Founder has posted on LinkedIn 3–15 times in the last 90 days (proof of belief) with irregular cadence (gaps of 10+ days between posts) AND average engagement under 100 reactions per post despite having 500+ followers.

**Why it predicts fit:** This is Igentiv's exact unlock. They believe in the channel (they post), but they can't sustain it (inconsistency) and their output isn't landing (low engagement). Design + cadence is the leverage they need. When we show them a carousel mockup of one of their existing posts, the gap is visible in 10 seconds.

**Detection method:**
```
LinkedIn scrape (Taplio / Favikon / Clay + Phantombuster):
  For each founder in Tier 1/2 target list:
    - Pull last 90 days of posts
    - Calculate: post count, avg days between posts, avg reactions
  Flag if:
    - post_count BETWEEN 3 AND 15
    - avg_days_between_posts > 10
    - avg_reactions_per_post < 100
    - follower_count > 500
```

**Message hook:** "Saw your post on [specific topic] — the idea was sharp, but I think the format held it back. Mocked up what the same post looks like as a carousel. No pitch, just curious what you think."

---

### Signal: Experienced Founder in Europe or US Running a B2B Business
**Category:** Firmographic / Personal
**Points:** 35
**Source:** LinkedIn profile history, Crunchbase, company website
**Refresh cadence:** One-time enrichment at list-build

**Definition:** Founder is based in Europe or US, has prior founder/operator experience (second-time founder, ex-VP at another startup, or agency owner 3+ years), and currently runs a defined B2B business — product, service, or agency — with real revenue signals (paying customers, public case studies, hiring).

**Why it predicts fit:** Experienced founders recognize production quality instantly and don't waste time shopping on price. They have the pattern recognition to know that $800–$1k/mo for content + leads is the value option, not the expensive one. First-time founders over-deliberate; experienced ones decide in a week.

**Detection method:**
```
LinkedIn + Clay enrichment:
  - Geography: EU (UK, FR, DE, NL, ES, IT, Nordics) OR US
  - Current role: Founder / Co-founder / CEO
  - Prior roles: at least one prior Founder role OR VP+ at a startup 3+ yrs OR agency owner 3+ yrs
  - Company: B2B (exclude consumer/DTC/media), has website with clear offer
  - Revenue proof: paying customer logos on site OR active hiring OR funded
```

**Message hook:** "Followed your work at [prior company] — [specific detail]. Building Igentiv for founders in your stage exactly; would be curious if our format matches how you want to show up now."

---

### Signal: Early-Stage Startup or Agency (1–30 Employees)
**Category:** Firmographic
**Points:** 30
**Source:** LinkedIn company page, Crunchbase, Clay
**Refresh cadence:** Monthly

**Definition:** Company has 1–30 employees, founded in the last 5 years, is either an early-stage B2B startup (bootstrapped, Seed, or Series A) or a boutique B2B agency (3+ employees, clear service offering, paying clients visible).

**Why it predicts fit:** This is the size band where the founder is still the face of the brand, still personally running sales, still without a full marketing team — but big enough to afford $800–$1k/mo without flinching. Larger than this and they hire in-house; smaller and they can't sustain a retainer.

**Detection method:**
```
Clay workflow:
  - Source: LinkedIn company search + Crunchbase
  - Employees: 1–30
  - Founded: after 2020
  - Type: B2B SaaS / B2B services / B2B agency
  - Geo: EU + US
  - Exclude: consumer, agencies selling content services (competitors)
```

**Message hook:** "At [company size], you're at the exact moment where founder brand is the fastest growth lever — and also the hardest to sustain. We run that layer so you don't have to hire for it yet."

---

## Tier 2 Signals — Add to Active Sequences

### Signal: Founder Hiring Content / Marketing / Growth Role
**Category:** Organizational
**Points:** 20
**Source:** LinkedIn Jobs, company careers pages

**Definition:** B2B company 1–30 employees posted a job for Content Marketer, Head of Marketing, Growth Lead, or Founder's Associate in the last 30 days.

**Why it predicts fit:** They've admitted content/growth is a priority but don't have it covered. Hiring takes 3–6 months; we bridge the gap immediately — often at 1/5 the fully-loaded cost of the hire.

---

### Signal: Recent Funding Round or Revenue Milestone
**Category:** Firmographic / Intent
**Points:** 15
**Source:** Crunchbase, LinkedIn News, founder's own posts

**Definition:** B2B company raised Seed or Series A in the last 60 days, OR founder publicly announced a revenue/customer milestone (e.g., "just crossed $1M ARR").

**Why it predicts fit:** Discretionary budget moment + "something to talk about" content fuel. Short window before they hire marketing in-house.

---

## Tier 3 Signals — Monitor

- Founder joined LinkedIn Creator Mode recently (+5 pts) — intent declared
- Founder engaged (commented / reacted) on Samy's or adjacent creators' content (+5 pts) — warm handle
- Founder posted a carousel that looks visually weak (+5 pts) — aware of the format but can't execute

---

## Signal Combinations

| Combination | Combined Score | What it means | Action |
|-------------|----------------|---------------|--------|
| Inconsistent posts + Experienced founder + EU/US | +15 bonus | The exact ICP. Dream account. | Samy DMs within 2 hours with a personalized carousel mockup |
| Inconsistent posts + Hiring content role | +10 bonus | They know they need it, internal hire is months away | Tier 1 sequence, lead with "before you hire" angle |
| Experienced founder + Early-stage + Recent funding | +10 bonus | Budget authority + awareness + spend window | Tier 1 sequence, reference the raise |

---

## Suppression Rules

- Account is an existing Igentiv client → suppress all outreach
- Founder unsubscribed or DM'd "not interested" in last 180 days → suppress
- **Founder is an agency owner selling content/LinkedIn services** → suppress (competitor / anti-ICP)
- **Founder has zero LinkedIn posts in last 12 months** → suppress (won't show up to do the work)
- **Founder is a "creator" without a real B2B business behind them** → suppress (anti-ICP)
- Founder is outside Europe / US → suppress for now
- Founder is a first-time founder with no prior operator experience → deprioritize to Tier 3 monitor only

---

## Signal Decay

| Signal age | Score multiplier |
|------------|-----------------|
| 0–30 days | 100% |
| 31–60 days | 75% |
| 61–90 days | 50% |
| 91–180 days | 25% |
| 180+ days | 0% (signal expires) |

Run a weekly batch to recalculate scores with decay applied. The "inconsistent posts" signal is the exception — it's a steady-state behavior, not an event, so evaluate it on a rolling 90-day window rather than decaying.

---

## Signal Performance Log

| Signal | Outreach sent | Replies | Meetings | Pipeline | Notes |
|--------|--------------|---------|----------|----------|-------|
| Inconsistent posts + low engagement | | | | | |
| Experienced founder EU/US | | | | | |
| Early-stage startup/agency 1–30 | | | | | |
| Hiring content/marketing role | | | | | |
| Recent funding / revenue milestone | | | | | |
