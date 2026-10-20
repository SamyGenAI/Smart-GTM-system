# Enrich leads

Research leads at or above a score and draft two LinkedIn DMs. Drafts stay in the CSV.

## Inputs

- A scored CSV with a `score` column.
- `brain/raw/me/offer.md` (`## Offer`, `## ICP`, `## Positioning`, `## Anti-ICP`).
- `brain/raw/me/voice.md` and `brain/raw/me/proof.md` when they exist. Each is clipped to 1500 characters.
- `ANTHROPIC_API_KEY` once the run is confirmed.

## Command

```bash
node scripts/enrich_leads_haiku.mjs -i outputs/2026-10-20-leads-scored.csv -o outputs/2026-10-20-leads-enriched.csv -s 60 --web-searches 1 --estimate
node scripts/enrich_leads_haiku.mjs -i outputs/2026-10-20-leads-scored.csv -o outputs/2026-10-20-leads-enriched.csv -s 60 --web-searches 1 --confirm
```

## Cost

- Anthropic: 1 Messages call per lead at or above `--min-score` (default 60), capped by `--max-leads`
- Anthropic web search: up to `--web-searches` per lead (default 1)
- Exa: 0
- RapidAPI: 0

The estimate counts eligible rows locally and prints the dollar figure before any call.

## Output

- CSV plus `outreach_angle`, `dm_sequence_1`, `dm_sequence_2`, `evidence`
- Run summary: `brain/outputs/gtm/<date>-enrich-leads/summary.md`

Empty DM columns mean no sourced signal. That is a valid result.

## Review gate

Samy reads the drafts and the evidence URLs. This step does not send, connect, or follow up.
