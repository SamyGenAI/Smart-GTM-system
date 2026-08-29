---
name: social-listening
description: Monitor what watched competitors and creators are posting on LinkedIn, X, and Reddit. Reads context/signals/watchlist.md, asks which sources to run, returns Top Signals — the posts most relevant to the user's business, most recent first — with brief analysis; a full table of every post is offered on request. Triggers on /social-listening or "what are my competitors posting", "check social listening", "what did [competitor] publish this week", "what is X saying about [topic]", "what is Reddit saying about [topic]".
---

# Social Listening

What the watchlist is **saying**. For what they are **doing** (hiring, funding,
launching), use `skills/intent-signals`.

Output in chat is **Top Signals** — up to 10 posts ranked by relevance to the
user's business and recency, not engagement — with 5-10 lines of analysis, then
stop. A raw table of every post is available on request but never printed by
default. No file is written.

## Sources

One script, `scripts/signals/social-listening.py`, with `--source`:

| Source | Cost | Needs |
|---|---|---|
| `linkedin` | bills per post scraped | `APIFY_API_KEY` |
| `x` | one API call per run, `-n` is ~free | `X_API_KEY` |
| `reddit` | free — no key, no credits | nothing |

Who to watch: `context/signals/watchlist.md`, under `## LinkedIn` / `## X` /
`## Reddit`.
What counts as a signal: `context/signals/signals.md` if it exists — use it to
judge relevance and ordering. If missing, use judgement and say once that
filling it in sharpens future runs.

## Step 1 — Ask first

**Never run every source by default.** Ask with AskUserQuestion
(`multiSelect: true`), offering only sources whose watchlist section has entries
and whose key is in `.env` (Reddit needs no key, so it qualifies on entries
alone, or on a topic question). Say how many entities each watches.

