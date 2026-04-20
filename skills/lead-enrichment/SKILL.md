# Skill: Lead Enrichment

**Duration:** ~15s per lead (1 RapidAPI call)
**Output:** `outputs/[date]-[campaign]-enriched.csv` — one row per lead, one file, nothing else.

---

## Quick Start

```
Read skills/lead-enrichment/SKILL.md and enrich outputs/[date]-[campaign]-scored.md
```

Enriches each approved lead with a single RapidAPI call that returns profile + connections + followers + posts, then writes ONE CSV with a `Comment` column the sequence step will read. Annotation only — never drops a lead.

---

## Principles (read before running)

1. **One file. A CSV.** No intermediate JSON, no `.tmp/`, no per-lead artifacts. If you find yourself writing a second file, stop.
2. **One RapidAPI call per lead.** The combined endpoint `/profile-data-connection-count-posts` returns profile + connections + followers + 50 recent posts in a single request. Don't split it into two calls.
3. **Crustdata is opt-in.** Only call it if the user explicitly asks for deeper firmographics (revenue bands, structured employer history, jobs signal) that RapidAPI does not return. Default = off.
4. **Comment column is the handoff.** One short sentence per lead that the sequence-writer will use as the hook. No verbose analysis anywhere else.

---

## Inputs

- A scored lead list (Markdown table, CSV, or JSON) with at minimum `lead_id`, `name`, `linkedin_url` (or `linkedin_username`)
- `.env` with `RAPIDAPI_KEY` set (required). `CRUSTDATA_API_KEY` optional — only loaded if the user opts into deep enrichment.

---

## Run Modes

**Ask the user once, then proceed:**

> "Deep enrichment (Crustdata) or RapidAPI-only (default)?"

- **`rapid` (default)** — one combined RapidAPI call. Covers 95% of what DM sequences need.
- **`deep`** — RapidAPI + Crustdata person + Crustdata company. Adds revenue band and structured past employers. Use when the user says "go deep", "firmographics", "verify", or names Crustdata.
- **`email`** — RapidAPI + Orthogonal (Hunter email-finder + verifier). Adds `email` and `email_status` columns. Use for email / multi-channel campaigns.

If the prompt already picks one (e.g. "enrich via RapidAPI"), skip the question.

---

## Pipeline

For each lead, run in parallel within the lead. Build ONE row of the output CSV.

### Always (both modes) — RapidAPI, ONE call

`GET https://linkedin-api8.p.rapidapi.com/profile-data-connection-count-posts?username=<username>`
Headers: `x-rapidapi-host: linkedin-api8.p.rapidapi.com`, `x-rapidapi-key: $RAPIDAPI_KEY`

Response shape:
```
{
  "connection": 1877,
  "follower": <number>,
  "data": { firstName, lastName, headline, summary, geo{full,countryCode},
            position[0]{title, companyName, companyUsername, companyStaffCountRange, companyId},
            isPremium, isCreator, isTopVoice, languages, educations, ... },
  "posts": [ { postedDateTimestamp, totalReactionCount, commentsCount, text, postUrl, contentType }, ... up to 50 ]
}
```

Fields used:
- Identity/firmo: `data.firstName`, `data.lastName`, `data.headline`, `data.geo.full`, `data.geo.countryCode`, `data.position[0].title`, `data.position[0].companyName`, `data.position[0].companyUsername` (→ `company_domain` guess), `data.position[0].companyStaffCountRange` (→ `company_staff_range`), `data.isPremium`, `data.isCreator`, `data.isTopVoice`
- Audience: `connection`, `follower`
- Activity: filter `posts[]` to `postedDateTimestamp >= now - 90d`, then:
  - `posts_90d` — count
  - `avg_reactions_90d` — avg of `totalReactionCount`
  - `max_reactions_90d` — max of `totalReactionCount`
  - `most_recent_post_date` — ISO date of latest post
  - Keep top-3 most recent post snippets (≤150 chars each) internally — used to write the `comment` column, not emitted as their own columns

### Only if mode = `deep` — Crustdata, 2 calls

Skip entirely in default mode. In `deep` mode:

