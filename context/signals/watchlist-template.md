# Watchlist

Who to watch. One line each. Delete what you don't use.

Format is always `Name: handle`, except Reddit which is just the subreddit.
Blank sections are fine — scripts skip them.

## LinkedIn

Jane Doe: https://linkedin.com/in/janedoe
Acme Corp: https://linkedin.com/company/acme

## X

Jane Doe: https://x.com/janedoe
Acme Corp: https://x.com/acme

## Reddit

Read by `--source reddit`. Free — no key, no credits. Just the subreddit.

r/sales
r/SaaS

## YouTube

Read by `--source youtube`. Free, but needs `pip install yt-dlp`.

Acme Corp: https://youtube.com/@acme

## Substack

Some Newsletter: https://somenewsletter.substack.com

## Newsletters

Some Roundup: https://example.com/newsletter

## Web

> Read by `scripts/signals/social-listening.py --source web`.
> Free on the keyless floor (DuckDuckGo/Startpage); uses Brave, Exa, Serper or
> Parallel instead when the matching key is in `.env`. Ranked by date, newest
> first — the open web has no engagement count.
>
> One domain per line as `Name: domain.com`. Each becomes a `site:` query, so
> the run surfaces what that competitor published. `-q` searches the open web
> instead, and narrows to these domains when both are given.


Acme Corp: https://acme.com

## Companies

Acme Corp: acme.com
Target Inc: targetinc.com
