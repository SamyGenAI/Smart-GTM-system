---
name: social-listening
description: Monitor what watched competitors and creators are posting on LinkedIn, X, Reddit, YouTube, the open web, and newsletters in Gmail. Reads context/signals/watchlist.md, asks which sources to run, returns Top Signals grouped by source — the posts most relevant to the user's business, most recent first — with brief analysis per source; a per-source table extract is offered on request, and the full run beyond that. Triggers on /social-listening or "what are my competitors posting", "check social listening", "what did [competitor] publish this week", "what is X saying about [topic]", "what is Reddit saying about [topic]", "what is on YouTube about [topic]", "what did [channel] publish", "what is the web saying about [topic]", "search the web for [topic]", "what did my newsletters say this week", "digest my newsletters", "check Gmail newsletters".
---

# Social Listening

What the watchlist is **saying**. For what they are **doing** (hiring, funding,
launching), use `skills/intent-signals`.

Output in chat is **Top Signals, grouped by source** — up to 5 posts per source
ranked by relevance to the user's business and recency, not engagement — with
2-4 lines of analysis under each, then stop. Every source that ran gets its own
block, in the same format; sources are never merged into one list. A per-source
raw table is available on request, and even then it is an extract: the top 15
rows of each source, with the rest offered below it. No file is written.

## Sources

Five run through one script, `scripts/signals/social-listening.py`, with
`--source`. **Gmail is the exception — it has no script**, and is read with the
Gmail MCP tools directly:

| Source | Cost | Needs |
|---|---|---|
| `linkedin` | bills per post scraped | `APIFY_API_KEY` |
| `x` | one API call per run, `-n` is ~free | `X_API_KEY` |
| `reddit` | free — no key, no credits | nothing |
| `youtube` | free — no key, no credits | `yt-dlp` installed; `GEMINI_API_KEY` optional |
| `web` | free keyless, or one API call per query | nothing, or a search key |
| `gmail` | free — no key, no credits | Gmail connector authorized |

Who to watch: `context/signals/watchlist.md`, under `## LinkedIn` / `## X` /
`## Reddit` / `## YouTube` / `## Web` / `## Gmail`.
What counts as a signal: `context/signals/signals.md` if it exists — use it to
judge relevance and ordering. If missing, use judgement and say once that
filling it in sharpens future runs. Whether a signal fits the business is
`## ICP` in `brain/raw/me/offer.md`. Do not paste that heading into the watchlist.

Paid sources (LinkedIn, X, a keyed web backend, YouTube when Gemini is on)
need `--dry-run` or `--estimate` first, then `--confirm`. Reddit, keyless web,
and YouTube without Gemini are free. Nothing posts or replies.

## Step 1 — Ask first

**Never run every source by default.** Ask with AskUserQuestion
(`multiSelect: true`), offering only sources whose watchlist section has entries
and whose key is in `.env` (Reddit needs no key, so it qualifies on entries
alone, or on a topic question). Say how many entities each watches.

