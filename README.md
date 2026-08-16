# Smart Creator GTM System

An AI-powered lead generation system for B2B founders. Type one slash command, get a ready-to-send outreach list with personalized LinkedIn DMs. No spreadsheets, no manual research.

---

## What it does

This system is built around one core idea: **every output is personalized using your own data.**

When you set it up, the AI reads your **LinkedIn profile** and **business website** to learn who you are, what you sell, and how you talk about it. Every later step : searching, scoring, writing DMs...is filtered through that context, so the leads it finds and the messages it writes actually sound like you and target your real ideal client.

| Features | What happens | Business outcome |
|------|-------------|------------------|
| **Personalize** | The AI pulls your LinkedIn profile, scrapes your website, and asks you 4 short questions about your offer, ICP, and competitors | The system learns your voice, positioning, and ideal client once, then reuses that everywhere |
| **Find** | The AI searches the web for people or companies matching your ICP | A fresh list of targeted prospects in minutes |
| **Score** | Every lead is rated 0–100 against *your* ICP and tagged Tier 1 / 2 / 3 | You only spend time on leads worth pursuing |
| **Capture warm leads** | Pull everyone who reacted to *any* LinkedIn post (yours, a competitor's, an industry leader's, an influencer's) | Turn other people's audiences into your prospect list |
| **Enrich** | The AI researches each prospect online and writes two LinkedIn DMs personalized to *both* their context and your offer | Outreach that sounds human, at scale, without a copywriter |
| **Export** | One clean CSV with name, LinkedIn URL, score, and DMs | Plug straight into your CRM, Notion, or outreach tool |
| **Watch signals** | Track a watchlist of competitors and target companies, and report what they post and what they do (hiring, funding, launches, job changes) | Know when an account is heating up, and reach out on timing instead of guesswork |


---

## Before you start

You will install three things on your computer. None of them require any developer experience.

### 1. Install Node.js

Node is what runs the scripts under the hood. You will not interact with it directly.

- Download the **LTS** version from [nodejs.org](https://nodejs.org/)
- Run the installer and click **Next** through every screen
- That's it

### 1b. Install Python (only for the signal commands)

Python runs the `/social-listening` and `/intent-signals` scripts. Skip this if you only use the lead pipeline.

- Download from [python.org/downloads](https://www.python.org/downloads/)
- **On Windows, tick "Add python.exe to PATH" on the first installer screen** — this is easy to miss and the scripts will not run without it
- macOS already has Python; nothing to do

### 2. Install your AI editor

Pick one. Both work identically with this repo.

| Editor | Download | Notes |
|--------|----------|-------|
| **Cursor** (recommended for non-developers) | [cursor.com](https://cursor.com/) | AI is built in. Easiest path. |
| **VS Code + Claude Code** | [VS Code](https://code.visualstudio.com/) + [Claude Code extension](https://claude.ai/code) | Free option. |

### 3. Get your API keys

Each link below leads to a signup page. All three services have free tiers, so you can start without paying.

| Key | What it powers | Required? | Get it here |
|-----|---------------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Lead scoring + writing DMs | Yes | [console.anthropic.com](https://console.anthropic.com/) |
| `EXA_API_KEY` | Searching for leads | Yes | [exa.ai](https://exa.ai/) |
| `RAPIDAPI_KEY` | Pulling LinkedIn post engagers + your LinkedIn profile | Optional, but unlocks warm leads | Subscribe to [linkedin-api8 on RapidAPI](https://rapidapi.com/rockapis-rockapis-default/api/linkedin-api8) |

Keep these three keys somewhere handy. You'll paste them into a file in the next step.

---

## Setup (one time, ~15 minutes)

### Step 1: Download this repository

1. On the GitHub page, click the green **Code** button → **Download ZIP**
2. Unzip the file anywhere you like (Desktop, Documents, etc.)
3. You should now have a folder named something like `smart-creator-gtm-system`

### Step 2: Open the folder in your AI editor

This is the most common stumbling point: make sure you open the **whole folder**, not a single file.

**In Claude code :**
1. Launch Claude code (using desktop app, VS Code or Cursor)
2. Click `File → Open Folder…`
3. Select the unzipped folder (the one that contains `README.md`, `package.json`, `skills/`, etc.)
4. Confirm by clicking **Select Folder**

**In Cursor:**
1. Launch Cursor
2. Click `File → Open Folder…`
3. Select the unzipped folder (the one that contains `README.md`, `package.json`, `skills/`, etc.)
4. Confirm by clicking **Open**

**In Codex:**
1. Launch Codex
2. Click `File → Open Folder…`
3. Select the unzipped folder (the one that contains `README.md`, `package.json`, `skills/`, etc.)
4. Confirm by clicking **Select Folder**

> ⚠️ **Important:** open the folder *at its root* (the one that contains `README.md`). If you open a parent folder or a sub-folder, the slash commands and skills won't load.

### Step 3: Add your API keys

1. In the file explorer (left sidebar), find a file named **`.env.example`**
2. Right-click it → **Copy**, then right-click in empty space → **Paste**. You now have `.env.example - Copy`
3. Right-click the copy → **Rename** → name it exactly **`.env`** (with the dot, no `.txt` at the end)
4. Click on `.env` to open it. You'll see this:

```
ANTHROPIC_API_KEY=
EXA_API_KEY=
RAPIDAPI_KEY=
```

5. Paste each of your keys after the `=` sign. No spaces, no quotes:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
EXA_API_KEY=xxxxx-xxxxx-xxxxx
RAPIDAPI_KEY=xxxxx
```

6. Save the file (`Ctrl+S` / `Cmd+S`)

> Your `.env` file stays on your machine only. It is listed in `.gitignore` and is never shared, committed, or sent to any server other than the API providers.

### Step 4: Install the project dependencies

1. Open a terminal inside your editor:
   - In Cursor / VS Code: `Terminal → New Terminal` (or `Ctrl+` ` on Windows / `Cmd+` ` on Mac)
2. The terminal opens at the bottom of the screen, already inside your project folder
3. Type this command and press Enter:

```bash
npm install
```

4. Wait for it to finish. You'll see a lot of text scroll by, which is normal. It usually takes under a minute. When it's done, you see your prompt again (`PS C:\...>` on Windows or `~/...$` on Mac).

### Step 5: Run the setup command

In the AI chat panel of your editor, type the slash command:

```
/setup
```

Then send. The AI will:

1. Ask for your **LinkedIn profile URL**
2. Ask for your **business website URL**
3. Ask **what you sell**
4. Ask **who your ideal client is**
5. Ask **who your competitors are** (optional)

Answer naturally. The AI will read your LinkedIn profile, scrape your website, and combine that with your answers to build five personalized context files in `context/`. These files drive every later command.

When setup finishes, you'll see a confirmation. You're now ready to generate leads.

---

## Daily workflow: slash commands

Once setup is done, every step is a single slash command in the AI chat. Just type `/` and pick from the menu, or type the full command.

### Path A: Cold outreach (find new leads)

```
/find-leads 25 B2B SaaS founders in France
```

The AI searches the web and saves a CSV with a targeted lead list in `outputs/`.

```
/score-leads
```

Every lead gets a 0–100 score and a one-sentence reason. Tier 1 / 2 / 3 is auto-tagged.

```
/enrich-leads
```

For each lead scored 60+, the AI does deep research and writes two ready-to-send LinkedIn DMs.

```
/export-leads
```

You get one clean CSV: `outputs/[date]-leads.csv`. Drop it into your CRM or outreach tool.

### Path B: Warm outreach (LinkedIn post engagers)

Anyone who liked or commented on a LinkedIn post is a warm lead. Pull them from any post (yours, a competitor's, an industry leader's).

```
/post-engagers
```

The AI will ask you to paste the LinkedIn post URLs (or how many of your own recent posts to scan). Requires `RAPIDAPI_KEY`.

Then run the same `/score-leads` → `/enrich-leads` → `/export-leads` chain.

---

## All slash commands

| Command | What it does |
|---------|-------------|
| `/setup` | One-time onboarding: pulls your LinkedIn + website, builds your ICP and positioning files |
| `/find-leads` | Searches the web for prospects matching your ICP |
| `/score-leads` | Scores a CSV of leads 0–100 against your ICP |
| `/post-engagers` | Pulls people who reacted to LinkedIn posts (yours or anyone's) |
| `/enrich-leads` | Researches tier 1 / 2 leads and writes two personalized DMs each |
| `/export-leads` | Produces the final clean CSV ready for your CRM |
| `/social-listening` | Reports what the competitors and people on your watchlist are posting |
| `/intent-signals` | Reports buying signals from your watchlist: hiring, funding, launches, job changes |

---

## Watching signals

The two signal commands answer a different question from the lead pipeline: not *who should I contact*, but *what changed this week among the people I already care about*.

**One-time setup.** Copy `context/signals/watchlist-template.md` to `context/signals/watchlist.md` and list who you want to track. One line each, grouped by platform:

```
## LinkedIn

Jane Doe: https://linkedin.com/in/janedoe
Acme Corp: https://linkedin.com/company/acme

## Reddit

r/sales
```

Delete the sections you don't use. That's the whole format.

**Optional.** Copy `context/signals/signals-template.md` to `context/signals/signals.md` to tell the AI which topics matter, what to ignore, and how to rank what comes back. Skip it and the AI uses its own judgement.

**Then run either command.** The AI asks which sources to check before it runs anything (it never runs them all by default — that wastes time and API quota), then reports what it found directly in the chat. No CSV, no file to open.

| Command | Answers |
|---------|---------|
| `/social-listening` | What are they **saying and publishing**? |
| `/intent-signals` | What are they **doing** that suggests they're ready to buy? |

Sources are added one at a time. A source that isn't built yet is listed as ⬜ in the skill file, and the AI will tell you plainly rather than inventing a result. Only the `demo` source ships working today — it returns clearly-labelled `[DEMO]` placeholder data so you can see the flow before connecting a real platform.

---

## Output file: what you get

Every export produces a CSV with these columns:

| Column | What it contains |
|--------|------------------|
| `name` | Full name |
| `linkedin_url` | Direct profile link |
| `headline` | Their current role |
| `score` | 0–100 ICP fit score |
| `tier` | tier1 / tier2 / tier3 |
| `why_match` | One sentence on why they fit (or don't) |
| `outreach_angle` | The specific hook the DMs are built around |
| `dm_sequence_1` | First LinkedIn DM, ready to send |
| `dm_sequence_2` | Follow-up DM with a fresh angle, not a bump |

---

## Troubleshooting

**"Slash commands don't appear in the chat"**: two common causes.
1. You opened a parent folder or sub-folder instead of the project root. Close the folder and reopen the one that contains `README.md` and `package.json`.
2. You're running an older AI editor version that doesn't read `.claude/commands/` or `.cursor/commands/` yet. Update your editor to the latest version, or fall back to the long-form prompt: `Read skills/setup/SKILL.md and follow it`.

**"Cannot find module" error**: run `npm install` in the terminal again from the project folder.

**"Invalid API key" error**: open `.env` and double-check the key. No quotes, no spaces, and make sure the file is named exactly `.env` (not `.env.txt`).

**Leads come back empty**: try a broader search query. Instead of "SaaS founders in Lyon", try "SaaS founders in France".

**DMs say `NO_SIGNAL`**: the AI couldn't find specific public information about that prospect. Either widen the search or skip that lead. Leaving the DM blank is better than fabricating one.

**LinkedIn profile pull fails during setup**: the `RAPIDAPI_KEY` is optional. Setup will skip that step and use your answers + website only. You can always re-run `/setup` later once the key is added.

**"python is not recognized" on the signal commands**: Python isn't installed, or it was installed without being added to PATH. Reinstall from [python.org](https://www.python.org/downloads/) and tick **"Add python.exe to PATH"** on the first screen.

**Signal commands say "nothing watched"**: you haven't created `context/signals/watchlist.md` yet, or the section for that platform is empty. Copy `context/signals/watchlist-template.md` and add one line per entity under the right heading.

---

## License

MIT
