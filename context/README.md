# Context

ICP, positioning, voice, and proof are **not** stored in this repo.

They live in the private vault, checked out as `brain/`:

| File | Role |
|---|---|
| `brain/raw/me/offer.md` | Offer, ICP, anti-ICP, positioning. Scoring and enrichment read this. |
| `brain/raw/me/voice.md` | How Samy sounds. Enrichment clips this into the DM prompt. |
| `brain/raw/me/proof.md` | Proof points. Enrichment clips this into the DM prompt. |
| `brain/wiki/gtm-os.md` | GTM hub. Read it before a run. |
| `brain/CLAUDE.md` | Vault schema. |

`raw/` is immutable. Never edit it from this repo, and never paste its text into a local file.

## Headings `offer.md` must have

Scripts match these as level-2 headings (`##`, exact text).

**Required.** Score and enrich stop until all four exist:

- `## Offer` — what is sold, and the outcome for the buyer
- `## ICP` — who to pursue (role, stage, size, the signal that makes them a fit)
- `## Anti-ICP` — who to exclude
- `## Positioning` — how to talk about the offer, including what not to say

**Optional.** Used when present, ignored when absent:

- `## Geography` — where they are. Included in the scoring rubric.
- `## Buyer` — the person who decides. Included in the scoring rubric.
- `## Scoring` — replaces the default 0–100 bands (80–100 strong, 60–79 decent, 40–59 weak, 0–39 exclude).
- `## LinkedIn` — Samy's profile URL, one line. Setup and post-engagers look here.
- `## Competitors` — names or domains. Not copied into the watchlist; add operational watches in `context/signals/watchlist.md`.

`voice.md` and `proof.md` have no required headings. Enrichment sends each file, clipped to 1500 characters.

## What stays local

`context/signals/` is GTM-only: who to watch, what counts as a signal, and the Sheets folder. It does not repeat the offer.