Skip the question when the user named the source ("check LinkedIn", "check
Reddit"). A topic question with no source named is query mode — ask whether to
run it on X, Reddit, YouTube, or the Web (or several), since all four answer it
and Reddit, YouTube and keyless Web are free.

Web qualifies for the question on entries alone or on a topic question, like
Reddit — it needs no key, since the keyless floor always works. When Web is
chosen for a topic question and you have a native web search tool, use that tool
rather than the script; see the Web notes in Step 2.

Gmail reads the user's own inbox, so unlike every other source it is **never**
offered for an open-web topic question and never runs unasked. Offer it when
`## Gmail` has entries — or when the user asks for newsletters and it is empty,
in which case offer to fill the section in.

When the user names a newsletter to watch, **write the name they said** into
`## Gmail` — never an email address. Addresses are resolved at run time and can
change; the name is what the user recognises a year later.

**If the connector is not authorized, offer to set it up.** The Gmail tools
(`search_threads`, `get_thread`) missing from this session means it is not
connected. Still offer Gmail in the question, labelled "needs connecting" — if
the user picks it, walk them through it: claude.ai → Settings → Connectors →
Gmail → Connect, then re-run. It is a browser flow you cannot perform for them,
so never ask for a token, code or app password, and never reach their mail any
other way.

**If they decline, skip the source and move on.** No second ask, no reminder
next run. Report the other sources normally and say nothing more about Gmail
than that it was skipped.

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
python scripts/signals/social-listening.py --source youtube -d 30 -n 15 --per-source 8 --enrich 3
python scripts/signals/social-listening.py --source youtube -q "linkedin ghostwriting" --enrich 3
python scripts/signals/social-listening.py --source web -q "linkedin ghostwriting pricing" -d 30
python scripts/signals/social-listening.py --source web -d 30 --per-source 5
```

All print `{"source","count","signals":[...]}` to stdout, **already sorted — by
engagement (highest first) on LinkedIn, X and Reddit, and by date (newest
first) on YouTube and Web**. Per-entity notes go to stderr. The JSON is for you;
never paste it into chat. Sources are independent — run them in parallel.

Gmail has no line here: it runs through the Gmail MCP tools, not this script.
See the Gmail notes below, and shape its results into the same `signals` fields
so Step 3 treats it like any other source.

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

**YouTube** — free and keyless, but needs `yt-dlp` on PATH
(`python -m pip install yt-dlp`); the script says so and exits if it is missing.
Slower than the others: a run does one discovery call per channel, then batched
metadata calls, then two more calls per enriched video, so budget a few minutes
and do not treat it as a hang.

Unlike every other source, **YouTube is ranked by date, newest first** — views
only break ties between videos published the same day. That is deliberate: an
old video with 500k views is not news, and this week's 400-view upload from a
competitor is. Do not re-sort it by views when reporting.

It has the same two modes as Reddit. `-q "..."` searches all of YouTube; with no
`-q` it pulls recent uploads from the channels under `## YouTube`. Both can run
at once — watchlist videos are kept regardless of the relevance floor, since a
channel the user chose to watch is on topic by definition. Pass keywords, not
the user's sentence, exactly as with Reddit.

`--per-source` (default 10) is how many recent videos to examine per channel —
free here, it is not a bill like LinkedIn's. Widen `-d` for YouTube: channels
publish weekly at best, so `-d 7` often returns nothing and `-d 30` is the more
useful default.

`--enrich` (default 5) sets how many of the top videos get their **transcript
and top comments** pulled. This is the reason to use the source at all — the
transcript is what was actually said, and the comments are where viewers state
the pain. Read both before ranking. Videos below the `--enrich` cutoff simply
have no transcript key — that is not a failure, just a budget line, so never
report those as silent.

Most YouTube videos carry no captions, so when `GEMINI_API_KEY` is set the
script falls back to **Gemini 2.5 Flash reading the video itself** — same field,
same use, and `transcript_source` says which route produced it (`captions` or
`gemini`). It fires only where yt-dlp came back empty, and at most 5 times per
run. Treat a Gemini transcript as slightly looser than captions: it is a dense
account of what was said, not a verbatim record, so paraphrase from it rather
than putting it in quotation marks. `--no-gemini` turns it off; without the key
nothing changes. A video still carrying `transcript_unavailable` had no captions
and Gemini could not read it either (private, age-gated, or quota) — say so
rather than treating it as having said nothing.

Engagement on YouTube is `views` — the best single indicator of reach there.
It is never a sum: views dwarf likes by orders of magnitude, so adding them
would change nothing but the number's meaning. `views`, `likes` and `comments`
are all still reported separately, and a `null` means the count was hidden, not
zero.

**Web — try your own search tool first.** This source is a ladder of three
rungs, and the script is only the bottom two:

1. **Your own web search tool**, if this harness gives you one. It is faster
   than a subprocess, costs no API credits, and returns better-synthesised
   results. Use it for any open-web topic question.
2. **A keyed backend** — Brave, EXA, Serper or Parallel, whichever key is in
   `.env`, picked automatically in that order.
3. **The keyless floor** — DuckDuckGo HTML, then Startpage. Free, no account.
   This is what runs when no key is set, and it always works.

So: **for a topic question, search with your own tool if you have one** and
report the results in the Part 1 format below, exactly as if the script had
produced them. Only run the script when you have no native search tool, when
the user explicitly asks to run the source, or when the run is watchlist-based.

**Watchlist runs always use the script**, whatever tools you have. Monitoring
the `## Web` domains means one `site:domain.com` query per line, which native
search handles poorly and the script does precisely. `-q` with a populated
`## Web` section narrows the topic to those domains rather than searching the
open web — the same combining rule X uses.

`--per-source` (default 10) caps results per query; `-n` caps the merged run.
`--web-backend` forces a specific rung (`keyless` to skip a paid key you have,
`brave`/`exa`/`serper`/`parallel` to pin one), and errors out if that key is
missing rather than silently falling back. `--dry-run` prints the backend and
the exact queries without spending a call — worth doing before a long
`## Web` section on a keyed backend, since each line is one call.

**Web is ranked by date, newest first**, like YouTube and for the same reason:
the open web reports no engagement, and a page that ranks well may be years
old. `engagement` is always `null` here — never write it as `0`, and never
merge Web rows into an engagement-sorted table as though they scored zero.

**The keyless floor returns no dates at all.** DuckDuckGo and Startpage do not
publish them, so keyless results carry `date: null`, sort last, and cannot be
windowed — `-d` silently does nothing on that rung. Say so when reporting a
keyless run: "these results have no publication date, so recency is unverified"
is honest; presenting them as this week's news is not. A keyed backend (EXA
included, which you have) does return real dates and does respect `-d`, so
prefer one when the question is about recency.

