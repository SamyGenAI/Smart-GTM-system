# Social listening and intent signals

What the watchlist is saying, and (separately) demo intent signals. Reports in chat. No lead CSV.

## Inputs

- `context/signals/watchlist.md` — who to watch. GTM-only. Not a copy of the ICP.
- `context/signals/signals.md` — optional ranking rules. Copy from `signals-template.md`.
- Fit is judged against `## ICP` in `brain/raw/me/offer.md`. Read that heading. Do not paste it into the watchlist.

Ask which source to run. Do not run every source.

## Command

```bash
python scripts/signals/social-listening.py --source reddit --dry-run
python scripts/signals/social-listening.py --source linkedin --dry-run
python scripts/signals/social-listening.py --source linkedin --confirm
python scripts/signals/intent/demo.py --dry-run
```

`--estimate` is the same as `--dry-run`.

## Cost

| Source | Paid? | Gate |
|---|---|---|
| LinkedIn (Apify) | yes, per post | `--confirm` |
| X (xAI, one call) | yes | `--confirm` |
| Web with Brave, Exa, Serper, or Parallel | yes, per query | `--confirm` |
| Web keyless, Reddit, YouTube without Gemini | no | `--dry-run` optional |
| YouTube with `GEMINI_API_KEY` | Gemini may read caption-less videos | `--confirm`, or `--no-gemini` to stay free |
| Intent demo | no | fabricated `[DEMO]` rows |

Gmail has no script. Read it through the Gmail connector, newsletters only, and never label, delete, or email anyone else.

## Output

Chat report. Listening does not write a lead CSV. A paid run still prints call counts and an approximate cost before it spends.

## Review gate

Samy decides which signal is worth a find-leads query. The script does not draft or send outreach from a post.
