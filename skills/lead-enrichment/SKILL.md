# Skill: Lead Enrichment

**Duration:** 30–90 seconds per lead (network-bound)
**Output:** `outputs/[date]-[campaign]-enriched.json` (one `EnrichedLead` object per input lead; schema in `schema/enriched-lead.json`)

---

## Quick Start

```
Read skills/lead-enrichment/SKILL.md and enrich this scored list: outputs/[date]-[campaign]-scored.csv
```

Enriches each approved lead with LinkedIn profile data, contact info (email/phone), and company hiring signals. Output is annotation-only — scoring already decided who's in or out.

---

## Purpose

Step 4 in the GTM workflow. Takes leads that passed ICP scoring and fills in every field needed to write a personalized DM sequence and push to a CSV / Notion table. The skill never drops a lead — it annotates. If an enrichment provider fails or isn't configured, the field stays null and the `sources` block records `skipped` or `error`.

---

## Inputs

- A scored lead list (CSV or JSON) — must include at minimum `lead_id`, `name`, and `linkedin_url`
- `.env` with any combination of `RAPIDAPI_KEY`, `CRUSTDATA_API_KEY`, `ORTHOGONAL_API_KEY` (skill adapts to what's available)
- `context/icp-definition.md` + `context/signal-library.md` — for Tier 1 signal annotation

---

## Run Mode (ask before any work)

**Step 0a — Ask the user what they're enriching for.**

Before the detection checks, ask once:

> "What are you enriching these leads for?
>  1. LinkedIn DM campaign (LinkedIn data + signals, no email/phone)
>  2. Email campaign (email + phone + company context, skip LinkedIn scrape)
>  3. Phone outreach (phone + basic identity, skip everything else)
>  4. Multi-channel (LinkedIn + email + phone)
>  5. Full enrichment (everything — default)"

Capture the answer as `run_mode` ∈ `linkedin | email | phone | multi | full`. Stamp it at the top of the output file and in the run summary.

**If the prompt already specifies a channel** (e.g. "enrich for LinkedIn DM campaign"), skip the question and set `run_mode` directly.

**Mode → provider matrix** — providers not in the row are `skipped (mode)`, not `skipped (no creds)`:

| Mode | RapidAPI | Orthogonal | Crustdata person | Crustdata company | Crustdata jobs |
|---|---|---|---|---|---|
| `linkedin` | on | off | off | on | on |
| `email` | off | on | on | on | off |
| `phone` | off | on | on | off | off |
| `multi` | on | on | on | on | on |
| `full` | on | on | on | on | on |

`multi` and `full` resolve to the same provider set today; keep the distinction so we can add more providers later without breaking callers.

---

## Data Source Priority

**Step 0b — Detect provider availability for the providers the mode requires.**

For each provider the mode calls for, check what's configured. Tell the user what's on and what's off, then proceed with whatever subset is available.

| Provider | Detection | If missing |
|---|---|---|
| RapidAPI LinkedIn | `RAPIDAPI_KEY` env var set | Skip LinkedIn scrape. `linkedin` block stays null. |
| Orthogonal (email/phone) | `orth` binary in PATH **and** `ORTHOGONAL_API_KEY` set **and** `orthogonal/lead-enrichment` skill installed | Skip to Crustdata for phone; leave email null. |
| Crustdata person | `CRUSTDATA_API_KEY` env var set | Skip person enrichment. Phone stays null if Orthogonal also missing. |
| Crustdata jobs | `CRUSTDATA_API_KEY` env var set AND a `current_company_id` resolved | Skip job signals. `recent_company_jobs*` stays null. |

Detection commands:
```bash
# Load .env into shell
set -a; source .env 2>/dev/null || true; set +a

# Check each credential
[[ -n "${RAPIDAPI_KEY:-}" ]] && echo "rapidapi:on" || echo "rapidapi:off"
[[ -n "${CRUSTDATA_API_KEY:-}" ]] && echo "crustdata:on" || echo "crustdata:off"
[[ -n "${ORTHOGONAL_API_KEY:-}" ]] && command -v orth >/dev/null 2>&1 && echo "orthogonal:on" || echo "orthogonal:off"
```

If Orthogonal is off, tell the user once:
> "Orthogonal isn't configured. To enable email/phone enrichment: `npm install -g @orth/cli`, then `orth skills add orthogonal/lead-enrichment`, then set `ORTHOGONAL_API_KEY` in `.env`."

Record the detection result in the run log — do not re-check per lead.

---

## Per-Lead Enrichment Pipeline

For each lead in the input list, run the providers that are on. Providers are **independent** — run in parallel per lead. Build the `EnrichedLead` object incrementally; each provider fills its slice.

### 1. RapidAPI LinkedIn scrape (if mode includes it AND provider on)

Parse the LinkedIn username from the URL, then:

```bash
scripts/rapidapi-linkedin.sh "<linkedin_url_or_username>"
```

Map the response to the `linkedin` block:
- `data.firstName` / `data.lastName` → `first_name` / `last_name`
- `data.headline` → `headline`
- `data.summary` → `linkedin.summary`
- `data.position[0].title` → `current_title`
- `data.position[0].companyName` → `current_company`
- `data.geo.full` → `location`; `data.geo.countryCode` → `country_code`
- `connection` → `linkedin.connections`
- `follower` → `linkedin.followers`
- `data.isCreator` / `data.isTopVoice` → `linkedin.is_creator` / `linkedin.is_top_voice`
- `posts` (array) → `linkedin.recent_posts_count` = length; compute avg reactions if available in post objects
- Record `sources.rapidapi = "hit"` (or `"miss"` / `"error"`)

### 2. Orthogonal email/phone (if mode includes it AND provider on)

Orthogonal runs as an installed sub-skill, not a raw HTTP call. The `orthogonal/lead-enrichment` skill handles its own provider routing internally.

Invoke it as a peer skill by following the instructions in its `SKILL.md` (installed at `skills/orthogonal-lead-enrichment/` or equivalent after `orth skills add orthogonal/lead-enrichment`). Pass the LinkedIn URL as input, expect email + phone in the response.

Map result → `contact.email` (with `email_source: "orthogonal"`) and `contact.phone` (with `phone_source: "orthogonal"`). Record `sources.orthogonal`.

### 3. Crustdata person enrich (if mode includes it AND provider on)

```bash
scripts/crustdata-person.sh "<linkedin_url>"
```

Response is an array; take `matches[0]` if `confidence_score >= 0.8`. Map:
- `basic_profile.current_title` → fill `current_title` if RapidAPI missed it
- `basic_profile.location.raw` → fill `location` if missing
- `basic_profile.languages` → `linkedin.languages` (extend schema if needed, not blocking)
- `contact.phone_numbers[0]` → `contact.phone` ONLY if Orthogonal didn't already set it. Set `phone_source: "crustdata"`.
- `contact.websites` → `contact.websites` (merge, dedupe)
- Record `sources.crustdata_person`

Lower-confidence matches (< 0.8) → record `sources.crustdata_person = "miss"` and add a note; don't overwrite fields.

### 4. Crustdata company_id resolution (needed for step 5)

RapidAPI gives a LinkedIn `companyId`, but Crustdata's `/job/search` needs Crustdata's own `crustdata_company_id`. These are not the same — resolve by domain.

Prefer domain sources in this order:
1. `current_company_domain` field already on the input lead (scoring step may have it)
2. Company domain derivable from the lead's email (if Orthogonal returned one)
3. Company homepage parsed from RapidAPI `data.position[0].companyURL`

Then:

```bash
scripts/crustdata-company.sh "<domain>"
```

Map response → extend the lead:
- `companies[0].crustdata_company_id` → `current_company_id`
- `companies[0].basic_info.name` → fill `current_company` if missing
- `companies[0].headcount.total` → `company.headcount`
- `companies[0].locations.hq_country` → `company.hq_country`
- `companies[0].funding.total_investment_usd` → `company.total_funding_usd`
- `companies[0].basic_info.year_founded` → `company.year_founded`

If `total_count: 0` or no domain is available, leave `current_company_id` null, skip step 5, and add a note. Do not block the rest of the enrichment.

### 5. Crustdata jobs signal (if on and company_id is set)

```bash
scripts/crustdata-jobs.sh "<company_id>" "2025-10-01" 10
```

Map response → `signals.recent_company_jobs` (up to 10 most recent). Compute:
- `signals.recent_company_jobs_count` = length
- `signals.hiring_content_or_growth_role` = true if any job title or category matches `/content|marketing|growth|founder'?s? associate/i`

These are **annotations only**. Never drop a lead based on job signals.

### 6. Derived Tier 1 signal annotation

If `linkedin.recent_posts_count`, `linkedin.followers`, and avg reactions are all populated, compute:
- `signals.tier1_inconsistent_poster` = true when:
  - posts in last 90d between 3 and 15
  - avg reactions < 100
  - followers ≥ 500

Use whatever the user's `context/signal-library.md` defines as the "inconsistent poster" unlock — thresholds above are a reasonable default but the library is the source of truth. Annotation only.

---

## Parallelism

Process leads in batches of 5–10 concurrently. Within one lead, the four provider calls can also run in parallel since they don't depend on each other (except Crustdata jobs depends on a resolved `current_company_id`, which comes from either RapidAPI or Crustdata person). Practical pattern: kick off RapidAPI + Orthogonal + Crustdata-person in parallel, then fire Crustdata jobs after they return.

Respect rate limits — if any provider returns HTTP 429, pause that provider for 60s and continue with the others. Note the rate-limit hit in the lead's `notes`.

---

## Output Format

One JSON file at `outputs/[date]-[campaign]-enriched.json`, containing an array of `EnrichedLead` objects conforming to `schema/enriched-lead.json`.

Also emit a run summary at the top of the terminal:

```
Enrichment complete — 147 leads   mode: linkedin
  rapidapi:         132 hit, 11 miss, 4 error
  orthogonal:       skipped (mode: linkedin)
  crustdata_person: skipped (mode: linkedin)
  crustdata_company: 118 hit, 23 miss, 6 skipped (no domain)
  crustdata_jobs:   89 hit (avg 4.2 jobs/lead), 29 skipped (no company_id)
Tier 1 inconsistent-poster signal: 91/147 leads (62%)
```

The "skipped" suffix distinguishes why: `(mode: X)` = intentional, `(no creds)` = user needs to set a key, `(no domain)` / `(no company_id)` = upstream dependency missing.

---

## Quality Check

Before handing off to the sequence-writer skill:

- [ ] `run_mode` was captured (asked or passed in) and stamped in the output + run summary
- [ ] Every input lead has a corresponding output record (no silent drops)
- [ ] The `sources` block is filled for every lead with the right status — `skipped_by_mode` vs `skipped_no_creds` vs `skipped_no_dependency` are distinguished, never collapsed into a generic "skipped"
- [ ] For email/phone/multi/full modes: leads with `email: null` are flagged in the run summary
- [ ] For linkedin/multi/full modes: `tier1_inconsistent_poster` is computed when the data allows (if the user's `context/signal-library.md` defines such a signal)
- [ ] The run summary is printed at the top of the terminal, not buried
- [ ] If every provider the mode requires is off (credentials missing), the skill stops with a clear error telling the user which keys to set, rather than producing a file of empty shells
