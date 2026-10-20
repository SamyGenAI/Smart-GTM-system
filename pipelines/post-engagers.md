# Post engagers

Pull people who reacted to LinkedIn posts. Warm list, still not a send.

## Inputs

- One or more post URLs, or a text file with one URL per line.
- `RAPIDAPI_KEY` once the run is confirmed (linkedin-api8).
- Samy's own profile URL, if you need it, is `## LinkedIn` in `brain/raw/me/offer.md`. The script does not read it; you pass post URLs.

## Command

```bash
node scripts/rapidapi_post_reactions.mjs --urls "https://www.linkedin.com/posts/..." --max-pages 5 --estimate
node scripts/rapidapi_post_reactions.mjs --urls "https://www.linkedin.com/posts/..." --max-pages 5 --confirm
```

A single profile lookup is the same rule: one RapidAPI call, `--estimate` then `--confirm`.

```bash
node scripts/rapidapi_linkedin_profile.mjs "https://www.linkedin.com/in/handle" --estimate
```

## Cost

- RapidAPI: up to `posts × max-pages` (default 5 pages). The live run stops early when a page is empty.
- About $0.005 per request, plan-dependent. The script prints the upper bound.
- Anthropic: 0
- Exa: 0

## Output

- CSV: `inputs/post-engagers/<date>-post-engagers-raw.csv`
- Run summary: `brain/outputs/gtm/<date>-post-engagers/summary.md`

Next pipeline is score, then enrich, then export. Engagers are not enrolled in anything.

## Review gate

Samy looks at repeat engagers before scoring. No InMail, no comment, no reaction is posted.
