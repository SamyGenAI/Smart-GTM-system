# Skill: Export List

**Duration:** 10–60 seconds (network-bound if Notion is selected)
**Output:** `outputs/[date]-[campaign]-list.csv` (always), optional Notion database row upsert.

---

## Quick Start

```
Read skills/export-list/SKILL.md and export outputs/[date]-[campaign]-sequenced.json
```

Steps 6 + 7 of the workflow, fused into one skill. CSV always. Notion on request.

---

## Purpose

Take the fully processed list (enriched + sequenced) and publish it. The CSV drops to `outputs/` so the user can paste it into whatever tool they actually send from (Instantly, Smartlead, a LinkedIn tool, a spreadsheet). Notion is for keeping a master table of what's in flight across campaigns — optional because not every user has a Notion workspace configured.

The skill is a thin adapter. No data is transformed beyond flattening the JSON; no decisions are made about content. Everything that had to be decided was decided upstream.

---

## Inputs

- Sequenced JSON from `skills/lead-sequence/` (one object per lead, with `touches` array)
- If Notion is requested: `Notion` MCP connected **and** either:
  - A target database URL/ID provided in the prompt, or
  - A saved default in `context/profile.md` under `notion_lists_database`

---

## Step 0: Ask About Notion

CSV always runs. Notion is optional.

If the prompt already says "also push to Notion" or "CSV only," skip the question. Otherwise ask once:

> "CSV will be saved to outputs/. Also push this list to Notion? (y/n)"

If yes and no database ID is set, ask:

> "Which Notion database? Paste a URL or database ID, or tell me to save one as default in `context/profile.md`."

Record the choice — `notion: true/false` — and proceed.

---

## Step 1: CSV Export (always)

**Path:** `outputs/[YYYY-MM-DD]-[campaign-slug]-list.csv`

If the user didn't supply a campaign slug, derive it from the input filename (e.g. `2026-04-19-tier1-founders-sequenced.json` → `2026-04-19-tier1-founders-list.csv`).

**Columns (in this order):**

```
lead_id, name, first_name, last_name, linkedin_url, linkedin_username,
current_title, current_company, current_company_domain,
company_headcount, company_hq_country, company_year_founded, company_total_funding_usd,
location, country_code,
email, email_source, phone, phone_source,
linkedin_followers, linkedin_connections, linkedin_is_creator, linkedin_is_top_voice,
posts_last_90d, avg_reactions, tier1_inconsistent_poster,
recent_company_jobs_count, hiring_content_or_growth_role,
run_mode, sequence_status, sequence_hook, sequence_angle,
touch1_channel, touch1_day, touch1_subject, touch1_body,
touch2_channel, touch2_day, touch2_subject, touch2_body,
touch3_channel, touch3_day, touch3_subject, touch3_body,
source_rapidapi, source_orthogonal, source_crustdata_person,
source_crustdata_company, source_crustdata_jobs,
notes
```

**Rules:**
- Flatten `touches[0..2]` into `touch{n}_*` columns. If the sequence has fewer than 3 touches, leave remaining `touch{n}_*` cells empty.
- `notes` is `";"` joined if the lead has multiple notes.
- Null JSON values → empty CSV cell (not the string `"null"`).
- CSV is UTF-8, RFC 4180 compliant: quote fields containing `,`, `"`, or newlines; escape inner `"` as `""`. Message bodies contain commas and line breaks — this matters.

**Do not drop leads.** `sequence_status: "insufficient_data"` and `"needs_rewrite"` rows still go in the CSV, with empty touch cells and the status column flagging them. The user filters in their tool.

Print the path when done:

```
CSV written: outputs/2026-04-19-tier1-founders-list.csv  (147 rows)
```

---

## Step 2: Notion Push (only if user said yes)

Use the Notion MCP tools (`mcp__claude_ai_Notion__*`). If the MCP isn't connected, tell the user:

> "Notion MCP isn't connected. CSV is saved — skipping Notion. To enable: connect the Notion integration, then re-run with 'also push to Notion'."

