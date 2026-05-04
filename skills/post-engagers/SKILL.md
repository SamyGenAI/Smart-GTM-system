# Skill: Post Engagers (RapidAPI)

**Duration:** 2-8 minutes  
**Output:** `outputs/[date]-post-engagers-raw.csv`

## Quick Start

```
Read skills/post-engagers/SKILL.md and pull engagers from my last [N] posts.
```

## Purpose

Pull people who reacted to a LinkedIn post and turn them into warm leads.

## Dependencies

- `context/profile.md` contains `user_linkedin_url`
- `RAPIDAPI_KEY` in `.env`
- Uses only RapidAPI scripts:
  - `skills/post-engagers/scripts/rapidapi-linkedin.sh`
  - `skills/post-engagers/scripts/rapidapi-post-reactions.sh`

## Output Columns

```
lead_id,name,headline,linkedin_url,engagement_count,repeat_engager,latest_engagement_date,reaction_types,engaged_posts,source
```

- `source` is always `post-engagers`.
- Keep only person URLs (`linkedin.com/in/`).

## Run Summary

Always print:

```
Post-engagers pull complete.
Output: outputs/[date]-post-engagers-raw.csv
Next step: Read skills/score-leads/SKILL.md and score this list with Claude Haiku.
```
