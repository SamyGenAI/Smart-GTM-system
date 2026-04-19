# Skill: People Research

**Duration:** 15–30 minutes per person
**Output:** `outputs/[date]-[person-slug]-research.md`

---

## Quick Start

```
Read skills/people-research/SKILL.md and research [LinkedIn URL or "Name, Company"]
```

That's it. Claude will read your ICP, personas, and positioning context automatically and produce a structured profile brief focused on whether this person is a fit, what they care about, and how to reach them.

---

## Purpose

Build a complete intelligence brief on a single person — a founder, a head of growth, a chief of staff, or whoever `context/personas/` defines — before any 1:1 outreach. The goal is not a bio you could copy from their LinkedIn headline. The goal is to understand what they post about, what they are struggling with, what they have tried, and what specific angle and channel will make a message from the user land instead of getting ignored.

---

## When to Run This Skill

- Before any Tier 1 LinkedIn DM (always)
- Before a discovery call (refresh if research is older than 2 weeks)
- When a person-level signal fires (new role, first LinkedIn post in 30+ days, funding announcement)
- When a warm intro is being considered and you need to confirm fit
- To map the second-degree network around an existing client or champion

---

## Inputs

- Name + company (or LinkedIn URL)
- `context/icp-definition.md` — to score person-level fit
- `context/personas/` — to identify which persona this person maps to
- `context/signal-library.md` — to check for person-level signals (inconsistent posting, recent hire, etc.)
- `context/positioning.md` — to pick the right angle for this specific person

---

## Data Source Priority

**Step 0 — Detect EXA availability (do this before any search).**

Check whether `web_search_advanced_exa` is present in the available tool list for this session.
- If **yes** → use EXA path for the whole run.
- If **no** → use WebSearch path for the whole run. Do not attempt `web_search_advanced_exa` — the call will fail.

Note the chosen path at the top of the output file: `Data source: EXA` or `Data source: WebSearch (EXA not connected)`.

**EXA path** (via `web_search_advanced_exa`)
- Follow token isolation: spawn a subagent for each search, return only distilled output
- Use `category: "people"` for LinkedIn/profile discovery
- Use `category: "news"` for press mentions, interviews, podcast appearances
- Use `category: "personal site"` for personal blogs, Substacks, portfolios
- Use no category (`type: "auto"`) for general web context

**WebSearch path** (via built-in `WebSearch`)
- Target queries at LinkedIn, X/Twitter, Substack, personal domains directly (use `site:linkedin.com/in`, `site:substack.com`, etc.)
- Spawn a subagent per search for token isolation, same as the EXA path

**Mid-run fallback:** if the chosen path returns 0 useful results for a specific query (rate-limited, category restriction, dead topic), switch that single query to the other path and note it inline. Do not silently retry the same tool.

**Auth-gated content** (private LinkedIn sections, paid newsletters) → Claude in Chrome, regardless of path.

---

## EXA Usage Rules (when available)

- **Only** use `web_search_advanced_exa`. Never `web_search_exa` or other Exa tools.
- **Never** run Exa searches in the main context. Spawn a Task/Agent subagent per search. The subagent runs the search, processes results, and returns compact JSON or brief markdown.
- **Tune numResults** to intent: "a few" → 10–20, "comprehensive" → 50–100, specific number → match it.
- **Generate 2–3 query variations** and run in parallel for coverage, then dedupe.
- **Category `people` restrictions:** no date filters, no `includeText`/`excludeText`, no `excludeDomains`, and `includeDomains` may only contain LinkedIn domains.

---

## Research Steps

### Step 1: Identity & Role Snapshot (5 min)

Confirm you have the right person and pull the basics.

- **Full name, current title, current company, location**
- **LinkedIn URL** (verified, not guessed)
- **Follower count + connection count** (proxy for reach)
- **Time in current role** (shorter tenure = more open to new vendors / change)
- **Prior roles** — founder, operator, agency owner? How many years of relevant experience?
- **Notable past companies or exits** — credibility signals

Exa query shape (people category):
```
web_search_advanced_exa {
  "query": "[Full Name] [Company] LinkedIn",
  "category": "people",
  "numResults": 15,
  "type": "auto"
}
```

---

### Step 2: ICP Fit Check (3 min)

Cross-reference against `context/icp-definition.md`:

- Is this person an **experienced B2B founder** (prior operator or 3+ yr agency owner)?
- Is the company **1–30 employees, Seed–Series A or profitable bootstrapped, B2B**?
- Are they **EU or US based**?
- **Anti-ICP red flags:** creator without a real business, first-time founder with no track record, B2C/DTC, agency selling content/LinkedIn services, enterprise (500+).

Output a Tier (1 / 2 / 3 / Skip) with one-line justification.

---

### Step 3: LinkedIn Activity Audit (10 min)

This is the core of the skill for users whose ICP hinges on LinkedIn behavior (per `context/icp-definition.md` and `context/signal-library.md`). If the user's ICP doesn't care about LinkedIn activity, do a lighter-weight version of this step focused on whatever channels and content patterns `context/signal-library.md` actually defines as Tier 1 signals.

For the last 90 days of LinkedIn activity, capture:

- **Post frequency:** posts in last 30 / 60 / 90 days
- **Gap pattern:** longest gap between posts
- **Avg reactions + avg comments** per post
- **Content themes:** what 3–5 topics do they keep returning to?
- **Format mix:** text-only, carousel, video, image, repost — what's working and what isn't?
- **Voice:** first-person founder voice, thought-leader lecture voice, corporate voice, ghostwritten feel?
- **Engagement quality:** are the commenters ICP-adjacent (other founders, operators) or junior/random?

**Signal check against `context/signal-library.md`:**
- For each Tier 1 / Tier 2 signal defined in the user's signal library, check whether it fires for this person based on the activity data captured above. Use the thresholds and scoring logic from `context/signal-library.md` — this skill does not define thresholds of its own.

Exa query shape (news category for press mentions + interviews):
```
web_search_advanced_exa {
  "query": "[Full Name] interview podcast [Company]",
  "category": "news",
  "numResults": 10
}
```

If LinkedIn-specific data is auth-gated, note it and fall back to Claude in Chrome or manual check.

---

### Step 4: Context Beyond LinkedIn (5 min)

Go wider to understand what they actually think about.

- **Personal site / Substack / blog** — what are they writing long-form?
- **Podcast appearances, conference talks, interviews** — what story do they tell about their company?
- **X/Twitter activity** — do they have a second voice there? Different from LinkedIn?
- **Press mentions** — funding, product launches, awards, controversy

Exa query shapes:
```
web_search_advanced_exa {
  "query": "[Full Name] blog OR substack OR newsletter",
  "category": "personal site",
  "numResults": 10
}
```
```
web_search_advanced_exa {
  "query": "[Full Name] [Company]",
  "numResults": 15,
  "type": "auto"
}
```

---

### Step 5: The Angle (7 min)

This is the only step that matters. Everything above was research. This step is judgment.

Map the person to the user's positioning (`context/positioning.md`):

1. **Which persona are they?** Founder/CEO, Head of Growth, or Chief of Staff? Different angle per persona.

2. **Why now?** What specific event or pattern makes *this week* the right moment to DM them? (Recent inconsistent post streak, new hire they just made, product launch, funding, conference talk.)

3. **Which competitive angle lands?** Read the angles from `context/competitor-radar.md` and `context/positioning.md`. Pick the one whose "win when" conditions match what this person signals (e.g. they value direct access → use the proximity angle; they're burned by generic templates → use the quality angle). Do not invent angles the user hasn't defined.

4. **What's the hook?** The first line of the DM. Reference something specific from Step 3 or 4 — a recent post, a podcast quote, a hiring move — and connect it to a relevant insight. Never generic. Never "loved your post."

5. **Which channel?** LinkedIn DM is default for founders. Warm intro if a mutual connection exists. Email only if LinkedIn is dormant.

---

## Output Format

```markdown
# People Research: [Full Name]
Date: [YYYY-MM-DD]
Company: [Company Name] | Role: [Title]
LinkedIn: [URL]
ICP Tier: [1 / 2 / 3 / Skip]
Persona: [Founder / Head of Growth / Chief of Staff]
Signal score: [X/100]
Recommended action: [DM this week / Sequence / Monitor / Skip]

## Snapshot
[2–3 sentences: who they are, what the company does, why they matter]

## ICP Fit
- Experienced founder: [Yes/No — evidence]
- Company stage/size fit: [Yes/No]
- Geography fit: [Yes/No]
- Anti-ICP flags: [None / list]

## LinkedIn Activity (last 90 days)
- Posts: [N] | Longest gap: [X days]
- Avg reactions: [X] | Avg comments: [X]
- Followers: [X]
- Content themes: [3–5 topics]
- Format mix: [breakdown]
- Voice: [description]
- Tier 1 signal #1 (inconsistent posting): [Fires / Does not fire]

## Broader Context
- Personal site / Substack: [URL or none]
- Recent press / podcasts: [list with dates]
- X/Twitter: [handle, activity level]
- Notable quotes or themes: [1–3 pull-quotes that reveal what they care about]

## The Angle
**Why now:** [Specific trigger, datable]
**Persona-specific concern:** [pulled from personas/]
**Competitive angle to use:** [proximity / speed / quality-per-dollar / bundled pipeline]
**Hook (first DM line):** [proposed opening]
**Channel:** [LinkedIn DM / Warm intro via X / Email]
**Sender:** [Who from the user's team sends this — read from context/profile.md]

## Suggested Next Action
[Specific: which sequence, which asset to attach — e.g., mockup of their last post redesigned as carousel — which day to send]
```

---

## Quality Check

Before filing the output, confirm:

- [ ] LinkedIn URL is verified (not guessed from a name pattern)
- [ ] Anti-ICP has been checked — not a creator-without-business, not a competitor agency
- [ ] LinkedIn activity audit has real numbers, not vibes
- [ ] The "why now" references a specific post, hire, or event — with a date
- [ ] The hook would make sense to this person reading it cold — it does not name-drop the user's company in line one
- [ ] The data source chosen at Step 0 (EXA or WebSearch) is noted at the top of the output