**Database handling:**

1. **Resolve target database.** Use the URL/ID from the prompt or `context/profile.md`. If neither, stop and ask — don't guess.

2. **Inspect the schema.** Call `notion-fetch` on the database to read its existing properties. Build a mapping from CSV columns to Notion property names.
   - If a property the CSV needs (e.g. `touch1_body`) doesn't exist, **don't silently drop it**. Options:
     - Ask the user: "The Notion database is missing these properties: [list]. Add them, or skip those fields for this push?"
     - If the user says "add them," use `notion-update-data-source` to add the missing properties with appropriate types (rich_text for bodies, number for counts, checkbox for booleans, URL for links, select for enums like `run_mode` / `sequence_status`).

3. **Upsert by `lead_id`.**
   - Query the database for existing rows where `lead_id` matches.
   - For matches: update via `notion-update-page`.
   - For new rows: create via `notion-create-pages`.
   - Never delete rows — even if a lead was in a prior push but isn't in this one, leave it.

4. **Batch.** Notion rate-limits ~3 req/sec. Batch page creation in groups of 10 with a 400ms pause between batches. On 429, back off 5s and retry once.

**Property type hints for the mapper:**

| CSV column(s) | Notion type |
|---|---|
| `lead_id` | title (the row's primary) |
| `name`, `first_name`, `last_name`, `current_title`, `current_company`, `location`, `sequence_hook`, `sequence_angle` | rich_text |
| `linkedin_url`, `current_company_domain`, `touch{n}_url`-style | url |
| `email`, `email_source`, `phone`, `phone_source` | email / phone_number / rich_text |
| `company_headcount`, `company_total_funding_usd`, `posts_last_90d`, `recent_company_jobs_count`, `avg_reactions`, `linkedin_followers`, `linkedin_connections` | number |
| `tier1_inconsistent_poster`, `hiring_content_or_growth_role`, `linkedin_is_creator`, `linkedin_is_top_voice` | checkbox |
| `run_mode`, `sequence_status`, `source_*` | select |
| `touch{n}_body`, `touch{n}_subject`, `notes` | rich_text |

Notion rich_text is limited to 2000 chars per block. If a body exceeds that, truncate with a `…` suffix and note the truncation in `notes`.

Print on done:

```
Notion push complete: 128 upserted, 19 created, 0 errors
Database: [URL]
```

---

## Step 3: Error Handling

The skill degrades toward CSV, never away from it.

| Failure | Behavior |
|---|---|
| Input JSON malformed | Stop before writing CSV. Print the validation error and the offending lead_id. |
| CSV write fails (disk full, permissions) | Hard fail. This is the primary output. |
| Notion MCP not connected | CSV succeeds. Skip Notion with the message above. |
| Notion property mismatch, user declines to auto-add | CSV succeeds. Push the properties that do match, list the skipped ones in the run summary. |
| Notion 429 / 5xx on a specific row | Retry once with backoff. If still failing, log that row's `lead_id` and continue — one bad row shouldn't kill the push. Final summary shows error count. |

---

## Output / Run Summary

```
Export complete — 147 leads
  CSV:    outputs/2026-04-19-tier1-founders-list.csv
  Notion: 128 upserted, 19 created, 0 errors   (or: skipped)
By status: 128 ready, 11 insufficient_data, 8 needs_rewrite
Run mode (from enrichment): linkedin
```

---

## Quality Check

- [ ] CSV file exists at `outputs/[date]-[slug]-list.csv` and row count matches input lead count
- [ ] Every input lead is in the CSV (including `insufficient_data` and `needs_rewrite` — not silently dropped)
- [ ] CSV is RFC 4180 valid — message bodies with commas/quotes/newlines don't break downstream parsers
- [ ] If Notion ran: upsert by `lead_id` worked (no duplicates); property mismatches were surfaced not silently dropped
- [ ] If Notion didn't run: the user was told why (not requested, MCP off, or errored)
- [ ] Run summary prints at the end with the exact CSV path