**Person** — `GET https://api.crustdata.com/screener/person/enrich?linkedin_profile_url=<url>`
Header: `Authorization: Token $CRUSTDATA_API_KEY`. Take `[0]`.
Pull: `current_employers[0].employer_company_website_domain[0]` (canonical domain for step 2), `current_employers[0].employer_company_id[0]`, `twitter_handle`, `past_employers` (structured history — optional, only if sequence needs a prior-company hook).
(Connections + followers already come from the RapidAPI combined call — don't re-fetch.)

**Company** — `GET https://api.crustdata.com/screener/company?company_domain=<domain>`
Take `[0]`. Pull: `employee_count_range`, `hq_country`, `year_founded`, `estimated_revenue_lower_bound_usd`, `estimated_revenue_higher_bound_usd`.

If Crustdata returns `status: "enriching"` or an empty array, leave those columns blank and move on. Do not block.

**Source of truth:** when Crustdata disagrees with RapidAPI on current company, trust RapidAPI `position[0]`. Crustdata's `current_employers[0]` can pick up concurrent roles (advisor, board, NGO) and resolve the wrong domain.

### Only if mode = `email` — Orthogonal (Hunter), 2 calls

Prereqs: `@orth/cli` installed globally, `ORTHOGONAL_API_KEY` in `.env`, skill installed via `orth skills install orthogonal/lead-enrichment`. Check balance first: `orth balance`.

Windows gotcha (MSYS / Git Bash): set `MSYS2_ARG_CONV_EXCL="*"` to stop the shell from rewriting `/v2/...` into `C:/Program Files/Git/v2/...`. Pass each query param as its own `--query key=value` flag — a single space-separated string fails.

**Finder** — find the email given first/last name + domain:
```bash
MSYS2_ARG_CONV_EXCL="*" orth api run hunter /v2/email-finder \
  --query domain=<domain> \
  --query first_name=<First> \
  --query last_name=<Last>
```
Maps: `data.email` → `email`; `data.score` → `email_score`; `data.verification.status` → `email_status`.

`domain` comes from (in order): Crustdata company domain (if `deep` already ran), domain guessed from RapidAPI `position[0].companyUsername`, or the user's input.

**Verifier** — optional, only if the finder's embedded verification isn't conclusive:
```bash
MSYS2_ARG_CONV_EXCL="*" orth api run hunter /v2/email-verifier --query email=<email>
```
Maps: `data.status` → `email_status` (overwrites finder's).

Record `sources.orthogonal_email = "hit" | "miss" | "error"`. A miss leaves the column blank — never block the lead.

---

## Signal + Comment (the only analysis step)

Compute `tier1_fit` from the RapidAPI post data and the scored input. It's a short label, not a float.

| Condition | Label |
|---|---|
| `posts_90d` in 3–15 AND `max_reactions_90d` < 500 AND `avg_reactions_90d` < 100 | `inconsistent-poster` (ICP match — Tier 1 unlock) |
| `max_reactions_90d` ≥ 500 OR `avg_reactions_90d` ≥ 200 | `high-engagement-creator` (anti-ICP) |
| `posts_90d` = 0 | `silent` (below floor) |
| `posts_90d` > 15 | `high-volume-poster` (verify: real creator or AI-automated?) |
| `posts_90d` in 1–2 | `barely-active` |

Then write a one-sentence **Comment** per lead using this recipe:

> `[tier1_fit label]. [One concrete hook the sequence-writer can use: most-recent-post angle, prior-company hook, company stage/size, or "no recent activity — lead with proximity angle only"].`

Examples:
- `inconsistent-poster. Posts 4x/90d about GTM ops at PlayGTM; last post on pricing ROI — hook on Kompyte→Semrush exit.`
- `high-engagement-creator. 10K-reaction viral on outbound personalization — anti-ICP, exclude.`
- `silent. No posts in 158d — lead with proximity-vs-big-creator angle; reference Sidetrade exit.`

Keep it under ~200 characters. This is the sequence-writer's only context from enrichment.

---

## Output: ONE CSV

Path: `outputs/[date]-[campaign]-enriched.csv`

Columns (exactly these, in order):

```
lead_id,name,linkedin_url,current_title,current_company,company_domain,company_staff_range,location,country_code,followers,connections,posts_90d,avg_reactions_90d,max_reactions_90d,most_recent_post_date,is_creator,tier1_fit,comment,source_mode
```

`source_mode` = `rapid` | `deep` | `email`.

In `deep` mode, append these columns AFTER `source_mode`:
```
revenue_band_usd,hq_country,year_founded
```

In `email` mode, append:
```
email,email_score,email_status
```

That's the entire output. No JSON sidecar, no markdown summary file, no `.tmp/` leftovers.

---

## Run Summary (printed to terminal only — not written to a file)

```
Enriched 15 leads — mode: rapid
  rapidapi_combined: 15 hit, 0 error (1 call per lead)
  tier1_fit breakdown:
    inconsistent-poster:     6
    high-engagement-creator: 3
    silent:                  4
    barely-active:           2
    high-volume-poster:      0
CSV: outputs/2026-04-19-tier1-founders-enriched.csv
```

Keep it to ~10 lines.

---

## Quality Check

- [ ] Exactly one file written: `outputs/[date]-[campaign]-enriched.csv`. Nothing in `outputs/.tmp/`, no intermediate JSON.
- [ ] Every input lead is a row in the CSV (no silent drops).
- [ ] `comment` column is filled for every lead, under ~200 chars, concrete enough to seed a DM hook.
- [ ] `tier1_fit` is set per the label table.
- [ ] If mode = `rapid`, no Crustdata calls were made.
- [ ] Terminal prints the run summary above the CSV path.
