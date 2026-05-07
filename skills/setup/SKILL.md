# Skill: Setup

**Run once:** right after clone  
**Goal:** make the repo usable in 10-15 minutes

## Quick Start

```
Read skills/setup/SKILL.md and set up this repo for [your-domain.com]
```

## What setup does

1. Capture your LinkedIn profile URL and business website
2. If `RAPIDAPI_KEY` exists, fetch LinkedIn profile once with:

```bash
node scripts/rapidapi_linkedin_profile.mjs "<your_linkedin_url>"
```
3. Use websearch to get as much details as possible from `<your_website_url>`
4. Write/update:
   - `context/profile.md`
   - `context/icp-definition.md`
   - `context/positioning.md`
   - `context/brief.md`
   - `competitor-radar.md`
   - `CLAUDE.md`

## Required question 1

Ask once:

> "Paste your LinkedIn profile URL (or reply 'skip')."

## Required question 2

Ask once:

> "What is your business website URL ? (or reply 'skip')."

## Required question 3

Ask once:

> "2 more questions, what service or product are you selling ? (or reply 'skip')."

## Required question 4

Ask once:

> "Who is your ideal client ? (or reply 'skip')."

## Required question 5

Ask once:

> "Last one, who are your competitors ? (provide their website URLs or reply 'skip')."


## Output checklist

- [ ] `your_linkedin_url` saved in `context/profile.md`
- [ ] If RapidAPI data is available, user's LinkedIn profile details are filled in `context/profile.md` under `User's LinkedIn profile` section
- [ ] Business details and `<your_website_url>` are saved in `context/profile.md` under `The Company` section.
- [ ] `context/icp-definition.md` and `context/positioning.md` are filled using details from Linkedin profile, user answers and website content.
- [ ] `context/competitor-radar.md` is filled with competitor details from question 5
- [ ] `CLAUDE.md` is personalized to user and company info.

## Rules

- Never infer a fact, all data stored must be accurate based on : user answers, Linkedin profile and website content.
- If an information is missing, don't try to guess it or to invent it
- Be concise, we must only keep useful data for specialized outreach.

## Next command

```
Give a prompt example to the user, "Using skills/find-leads/SKILL.md find 25 leads matching my ICP".
```
