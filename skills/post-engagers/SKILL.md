# Skill: Post-Engagers Signal

**Duration:** 2–8 minutes per run (depending on post count and pagination)
**Output:** `outputs/[date]-post-engagers-raw.csv` — a raw lead list of people who reacted to the user's recent LinkedIn posts, ready to feed into `skills/icp-scoring/`.

---

## Quick Start

```
Read skills/post-engagers/SKILL.md and pull engagers from my last [N] LinkedIn posts
```

Turns the user's own LinkedIn engagement into a lead source. Every person who hit like on a post becomes a candidate — high-intent because they've already signaled they're paying attention.

---

## Purpose

The user's own audience is the most under-used lead list in most GTM motions. People who react to a post are warmer than cold outbound by definition: they self-selected in. This skill surfaces them as structured leads that then flow through the normal pipeline — scoring, enrichment, sequencing, export.

This skill does **not** score or enrich. It only surfaces. The downstream pipeline decides who's worth pursuing.

---

## Inputs

- `context/profile.md` must contain `user_linkedin_url` (set during `skills/setup/`)
- `RAPIDAPI_KEY` in `.env`
- Either a user-provided post count (e.g. "last 5 posts") or a default of 10 most recent

---

## Step 0: Read the User's LinkedIn URL

Pull `user_linkedin_url` from `context/profile.md`. If it's missing or set to "not provided," stop with:

> "This skill needs the user's own LinkedIn URL. Run `skills/setup/` or add `user_linkedin_url` to `context/profile.md` manually, then retry."

Never ask for another URL at runtime — the user URL is a context concern, not a prompt concern.

---

## Step 1: Fetch the User's Recent Posts

Use the existing profile endpoint which returns a `posts` array:

```bash
skills/lead-enrichment/scripts/rapidapi-linkedin.sh "<user_linkedin_url>"
```

From the response, extract the `posts` array. Each post object should include a URL, an activity ID, a post date, and reaction totals. If the array contains fewer posts than the user asked for, use all available and note the gap.

Ask the user once (skip if already specified in the prompt):

> "How many recent posts to pull engagers from? (default: 10)"

Take the top N posts, most recent first. Print the list:

```
Pulling engagers from 10 posts:
  1. [2026-04-18] "Three things I stopped doing as a founder..."   (147 reactions)
  2. [2026-04-15] "A carousel on why Tier-1 founders post..."       (89 reactions)
  ...
```

If a post has zero reactions, skip it — no point querying an empty list.

---

## Step 2: Fetch Reactors Per Post

For each post URL, call the reactions endpoint and paginate until the page returns fewer items than the page size (or `currentPage >= totalPages`):

```bash
skills/post-engagers/scripts/rapidapi-post-reactions.sh "<post_url>" 1
skills/post-engagers/scripts/rapidapi-post-reactions.sh "<post_url>" 2
# ... until exhausted
```

**Rate limiting:** the linkedin-api8 tier limits vary. Pace at ~2 req/sec across calls. On HTTP 429, back off 10s and retry once; if still failing, stop that post's pagination and continue with the next post, noting the partial pull in the run summary.

**Token hygiene:** the full reactions JSON can be large. Process each response inline — extract only the fields you need, throw the rest away. Do not accumulate raw bodies in the main context.

Per reactor, extract:
- `name` (full name)
- `firstName`, `lastName` if available
- `headline` or `occupation`
- `profileUrl` → LinkedIn URL (this is the critical field — every downstream skill keys off it)
- `reactionType` (LIKE, CELEBRATE, SUPPORT, LOVE, INSIGHTFUL, FUNNY)
- `profilePicture` (optional, nice-to-have)

---

## Step 3: Deduplicate and Annotate

One person may react to multiple of the user's posts — that's stronger signal, not a duplicate row. Dedupe by `profileUrl` (canonicalized: strip query, hash, trailing slash, lowercase host). For each unique reactor, track:

- `engagement_count` — how many of the user's posts they reacted to in this pull
- `engaged_posts` — array of post URLs they reacted to
- `latest_engagement_date` — most recent reaction date
- `reaction_types` — unique set of reaction types they used

A reactor who hit **2+** of the user's posts is a stronger signal than a one-time liker. Flag them with `repeat_engager: true`.

---

## Step 4: Write the Raw CSV

**Path:** `outputs/[YYYY-MM-DD]-post-engagers-raw.csv`

**Columns:**

```
lead_id, name, first_name, last_name, headline, linkedin_url,
engagement_count, repeat_engager, latest_engagement_date,
reaction_types, engaged_posts, source
```

- `lead_id`: generate a stable id — `eng-[slug(name)]-[short hash of linkedin_url]` — so downstream skills can track this person across runs.
- `source`: literal `"post-engagers"`. The icp-scoring and enrichment skills may use this later to tune behavior.
- `reaction_types`: semicolon-joined (e.g. `"LIKE;INSIGHTFUL"`).
- `engaged_posts`: semicolon-joined list of post URLs.
- Empty fields stay empty (not the string `"null"`).
- UTF-8, RFC 4180. Names can contain commas and non-ASCII characters.

This CSV is the **input** to `skills/icp-scoring/` — do not try to score here. Separation of concerns: surfacing, scoring, enriching, sequencing, exporting are five distinct skills on purpose.

---

## Step 5: Run Summary

```
Post-engagers pull complete
  Posts queried:        10
  Posts with engagers:  9   (1 had zero reactions, skipped)
  Total reactor events: 1,284
  Unique engagers:      847
  Repeat engagers (2+): 112
  Top reactors (5+ posts engaged):  14

Output: outputs/2026-04-19-post-engagers-raw.csv
Next step: Read skills/icp-scoring/SKILL.md and score outputs/2026-04-19-post-engagers-raw.csv
```

Always print the "next step" line — it's the whole point of this skill.

---

## Quality Check

- [ ] `user_linkedin_url` was read from `context/profile.md` (not prompted for at runtime)
- [ ] Every row has a non-null `linkedin_url` — rows without one are useless downstream
- [ ] Dedup key is canonicalized (two rows with `linkedin.com/in/foo/` and `linkedin.com/in/foo/?utm=x` collapse to one)
- [ ] `engagement_count` and `repeat_engager` are populated correctly
- [ ] Raw JSON bodies are not in the final output — only the extracted fields
- [ ] Pagination terminated cleanly on every post (either reached last page, or explicitly noted as partial with reason)
- [ ] The "next step" line pointing at icp-scoring is printed

---

## Notes on Tiering

This skill intentionally surfaces **everyone** who reacted. Filtering by "only people whose headline matches our ICP" is tempting but premature — that's `icp-scoring`'s job, and it has richer context (the full ICP definition, tier rules, anti-ICP). Keeping the tiering out of this skill means a future change to ICP doesn't require re-running the API pulls.

Exception: if a reactor's profile URL resolves to a company page (`/company/foo`) rather than a person page (`/in/foo`), drop it — companies can't be DM'd as people.
