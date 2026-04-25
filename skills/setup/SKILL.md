# Skill: Setup (Dead Simple)

**Run once:** right after clone  
**Goal:** make the repo usable in 10-15 minutes

## Quick Start

```
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]
```

## What setup does

1. Capture your LinkedIn profile URL
2. If `RAPIDAPI_KEY` exists, fetch your profile once with:

```bash
skills/post-engagers/scripts/rapidapi-linkedin.sh "<your_linkedin_url>"
```

3. Write/update:
   - `context/profile.md` (`user_linkedin_url`, headline, followers, voice sample)
   - `context/icp-definition.md`
   - `context/positioning.md`
   - `CLAUDE.md`

## Required question

Ask once:

> "Paste your LinkedIn profile URL (or reply 'skip')."

## Output checklist

- [ ] `user_linkedin_url` saved in `context/profile.md`
- [ ] If RapidAPI data is available, store headline + followers + short voice sample
- [ ] `CLAUDE.md` quick commands match the dead-simple workflow

## Next command

```
Read skills/find-leads/SKILL.md and find 25 leads matching our Tier 1 ICP.
```