Skip the question when the user named the source ("check LinkedIn", "check
Reddit"). A topic question with no source named is query mode — ask whether to
run it on X, Reddit, or both, since both answer it and Reddit is free.

When Reddit is one of the chosen sources, also settle **what** it watches before
running: a topic/keyword/brand (`-q`) or the watchlist subreddits (no `-q`).
Infer it when the user's wording already decides — a subject means `-q`, a named
subreddit means subreddit mode — and only ask when genuinely ambiguous. Fold
that into the same AskUserQuestion rather than asking twice.

## Step 2 — Run

```bash
python scripts/signals/social-listening.py --source linkedin -d 7 -n 25 --per-source 10
python scripts/signals/social-listening.py --source x -d 7 -n 25
python scripts/signals/social-listening.py --source x -q "AI ghostwriting pricing"
python scripts/signals/social-listening.py --source reddit -d 7 -n 25 --enrich 5
python scripts/signals/social-listening.py --source reddit -q "linkedin ghostwriting pricing"
```

Both print `{"source","count","signals":[...]}` to stdout, **already sorted by
engagement, highest first**. Per-entity notes go to stderr. The JSON is for you;
never paste it into chat. Sources are independent — run them in parallel.

**LinkedIn** — `--per-source` (default 10) caps posts per watchlist line; one run
scrapes at most `lines x --per-source`, and that is the bill. `-d` filters after
fetching, so narrowing it saves nothing — lower `--per-source` instead.
`--dry-run` is free and prints `max_posts_scraped`; use it when the section is
long. Read the stderr lines: a profile returning nothing means unreachable or
inactive, never "quiet".

**X** — `-q` researches a topic across all of X (no watchlist needed); with a
watchlist it narrows that topic to those accounts. Takes ~2 minutes, one call
regardless of `-n`. Caps at 20 handles.

**Reddit** — free, so run it freely; the only cost is time. Requests are paced
~2s apart to stay under Reddit's rate limit, so a five-subreddit run takes a
couple of minutes — do not treat that as a hang. Upvote and comment counts are
real, from the arctic-shift archive, and are point-in-time so they can lag live
by a little. `--enrich` (default 5) sets how many top posts get their comment
threads pulled; the comments are usually where the buying pain is stated
plainly, so read them.

**Reddit has two modes — pick one deliberately, they answer different
questions.**

*Topic / keyword / brand mode* (`-q "..."`) searches all of Reddit and is the
stronger of the two. Use it whenever the user names a subject rather than a
place: a topic ("what do people say about LinkedIn ghostwriting"), a keyword, a
competitor's brand, or a category. It reaches far past the watchlist — one
three-word query pulled 97 posts from 22 subreddits, none of them watchlisted —
so it is the right default for finding buyers who are not where you expected.
Reddit's own search ranks the `-q` hits, and those are kept as ranked. The
local relevance cut applies only to the subreddit listing feeds, which carry no
query — that is what stops a viral off-topic thread from hijacking the brief.

**Pass keywords, not the user's sentence.** Search results are no longer
re-filtered locally, so query quality is what decides relevance: a vague
sentence returns whatever Reddit matched on its filler words. Shorten to the
1-2 words that would actually appear in a post worth reading:

| User asks | Pass | Not |
|---|---|---|
| "what are the latest trends in AI" | `-q "AI agents"` | `-q "what are the latest trends in AI"` |
| "monitor mentions of Taplio" | `-q "Taplio"` | `-q "monitor mentions of Taplio"` |
| "what do founders say about hiring ghostwriters" | `-q "ghostwriter"` | `-q "founders hiring ghostwriters"` |

A vague query returns noise rather than nothing: "what are the latest trends
in AI" pulled 21 posts, several matched only on "latest" or "trends". Skim and
drop those when reporting rather than presenting them as signal. `nothing
cleared the floor` now only appears in subreddit mode; in search mode an empty
result means Reddit found nothing, so broaden the keyword.

*Subreddit mode* (no `-q`) pulls the top/hot feeds of whatever is under
`## Reddit` in the watchlist. Use it when the user names places ("check
r/agency", "what's happening in my subreddits"). It ranks by raw engagement, so
in broad subs it surfaces whatever is most relatable rather than most relevant
— milestone posts, venting, memes. Filter hard against `signals.md` before
reporting, and expect to keep fewer posts than the run returned.

With both a `-q` and watchlist subreddits, it searches globally **and** in those
subs, mixing topical hits with subreddit noise. When the user wants a clean
topic read, say so and run `-q` against an empty `## Reddit` section, or ask
whether to include the subreddits.

**Choosing when the user is ambiguous:** a subject → `-q`; a place → subreddit
mode; a brand or competitor name → `-q`, and report every mention regardless of
score, since one prospect saying they cancelled a competitor matters at zero
upvotes. Multiple keywords need one run each — the script takes a single `-q` —
so state that cost before running several, and dedupe by URL across them when
reporting.

**Adding or changing what is monitored:** subreddits go under `## Reddit` in
`context/signals/watchlist.md`, one per line, `r/` optional, no `Name:` prefix.
Keywords have no watchlist section — they are passed per run with `-q`. If the
user asks to "monitor" a keyword standingly, tell them that plainly: offer to
save the term in `signals.md` as a topic that matters and run it on request,
rather than implying a keyword watchlist exists.

Reddit upvote counts come from an archive snapshot taken near posting time,
while comment scores are live. On a thread that took off after archiving the
post reads as under-scored, so a post carrying `score_note` has had its count
raised to its top comment's — treat that number as a floor, not a measurement,
and don't quote it as exact. `upvotes_stale` keeps the original.

Read Reddit's stderr as carefully as LinkedIn's: a subreddit listed under
`no posts from ...` was rate-limited or unreachable, **not** quiet. Say so in
Part 1 rather than reporting it as a silent week.

## Step 3 — Report

Default output is **Top Signals** with short analysis, and nothing else. The
**raw table** of everything is Part 2 — held back unless the user asks for it.

### Part 1 — Top Signals

Up to 10 posts, ranked by **relevance to the user's business, then recency** —
**not** by engagement. Engagement is a tiebreaker between two equally relevant
posts, never the sort key. A 30,000-engagement post from outside the user's
space does not belong here; a 90-engagement post from a direct competitor
describing their delivery model does.

Read `context/signals/signals.md` for what counts and how to rank. It is the
authority — its topic and ignore lists override any judgement of yours. If the
file is missing, fall back to the company context in `CLAUDE.md`, and say once
that filling in `signals.md` sharpens future runs.

Absent other guidance, a post earns a slot when it is about the user's category
or the work they sell, comes from a direct competitor, names pricing or
packaging, reveals how someone delivers the service, or marks a shift in the
tools and channels the user's buyers use. Broad or off-topic posts are excluded
no matter how well they performed: general-audience philosophy, politics,
history and human-interest storytelling, health, personal-life posts, and
commentary on products the user's buyers do not touch.

**Reddit comments outrank Reddit post text.** When a post carries
`top_comments`, read them before ranking it: a thread's replies are where
buyers state a price they paid, name the agency they fired, or admit the
problem the post only gestures at. Quote a comment in the analysis where it
says something the post does not, and attribute it to the commenter.

**Recency is a ranking input, not just a filter.** Within the window, newer
outranks older when relevance is comparable; call out anything from the last
48 hours. Say so plainly if the most relevant posts are all from the window's
far edge.

Fewer than 10 is correct and expected when the run is thin — never pad the list
with off-topic posts to reach ten. If nothing qualifies, say so in one line and
go straight to the table.

Format each as one line: `<Author> — <eng> — <what the post is> — <link>`.

Then **5-10 lines of analysis** of those signals. This is the only place
analysis is allowed. Cover what competitors are publishing and selling
underneath it, what is repeated across several of them, what is new this week
versus continuing, and where the numbers say something the text does not.
Ground every claim in a specific post or number from the run — no generic
content-marketing advice. Note briefly when the highest-engagement posts of the
run were excluded as off-topic, so the omission is visible.

Keep it to 5-10 lines. Do not pad, and do not spill into a strategy memo. Close
with at most one line on what is worth acting on, and only when the data
supports it.

**Then stop.** End the turn with a single line offering the rest, naming how
many posts are being held back — e.g. *"39 other posts in the run — say the word
for the full table."* Do not use AskUserQuestion for this; it is an offer, not a
blocking question, and the user usually will not need it.

Flag any run that returned nothing, errored, was retried, or produced duplicate
posts here in Part 1 — those belong with the summary, not held back with the
table.

### Part 2 — Raw table (only on request)

**Do not print this by default.** It costs a lot of tokens and the Top Signals
usually answer the question on their own. Build it only when the user asks for
it — "full table", "show me everything", "more detail", or a follow-up about
posts outside the Top Signals.

When asked, print **every post from the run**, including the Top Signals and
everything cut from them as off-topic — the table is the complete record, not
the leftovers. This is where broad and off-topic posts appear, so nothing is
lost.

The run's JSON stays available for the whole session, so a later request is
answered from it — never re-run the script to rebuild the table, since a
LinkedIn re-run bills again.

**One markdown table** across whatever ran — all sources merged into a single
table, sorted by `engagement` descending. Not a table per source.

Columns, in this order:

| Author | Src | Eng | Breakdown | Summary | Link |
|---|---|---|---|---|---|

- **Author** — the post's `author`, not the watchlist `entity`. On Reddit that
  is the redditor; put the subreddit (`entity`) in the summary. When they differ
  (a repost surfaced through a watched profile), use the real author and note the
  watchlist line it came from in the summary.
- **Src** — `LI`, `X`, or `RD`.
- **Eng** — the `engagement` number, plain digits. A **null** means the count was
  unknown, not zero — write `?`, never `0`.
- **Breakdown** — `<likes>/<reposts>/<replies>` on X,
  `<reactions>/<comments>/<shares>` on LinkedIn, `<upvotes>/<comments>` on
  Reddit, slash-separated, digits only.
- **Summary** — 1-2 sentences on what the post says. Keep it to roughly 200
  characters so the row stays readable; the table is the deliverable, so trade
  detail for scannability here rather than letting one cell dominate.
- **Link** — a markdown link labelled `link`, pointing at the post URL.

The summary describes the post's content — what it claims, lists, or argues.
Favour the concrete specifics it contains: numbers, tool names, frameworks,
prices. Do not say why it matters, who it threatens, what it signals about the
market, or what the user should do — that belongs in Part 1, not here.

**Forbidden inside the table:** themes, groupings by topic, cross-post patterns,
competitive read-outs, opportunities, and recommendations. Rows stay descriptive.
Sort strictly by engagement — never regroup rows by topic or source. If several
posts cover the same subject, they are simply separate rows.

Every row gets its URL. **Never invent a post that was not in the JSON.**
One line above the table may state the window, source(s) and post count. Nothing
below it — the analysis already happened in Part 1, so do not close with a
second round of it.

## Next

```
Read skills/intent-signals/SKILL.md and check buying signals for my watchlist.
```
