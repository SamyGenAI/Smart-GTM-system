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
4. For each context file, read the corresponding template to understand the required structure, then create the adapted file alongside it — never modify the template:

| Template (read, never touch) | Adapted file (create/overwrite with real data) |
|------------------------------|------------------------------------------------|
| `context/profile/profile-template.md` | `context/profile/profile.md` |
| `context/icp-definition/icp-definition-template.md` | `context/icp-definition/icp-definition.md` |
| `context/positioning/positioning-template.md` | `context/positioning/positioning.md` |
| `context/brief/brief-template.md` | `context/brief/brief.md` |
| `context/competitor-radar/competitor-radar-template.md` | `context/competitor-radar/competitor-radar.md` |

5. Update `CLAUDE.md` with the user's company name, GTM motion, and current priorities.

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

- [ ] All `*-template.md` files are untouched — no edits, no overwrites.
- [ ] `context/profile/profile.md` exists and is populated (LinkedIn URL, company details).
- [ ] If RapidAPI data is available, LinkedIn profile details are filled under `User's LinkedIn profile`.
- [ ] `context/icp-definition/icp-definition.md` and `context/positioning/positioning.md` are filled from profile, answers, and website content.
- [ ] `context/brief/brief.md` contains a concise offer + ICP summary (max ~150 words).
- [ ] `context/competitor-radar/competitor-radar.md` is filled with competitor details from question 5.
- [ ] `CLAUDE.md` is personalized to user and company info.

## Rules

- **Never edit a `*-template.md` file.** Templates are read-only reference files. Always write user data into the adapted `*.md` file (same name, no `-template` suffix).
- Never infer a fact — all data stored must be accurate based on: user answers, LinkedIn profile, and website content.
- If information is missing, leave the field blank or note `[unknown]`. Never guess or invent.
- Be concise — only keep data that is useful for specialized outreach.

## Next command

```
Give a prompt example to the user, "Using skills/find-leads/SKILL.md find 25 leads matching my ICP".
```
