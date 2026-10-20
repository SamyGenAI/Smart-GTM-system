---
name: setup
description: Run once after cloning. Checks the brain submodule, .env, and the offer.md headings. Does not copy ICP or offer text into this repo. Triggers on /setup or "set up this repo".
---

# Skill: Setup

**Run once** after clone. Goal: the repo can estimate a lead run.

## Steps

1. If `.env` is missing, tell the user to copy `.env.example` to `.env` and fill:
   - `ANTHROPIC_API_KEY` (score + enrich)
   - `EXA_API_KEY` (find leads)
   - `RAPIDAPI_KEY` (optional: profile pull and post engagers)
   Wait until they say the file is saved. Never write a key into the repo.

2. If `brain/raw/me/offer.md` is missing, stop. Give them:

```bash
git submodule add -b main https://github.com/SamyGenAI/Samy-SmartOS.git brain
git submodule update --init brain
```

Do not vendor the vault and do not edit `raw/`.

3. Read `brain/raw/me/offer.md` and check the headings in `context/README.md`. Required: `## Offer`, `## ICP`, `## Anti-ICP`, `## Positioning`. If one is missing, name it and stop. Samy fills it in the vault.

4. Read `brain/wiki/gtm-os.md` if it exists, and `context/signals/gtm.md`. Do not create `context/icp-definition/`, `context/positioning/`, `context/brief/`, or `context/profile/`. Those files used to duplicate the offer.

5. Optional: `## LinkedIn` in offer.md is the profile URL. A profile pull is one RapidAPI call. Estimate first:

```bash
node scripts/rapidapi_linkedin_profile.mjs "<linkedin-url>" --estimate
```

Only add `--confirm` after Samy accepts the estimate. Parsing the saved JSON with `scripts/parse_linkedin_profile.mjs` is local and free.

6. Watchlist: `context/signals/watchlist.md` is already the GTM watchlist. Do not paste the ICP into it.

## Done when

- `.env` exists locally and is not committed.
- `brain/raw/me/offer.md` has the four required headings.
- No offer or ICP text was written under `context/`.
- Samy has seen an example: estimate a find-leads run, then confirm.

## Next

`pipelines/find-leads.md`
