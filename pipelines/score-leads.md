# Score leads

Score a CSV 0–100 against the ICP in the brain.

## Inputs

- A lead CSV from find-leads, `inputs/connections/`, or `inputs/post-engagers/`.
- `brain/raw/me/offer.md` with `## ICP`, `## Anti-ICP`, and `## Positioning`. Optional: `## Geography`, `## Buyer`, `## Scoring`.
- `ANTHROPIC_API_KEY` once the run is confirmed.

The rubric sent to the model is built from those headings. This repo does not keep a second copy of the ICP.

## Command

```bash
node scripts/score_leads_haiku.mjs -i outputs/2026-10-20-find-leads.csv -o outputs/2026-10-20-leads-scored.csv -b 20 --estimate
node scripts/score_leads_haiku.mjs -i outputs/2026-10-20-find-leads.csv -o outputs/2026-10-20-leads-scored.csv -b 20 --confirm
```

## Cost

- Anthropic: one Messages call per batch (`-b`, default 20)
- Exa: 0
- RapidAPI: 0
- Haiku token estimate is printed before the run (`scripts/lib/costs.mjs`)

## Output

- Scored CSV, same rows plus `score` and `why_match`: the `-o` path
- Run summary with the top leads: `brain/outputs/gtm/<date>-score-leads/summary.md`

Tiers are not a column here. Export derives them: 80–100 tier1, 60–79 tier2, 40–59 tier3, below that exclude.

## Review gate

Samy checks tier1 and tier2 before enrichment. A low score is not contacted to "see what happens".
