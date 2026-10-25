# Smart Creator GTM OS

Lead generation, outreach prep, and sales research for [The Smart Creator](https://github.com/SamyGenAI). Samy sells the Smart Operating System, an AI agent swarm on Grok Bot, to founders, creators, and knowledge workers who want less time in front of a screen.

This repo finds and scores leads, drafts LinkedIn DMs, and exports a CSV for Google Sheets. It does not send messages, enroll sequences, or post.

Grok Bot orchestrates. Claude Code, Codex, or Cursor run the work. Content lives in the Content OS repo (`Smart-creator-design-system`). The shared brain is the private vault [Samy-SmartOS](https://github.com/SamyGenAI/Samy-SmartOS).

## Structure

```text
brain/                 private vault submodule (raw/ is immutable)
context/signals/       GTM-only watchlist and settings (not the offer or ICP)
context/README.md      headings offer.md must have
pipelines/             one doc per flow, plus handoffs
scripts/               find, score, enrich, export, post engagers, listening
skills/                slash-command instructions for the agent
outputs/               CSV for Google Sheets (gitignored) and pending summaries
inputs/                connections and post-engager drops
.env.example           key names only
```

| Path | What it is |
|---|---|
| `brain/raw/me/offer.md` | Source for offer, ICP, positioning |
| `brain/raw/me/voice.md`, `proof.md` | Voice and proof for draft DMs |
| `brain/wiki/gtm-os.md` | GTM hub |
| `brain/outputs/gtm/<date>-<run>/` | Run summary |
| `pipelines/` | Inputs, command, cost, output, review gate |
| `context/signals/gtm.md` | Sheets folder and review rule |

## Quick start

1. Clone this repo and open the folder that contains this README.
2. Link the brain (needs access to the private vault):

```bash
git submodule add -b main https://github.com/SamyGenAI/Samy-SmartOS.git brain
git submodule update --init brain
```

`.gitmodules` already records the URL and branch. `git submodule add` still has to record the vault commit. If Git says `brain` is already registered, delete the `[submodule "brain"]` block from `.gitmodules` and run the add command again.

3. Copy keys into `.env` (this file stays local):

```bash
cp .env.example .env
```

`ANTHROPIC_API_KEY` and `EXA_API_KEY` are required for paid lead runs. `RAPIDAPI_KEY` is optional (LinkedIn profile and post engagers).

4. Install dependencies. `node_modules` is not in git.

```bash
npm install
```

5. In the vault, fill the headings in `brain/raw/me/offer.md` listed in `context/README.md`. Do not copy that text into this repo.
6. Preview cost, then run only after you accept it:

```bash
node scripts/find_leads_exa.mjs -q "your query from the ICP" -n 25 --estimate
node scripts/find_leads_exa.mjs -q "your query from the ICP" -n 25 --confirm
```

Then score, enrich, and export. Each paid step has the same `--estimate` then `--confirm` rule. The docs are in `pipelines/`.

Import `outputs/<date>-<campaign>-leads.csv` into the [lead-table Drive folder](https://drive.google.com/drive/folders/1JuNMJvV8uTT9o41m8TpZLO5F0tuh3Jow).

## Pipelines

| Step | Doc | Spends money? |
|---|---|---|
| Find leads | `pipelines/find-leads.md` | Exa, after `--confirm` |
| Score | `pipelines/score-leads.md` | Anthropic, after `--confirm` |
| Enrich | `pipelines/enrich-leads.md` | Anthropic, after `--confirm` |
| Post engagers | `pipelines/post-engagers.md` | RapidAPI, after `--confirm` |
| Intent signals | `skills/intent-signals/SKILL.md` | No (demo source only) |
| Export to Sheets | `pipelines/export-to-sheets.md` | No |
| Review handoff | `pipelines/handoffs.md` | No sending |

Slash commands in `.claude/commands/` and `.cursor/commands/` point at `skills/`. The agent reads the brain, picks one pipeline, estimates, and waits.

## Safety

- `--estimate` / `--dry-run` prints Anthropic, Exa, and RapidAPI call counts and an approximate cost. No paid call.
- Paid runs need `--confirm`.
- Draft DMs stay in the CSV until a person reviews them.
- Lists go to the Grok Bot GTM team only after that review (`pipelines/handoffs.md`).
- Do not commit `.env`, CSVs, or anything from `brain/raw/`.

## Brain submodule

This copy records the vault in `.gitmodules` only. The private repo was not readable here, so there is no gitlink and `brain/` is not populated. From a machine that can read `SamyGenAI/Samy-SmartOS`:

```bash
git submodule add -b main https://github.com/SamyGenAI/Samy-SmartOS.git brain
```

If Git says `brain` is already in `.gitmodules`, delete that stanza and run the command again. That writes the gitlink. Later clones use `git submodule update --init brain`.

Until that works, run summaries are written to `outputs/gtm-pending/` instead of `brain/outputs/gtm/`.

## License

MIT
