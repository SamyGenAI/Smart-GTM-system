# Find leads

Search Exa for people or companies. One search, one query.

## Inputs

- A query Samy wrote after reading `## ICP` in `brain/raw/me/offer.md`. The script does not send the ICP text to Exa.
- `EXA_API_KEY` in `.env` (only needed once the run is confirmed).

## Command

```bash
node scripts/find_leads_exa.mjs -q "founders who want time off the screen" -n 25 --estimate
node scripts/find_leads_exa.mjs -q "founders who want time off the screen" -n 25 --confirm
```

`--estimate` and `--dry-run` print the call count and stop. `--confirm` is required before the Exa call.

## Cost

- Exa: 1 call
- Anthropic: 0
- RapidAPI: 0
- About $0.007 (see `scripts/lib/costs.mjs`)

## Output

- CSV (UTF-8 with BOM, ready for Google Sheets): `outputs/<date>-find-leads.csv`
- Run summary: `brain/outputs/gtm/<date>-find-leads/summary.md`

Columns: `rank,category,query,title,url,snippet,highlights`

## Review gate

Samy reads the summary and the CSV before anyone is scored. Nothing is contacted.