Pass keywords, not the user's sentence, exactly as with Reddit and YouTube —
the same relevance floor applies to `-q` results. Results from a watched
`## Web` domain are exempt from that floor, since a domain the user chose to
watch is on topic by definition.

**Gmail — no script, use the MCP tools.** This is the only source without a
`--source` flag. The Gmail connector already handles OAuth, so there is nothing
to install, no key in `.env`, and no token to refresh.

*Not connected, or the call errors on auth?* The connection is missing or
lapsed. Say so in one line, offer to walk them through claude.ai → Settings →
Connectors, and carry on — the other sources still report in full, and Gmail
gets a block saying it was not read.

**Read-only, always.** Use `search_threads`, `get_thread` and `get_message`, and
nothing else. The Gmail connector also exposes send, reply, draft, label, trash
and spam tools — **none of them belong in this skill.** Social listening reads;
it never writes, never marks anything read, never labels, never replies. If the
user wants mail sent, that is a different task, not this one.

*The watchlist holds names, not addresses.* `## Gmail` lines are what the user
would say out loud — `Aakash Gupta — Product Growth`. **Resolve each name to its
real sending addresses first**, with one broad search on the distinctive words
in the name:

```
from:(aakash OR "product growth") newer_than:90d
```

Read the senders off those results. Expect **more than one address per name**: a
writer with several publications sends from several, and Substack in particular
uses `name+publication@substack.com` per publication — Aakash Gupta resolves to
four. Take every address whose issues plainly belong to that writer or
publication, and say which you matched when you report, so a wrong guess is
visible. If a name resolves to nothing, say so and ask for a forwarded issue
rather than guessing an address.

Resolution is the only reason to search on a name rather than an address, and it
is still bounded — `from:` with the name's own words, never a body search across
the inbox. Do it once per run, not per source.

*Scope — two rings, both bounded.* Once resolved, every query is pinned to those
addresses plus the newsletter categories, so the primary inbox is out of scope:

```
from:(aakashgupta@substack.com OR aakashgupta+getting-a-pm-job@substack.com) newer_than:7d
{category:promotions category:updates} newer_than:7d -in:sent
```

Run the first for the watchlist, the second to catch newsletters the user never
listed. **Never widen past those two.** A bare inbox sweep, `in:anywhere`, a
`from:` a person rather than a list, or a search of the primary category reads
personal and client mail, and this skill does not do that — no matter how the
question is phrased. A topic question is answered by adding terms *inside* those
two rings, never by dropping them.

Anything the categories surface that is plainly not a newsletter — a receipt, a
calendar notice, a password reset, a personal thread that landed in updates — is
dropped without being summarised or quoted. Say how many were dropped, not what
they were.

*One call per name to resolve, then one for the whole watchlist.* After
resolution, a single `search_threads` covers every newsletter via the `OR` list
above — do not loop per sender or per address. Use
`view: THREAD_VIEW_MINIMAL` so the listing returns subject and snippet, rank
those by relevance, then call `get_thread` with
`messageFormat: "PLAIN_TEXT"` on only the top few. `PLAIN_TEXT` converts the
HTML newsletter to text, which is the whole reason not to write a script.

