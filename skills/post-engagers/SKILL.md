---
name: post-engagers
description: Pull warm leads from LinkedIn post reactions using RapidAPI (linkedin-api8). Extracts people who reacted to one or more posts and outputs a scored-ready CSV in inputs/post-engagers/. Requires RAPIDAPI_KEY. Triggers on /post-engagers or any message like "pull post engagers", "get people who reacted to my posts", "warm leads from LinkedIn", or "extract post reactions".
---

# Skill: Post Engagers (RapidAPI)

**Duration:** 2-8 minutes  
**Output:** `inputs/post-engagers/[date]-post-engagers-raw.csv`

## Quick Start

```
Read skills/post-engagers/SKILL.md and pull engagers from my last [N] posts.
```

## Purpose

Pull people who reacted to a LinkedIn post and turn them into warm leads.

## Dependencies

- Samy's profile URL, when needed, is the `## LinkedIn` heading in `brain/raw/me/offer.md`
- `RAPIDAPI_KEY` in `.env`
- Scripts:
  - `scripts/rapidapi_post_reactions.mjs` — fetch post reactions → CSV in `inputs/post-engagers/`
  - `scripts/rapidapi_linkedin_profile.mjs` — fetch a single LinkedIn profile (JSON)

## Output Columns

```
lead_id,name,headline,linkedin_url,engagement_count,repeat_engager,latest_engagement_date,reaction_types,engaged_posts,source
```

- `source` is always `post-engagers`.
- Keep only person URLs (`linkedin.com/in/`).

## Quick Commands

```bash
# Pull reactions from specific posts (comma-separated URLs)
node scripts/rapidapi_post_reactions.mjs \
  --urls "https://www.linkedin.com/posts/HANDLE_activity-XXXX,https://www.linkedin.com/posts/HANDLE_activity-YYYY" \
  --max-pages 5 \
  --estimate

# Pull from a text file with one URL per line
node scripts/rapidapi_post_reactions.mjs \
  --urls-file inputs/post-engagers/post-urls.txt \
  --max-pages 5

# Fetch a single LinkedIn profile (JSON to stdout)
node scripts/rapidapi_linkedin_profile.mjs adamselipsky

# Score the engager CSV immediately after
node scripts/score_leads_haiku.mjs \
  -i inputs/post-engagers/[date]-post-engagers-raw.csv \
  -o outputs/[date]-post-engagers-scored.csv \
  -b 8
```

## Run Summary

Always print:

```
Post-engagers pull complete.
Output: inputs/post-engagers/[date]-post-engagers-raw.csv
Next step: Read skills/score-leads/SKILL.md and score this list with Claude Haiku.
```
