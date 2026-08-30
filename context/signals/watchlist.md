# Watchlist

Who to watch. One line each. Delete what you don't use.

Format is always `Name: handle`, except Reddit which is just the subreddit.
Blank sections are fine — scripts skip them.

Inside a section, only real entries are bare lines. Anything starting with
`>`, `-`, `*` or `#` is treated as a note and skipped.

## LinkedIn

> Read by `scripts/signals/social-listening.py --source linkedin` (Apify). Each line costs
> credits — a run scrapes up to `--per-source` posts per line (default 10).
> Run with `--dry-run` first to see `max_posts_scraped` before spending.
>
> Four URL shapes work here, mix them freely:
> - Person       https://www.linkedin.com/in/<handle>
> - Company      https://www.linkedin.com/company/<handle>
> - Keyword feed https://www.linkedin.com/search/results/content/?keywords=<term>
> - Single post  https://www.linkedin.com/posts/...-activity-...

> Replace the seed line below with real accounts.


Tim Scheuer: https://www.linkedin.com/in/tim-scheuer-91b005237
Nico Druelle: https://www.linkedin.com/in/nicolasdruelle
Alex Vacca: https://www.linkedin.com/in/alex-vacca
Fivos Aresti: https://www.linkedin.com/in/fivosaresti
Othman Khadri: https://www.linkedin.com/in/othmane-khadri-b48162236
Ruben Hassid: https://www.linkedin.com/in/ruben-hassid
Michel Lieben: https://www.linkedin.com/in/michel-lieben
Nate Herk: https://www.linkedin.com/in/nateherkelman

## X

> Read by `scripts/signals/social-listening.py --source x` (xAI Grok
> `x_search`). One API call per run, so lines here are cheap — but the tool
> accepts at most 20 accounts and extras are dropped with a warning.
>
> Either shape works: `Name: https://x.com/handle` or `Name: handle`.

Greg Isenberg: https://x.com/gregisenberg
Aakash Gupta: https://x.com/aakashgupta

## Reddit

> Read by `scripts/signals/social-listening.py --source reddit`. Free — no API
> key, no credits — so lines here cost nothing but run time. Each one pulls the
> subreddit's top and hot feeds; add `-q` to search a topic instead.
>
> Just the subreddit, no `Name:` prefix. `r/` optional.

r/gtmengineering
r/sales
r/SaaS
r/artificial
r/ClaudeCode
r/ArtificialInteligence
r/codex


## YouTube

> Read by `scripts/signals/social-listening.py --source youtube` (yt-dlp).
> Free — no API key, no credits — but needs `yt-dlp` installed:
> `python -m pip install yt-dlp`. Ranked by date, newest first, not by views.
> Pulls transcripts and top comments for the top `--enrich` videos.
>
> Either shape works: `Name: https://www.youtube.com/@handle` or `Name: @handle`.

Sanji Nai-Chien: https://www.youtube.com/@Sanji_Chien
Nate Herk: https://www.youtube.com/@nateherk
Ras Mic: https://www.youtube.com/@rasmic
Greg Isenberg: https://www.youtube.com/@GregIsenberg
Ben AI: https://www.youtube.com/@BenAI92


## Gmail

> Read by `skills/social-listening` via the Gmail connector — no script, no key.
> Free, and strictly read-only. Needs the Gmail connector authorized in your
> claude.ai settings.
>
> One newsletter per line — just the name, as you'd say it out loud. Claude
> finds the sending addresses itself, including the several a writer with
> multiple publications sends from.
>
> Only newsletters named here, plus the promotions/updates categories, are ever
> read — the primary inbox stays out of scope. Ranked by date, newest first.
>
> Not connected? Claude offers to walk you through it; decline and the source
> is skipped.

Aakash Gupta — Product Growth
AlphaSignal
Lenny's Newsletter
Sabahudin from Unstuck



## Web

> Read by `scripts/signals/social-listening.py --source web`.
> Free on the keyless floor (DuckDuckGo/Startpage); uses Brave, Exa, Serper or
> Parallel instead when the matching key is in `.env`. Ranked by date, newest
> first — the open web has no engagement count.
>
> One domain per line as `Name: domain.com`. Each becomes a `site:` query, so
> the run surfaces what that competitor published. `-q` searches the open web
> instead, and narrows to these domains when both are given.

Clay: clay.com
Lemlist: lemlist.com
Anthropic: anthropic.com
OpenAI: openai.com
Grok: x.ai