That second step is Gmail's `--enrich`: **5 issues by default.** Newsletter
bodies are long, and fetching twenty in full will exhaust the context window
before the report is written. Issues below the cutoff are reported from subject
and snippet alone — that is a budget line, not a failure, so never call them
empty.

`newer_than:7d` matches the other sources' `-d`. Widen it like YouTube: most
newsletters ship weekly, so `newer_than:30d` is often the more useful window.
Gmail's search is date-accurate, so unlike the keyless Web floor the window is
real and can be trusted.

*Shape the result like every other source*, so Step 3 treats it identically:
`entity` is the watchlist name (or the sender's list name when the categories
surfaced it), `author` the sender, `text` the plaintext body, `date` the
received date, and `url` the thread permalink
`https://mail.google.com/mail/u/0/#inbox/<threadId>`.

`engagement` is **always `null`** on Gmail. A newsletter reports no public
counts — write `—` in the table exactly as with Web, never `0`, and never invent
an open or click number.

**Gmail is ranked by date, newest first**, joining YouTube and Web for the same
reason: there is no engagement to rank by, and last month's issue is not a
signal. Do not re-sort it.

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
**raw table** is Part 2 — held back unless the user asks for it, and even then
it is an extract, not the whole run.

**Everything in this step is grouped by source.** A run that fetched Reddit and
YouTube produces a Reddit block and a YouTube block, in both parts, in the same
format. Never merge sources into one list or one table. Sources measure
different things — views are not upvotes are not reactions — and a merged
ranking silently compares them. Order the blocks by how much they returned,
most first, and use the source's own sort inside each block.

### Part 1 — Top Signals, by source

One block per source that ran. Head each with the source, its window and its
count:

```
**Reddit** — 7 days, 34 posts, 6 worth reading
```

Then up to **5 posts per source** (not 10 across the run), ranked by
**relevance to the user's business, then recency** — **not** by engagement.
Engagement is a tiebreaker between two equally relevant posts, never the sort
key. A 30,000-engagement post from outside the user's space does not belong
here; a 90-engagement post from a direct competitor describing their delivery
model does.

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

**Reddit and YouTube comments outrank the post text.** When an item carries
`top_comments`, read them before ranking it: replies are where buyers state a
price they paid, name the agency they fired, or admit the problem the post only
gestures at. Quote a comment in the analysis where it says something the post
does not, and attribute it to the commenter.

**On YouTube, read the `transcript` before ranking.** A title sells the click;
the transcript is what was actually said, and it is often where a competitor
names their price, their delivery model, or their client count. Rank and quote
from it, not from the title. Cite a timestamp-free quote and attribute it to the
channel.

**On Gmail, one line per issue — not per story.** A newsletter is one item, like
a post: `<Newsletter> — — <what the issue covered, then the one item that
matters to the user> — <link>`. The Eng slot is empty because there is no count.
Lead the summary with the issue's own subject matter, then name the single most
relevant item in it and why — a competitor mentioned, a price quoted, a tool the
user's buyers are moving to. Quote the newsletter's own words for that item
rather than paraphrasing, since the wording is the evidence.

Five newsletters covering the same launch stay five lines. Say it once in the
block's analysis — *"four of five led with X"* — rather than collapsing the
rows; repetition across issues is itself the signal, and collapsing hides it.

Issues fetched only as subject and snippet (below the enrich cutoff) are ranked
and reported from that, and marked as such in one word. Never summarise a body
that was not fetched. Within the window, newer
outranks older when relevance is comparable; call out anything from the last
48 hours. Say so plainly if the most relevant posts are all from the window's
far edge.

Fewer than 5 in a block is correct and expected when that source ran thin —
never pad to reach five. A source that qualified nothing gets one line saying
so, and still gets its block, so its silence is visible rather than absent.

**"Found nothing" and "could not read it" are different.** A source that was
unreachable — Gmail not connected, a rate-limited subreddit, a dead LinkedIn
profile — says so plainly and never reads as "quiet".

Format each post as one line: `<Author> — <eng> — <what the post is> — <link>`.

Then **2-4 lines of analysis under each block**, about that source only: what
those accounts are publishing and selling underneath it, what repeats, what is
new versus continuing, where the numbers say something the text does not. Ground
every claim in a specific post or number from that source — no generic
content-marketing advice. Note briefly when that source's highest-engagement
posts were excluded as off-topic, so the omission is visible.

