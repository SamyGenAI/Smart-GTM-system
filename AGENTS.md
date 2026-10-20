# GTM OS

This repo is Samy's **GTM OS**: lead generation, outreach prep, and sales research for The Smart Creator. The product is the Smart Operating System, an AI agent swarm on Grok Bot. The ICP is founders, creators, and knowledge workers who want to save time and spend less time in front of a screen.

One repo per OS. This repo is GTM. Content OS is `Smart-creator-design-system`. The shared brain is the private vault `https://github.com/SamyGenAI/Samy-SmartOS` (Karpathy LLM-wiki layout), checked out at `brain/`.

Grok Bot orchestrates. Claude Code, Codex, or Cursor do the work in this repo.

## Read the brain first

1. `brain/CLAUDE.md` — vault schema.
2. `brain/wiki/gtm-os.md` — GTM hub.
3. `brain/raw/me/offer.md` — offer, ICP, positioning. Required headings are listed in `context/README.md`.
4. `brain/raw/me/voice.md` and `brain/raw/me/proof.md` — voice and proof, for enrichment.
5. `context/signals/` — GTM-only watchlist and settings. Do not copy offer or ICP text into this repo.

`raw/` is immutable. Never edit it, and never commit vault content. A submodule stores a URL and a commit, nothing else.

If `brain/` is missing, stop and tell Samy to run:

```bash
git submodule add -b main https://github.com/SamyGenAI/Samy-SmartOS.git brain
```

The `.gitmodules` entry is already here. The gitlink is not, because this environment could not read the private vault. If Git says `brain` is already registered, delete the `[submodule "brain"]` block and run the add command again. After that commit exists, later clones use `git submodule update --init brain`.

## Pick a pipeline

Read `pipelines/` and run one flow. Do not invent a send step.

| Pipeline | Doc |
|---|---|
| Find leads | `pipelines/find-leads.md` |
| Score | `pipelines/score-leads.md` |
| Enrich (draft DMs only) | `pipelines/enrich-leads.md` |
| Post engagers | `pipelines/post-engagers.md` |
| Social listening / intent | `pipelines/social-listening.md` |
| Export to Sheets | `pipelines/export-to-sheets.md` |
| Who reviews the list | `pipelines/handoffs.md` |

Listening and intent always ask which source to run. They never run every source by default.

## Cost and approval

Paid scripts print Anthropic, Exa, and RapidAPI call counts and an approximate USD cost, then stop.

- Preview: `--estimate` or `--dry-run`
- Spend: `--confirm`, only after Samy approves the estimate

Do not make a paid call yourself to "try it". Do not add API keys. `.env.example` lists `ANTHROPIC_API_KEY`, `EXA_API_KEY`, and optional `RAPIDAPI_KEY`. Real keys stay in `.env`.

Nothing sends a message, enrolls a sequence, posts, comments, or replies.

## Outputs

- Lead CSV, UTF-8 with BOM, gitignored: `outputs/`
- Import that CSV into the Drive folder in `context/signals/gtm.md`
- Run summary (query, counts, top leads, estimated cost): `brain/outputs/gtm/<date>-<run>/summary.md`
- If the submodule is not checked out, the summary is staged in `outputs/gtm-pending/` and must be moved into the vault later

## Current priorities

- Keep ICP and positioning only in the brain, and fill the `offer.md` headings the scripts expect.
- Run find → score → enrich → export with an estimate before every paid step.
- Hand reviewed lists to the Grok Bot GTM team. No automatic sending.
