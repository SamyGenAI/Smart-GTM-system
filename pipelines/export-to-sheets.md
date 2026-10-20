# Export to Sheets

Turn a scored or enriched CSV into one Sheets-ready file. No API call.

## Inputs

- The enriched CSV, or a scored CSV if you only need fit and not drafts.
- Campaign label for the filename.

## Command

```bash
node scripts/export_leads.mjs -i outputs/2026-10-20-leads-enriched.csv -c founders -s 60
```

There is no `--confirm` flag. This step spends nothing.

## Cost

- Anthropic: 0
- Exa: 0
- RapidAPI: 0

## Output

- CSV, UTF-8 with BOM: `outputs/<date>-<campaign>-leads.csv`
- Columns: `lead_id,name,headline,linkedin_url,score,tier,why_match,outreach_angle,dm_sequence_1,dm_sequence_2,evidence,source`
- Run summary: `brain/outputs/gtm/<date>-export-<campaign>/summary.md`

Import the CSV into the lead-table folder:

https://drive.google.com/drive/folders/1JuNMJvV8uTT9o41m8TpZLO5F0tuh3Jow

The folder URL is also in `context/signals/gtm.md`. CSVs are gitignored.

## Review gate

Samy imports the sheet and checks the top rows in the summary. The sheet is not a sequence. See `pipelines/handoffs.md`.