When two or more sources ran, close with **up to 3 lines across sources** —
what shows up in more than one place, and where they disagree. This is the only
place sources are compared. Skip it on a single-source run.

Keep the whole of Part 1 tight. Do not spill into a strategy memo. Close with at
most one line on what is worth acting on, and only when the data supports it.

**Then stop.** End the turn with a single line offering the rest, naming what is
held back per source — e.g. *"Held back: 28 more Reddit posts, 11 YouTube — say
the word for the tables."* Do not use AskUserQuestion for this; it is an offer,
not a blocking question, and the user usually will not need it.

Flag any run that returned nothing, errored, was retried, or produced duplicate
posts in that source's block — those belong with the summary, not held back with
the table.

### Part 2 — Raw tables, by source (only on request)

**Do not print these by default.** They cost a lot of tokens and the Top Signals
usually answer the question on their own. Build them only when the user asks —
"full table", "show me everything", "more detail", or a follow-up about posts
outside the Top Signals.

**One table per source, never a merged one.** Each keeps its own sort: by
`engagement` descending on LinkedIn, X and Reddit; by date, newest first, on
YouTube, Web and Gmail, matching how those sources rank. Head each table with one line
stating the source, window and how many of its posts are shown out of how many
it returned.

**Each table is an extract, not the whole run.** Print the **top 15 rows per
source** by that source's sort, then one line below it naming the remainder —
e.g. *"19 more Reddit posts in the run — ask for the rest."* Only when the user
asks again ("everything", "all of them", "the full list") do you print the
remaining rows, and then print them all. A source with 15 or fewer posts is
already complete — print it whole and say nothing about a remainder.

The extract is the source's ranked top, not a curated pick: take rows straight
off the sort, including off-topic ones. Part 2 is the record, so a post cut from
Top Signals as off-topic still appears here in rank order — that is what makes
the cut visible.

The run's JSON stays available for the whole session, so a later request is
answered from it — never re-run the script to rebuild a table, since a LinkedIn
re-run bills again.

Columns, in this order, in every source's table:

| Author | Eng | Breakdown | Summary | Link |
|---|---|---|---|---|

There is no `Src` column — the table's heading already names the source.

- **Author** — the post's `author`, not the watchlist `entity`. On Reddit that
  is the redditor; put the subreddit (`entity`) in the summary. On YouTube it
  is the channel. On Gmail it is the newsletter's name, not the raw sending
  address — put the address in the summary when it is not obvious. When they differ
  (a repost surfaced through a watched profile), use the real author and note the
  watchlist line it came from in the summary.
- **Eng** — the `engagement` number, plain digits. A **null** means the count was
  unknown, not zero — write `?`, never `0`. On YouTube this is views; on Web and
  Gmail there is no number at all, so the column reads `—` in every row.
- **Breakdown** — `<likes>/<reposts>/<replies>` on X,
  `<reactions>/<comments>/<shares>` on LinkedIn, `<upvotes>/<comments>` on
  Reddit, `<views>/<likes>/<comments>` on YouTube, slash-separated, digits only.
  Web and Gmail have no counts at all — write `—`, not `?` or `0`. On Gmail use
  the column for the received date instead, `YYYY-MM-DD`, since date is what the
  table is sorted by and the reader needs it visible.
- **Summary** — 1-2 sentences on what the post says. Keep it to roughly 200
  characters so the row stays readable; the table is the deliverable, so trade
  detail for scannability here rather than letting one cell dominate.
- **Link** — a markdown link labelled `link`, pointing at the post URL. Every
  printed row gets one; an extract drops whole rows, never a row's URL.

The summary describes the post's content — what it claims, lists, or argues.
Favour the concrete specifics it contains: numbers, tool names, frameworks,
prices. Do not say why it matters, who it threatens, what it signals about the
market, or what the user should do — that belongs in Part 1, not here.

**Forbidden inside the tables:** themes, groupings by topic, cross-post patterns,
competitive read-outs, opportunities, and recommendations. Rows stay descriptive.
Sort strictly by the source's own key — never regroup rows by topic. If several
posts cover the same subject, they are simply separate rows.

**Never invent a post that was not in the JSON.** Nothing goes below the last
table but the remainder lines — the analysis already happened in Part 1, so do
not close with a second round of it.

## Next

```
Read skills/intent-signals/SKILL.md and check buying signals for my watchlist.
```
