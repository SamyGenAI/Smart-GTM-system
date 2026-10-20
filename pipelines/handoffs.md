# Handoffs

Lists leave this repo as a CSV and a short summary. They go to Samy first, then to the Grok Bot GTM team for review.

No script sends a message, enrolls a sequence, posts, comments, or replies.

## Who reviews

| Role | What they receive | What they do not do automatically |
|---|---|---|
| Outbound Lead | The run summary and the sheet | Launch a campaign |
| Lead Sourcer | The find-leads and post-engager CSVs | Add people to a tool |
| Outbound Copywriter | Draft `dm_sequence_1` / `dm_sequence_2` plus `evidence` | Send or rewrite in place without Samy |
| Sequences & Deliverability | A reviewed list, only after Samy says the copy is final | Enroll anyone |
| Reply Manager | Nothing from these scripts | Read or answer a LinkedIn inbox |
| Deal Reactivation | Nothing from these scripts | Email closed deals |
| Social Engagement | The listening chat report | Like, comment, or post |

Grok Bot orchestrates that team. Claude Code, Codex, or Cursor run the pipelines in this repo. There is no enrichment inbox, no sequencer, and no LinkedIn inbox tool here yet.

## Where the work lands

- CSV for Google Sheets: `outputs/`
- Summary for the vault: `brain/outputs/gtm/<date>-<run>/summary.md`
- Hub page to update by hand in the vault, when Samy wants a log line: `brain/wiki/gtm-os.md`

`raw/` stays untouched.
