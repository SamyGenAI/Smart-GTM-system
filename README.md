# Smart Creator GTM System

An AI-powered lead generation system for B2B founders. Type one slash command, get a ready-to-send outreach list with personalized LinkedIn DMs — no spreadsheets, no manual research.

---

## What it does

This system is built around one core idea: **every output is personalized using your own data.**

When you set it up, the AI reads your **LinkedIn profile** and **business website** to learn who you are, what you sell, and how you talk about it. Every later step : searching, scoring, writing DMs...is filtered through that context, so the leads it finds and the messages it writes actually sound like you and target your real ideal client.

| Step | What happens | Business outcome |
|------|-------------|------------------|
| **Personalize** | The AI pulls your LinkedIn profile, scrapes your website, and asks you 4 short questions about your offer, ICP, and competitors | The system learns your voice, positioning, and ideal client — once, then reused everywhere |
| **Find** | The AI searches the web for people or companies matching your ICP | A fresh list of targeted prospects in minutes |
| **Score** | Every lead is rated 0–100 against *your* ICP and tagged Tier 1 / 2 / 3 | You only spend time on leads worth pursuing |
| **Capture warm leads** | Pull everyone who reacted to *any* LinkedIn post — yours, a competitor's, an industry leader's, an influencer's | Turn other people's audiences into your prospect list |
| **Enrich** | The AI researches each prospect online and writes two LinkedIn DMs personalized to *both* their context and your offer | Outreach that sounds human, at scale, without a copywriter |
| **Export** | One clean CSV with name, LinkedIn URL, score, and DMs | Plug straight into your CRM, Notion, or outreach tool |

> **Why post engagers matter:** anyone who liked or commented on a LinkedIn post about your topic has already raised their hand. Pulling engagers from a competitor's post or a thought leader's post in your niche is one of the highest-converting warm-lead sources available — and this system automates it.

---

## Before you start

You will install three things on your computer. None of them require any developer experience.

### 1. Install Node.js

Node is what runs the scripts under the hood. You will not interact with it directly.

- Download the **LTS** version from [nodejs.org](https://nodejs.org/)
- Run the installer and click **Next** through every screen
- That's it

### 2. Install your AI editor

Pick one. Both work identically with this repo.

| Editor | Download | Notes |
|--------|----------|-------|
| **Cursor** (recommended for non-developers) | [cursor.com](https://cursor.com/) | AI is built in. Easiest path. |
| **VS Code + Claude Code** | [VS Code](https://code.visualstudio.com/) + [Claude Code extension](https://claude.ai/code) | Free option. |

### 3. Get your API keys

Each link below leads to a signup page. All three services have free tiers — you can start without paying.

| Key | What it powers | Required? | Get it here |
|-----|---------------|-----------|-------------|
| `ANTHROPIC_API_KEY` | Lead scoring + writing DMs | Yes | [console.anthropic.com](https://console.anthropic.com/) |
| `EXA_API_KEY` | Searching for leads | Yes | [exa.ai](https://exa.ai/) |
| `RAPIDAPI_KEY` | Pulling LinkedIn post engagers + your LinkedIn profile | Optional, but unlocks warm leads | Subscribe to [linkedin-api8 on RapidAPI](https://rapidapi.com/rockapis-rockapis-default/api/linkedin-api8) |

Keep these three keys somewhere handy — you'll paste them into a file in the next step.

---

## Setup (one time, ~15 minutes)

### Step 1 — Download this repository

1. On the GitHub page, click the green **Code** button → **Download ZIP**
2. Unzip the file anywhere you like (Desktop, Documents, etc.)
3. You should now have a folder named something like `smart-creator-gtm-system`

### Step 2 — Open the folder in your AI editor

This is the most common stumbling point — make sure you open the **whole folder**, not a single file.

**In Cursor:**
1. Launch Cursor
2. Click `File → Open Folder…`
3. Select the unzipped folder (the one that contains `README.md`, `package.json`, `skills/`, etc.)
4. Confirm by clicking **Open**

**In VS Code (with Claude Code installed):**
1. Launch VS Code
2. Click `File → Open Folder…`
3. Select the unzipped folder (the one that contains `README.md`, `package.json`, `skills/`, etc.)
4. Confirm by clicking **Select Folder**
5. Open Claude Code from the sidebar or by pressing `Ctrl+Esc` (Windows) / `Cmd+Esc` (Mac)

> ⚠️ **Important:** open the folder *at its root* — the one that contains `README.md`. If you open a parent folder or a sub-folder, the slash commands and skills won't load.

### Step 3 — Add your API keys

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

### Step 4 — Install the project dependencies

1. Open a terminal inside your editor:
   - In Cursor / VS Code: `Terminal → New Terminal` (or `Ctrl+` ` on Windows / `Cmd+` ` on Mac)
2. The terminal opens at the bottom of the screen, already inside your project folder
3. Type this command and press Enter:

```bash
npm install
```

4. Wait for it to finish. You'll see a lot of text scroll by — that's normal. It usually takes under a minute. When it's done, you see your prompt again (`PS C:\...>` on Windows or `~/...$` on Mac).

### Step 5 — Run the setup command

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

Answer naturally — the AI will read your LinkedIn profile, scrape your website, and combine that with your answers to build five personalized context files in `context/`. These files drive every later command.

When setup finishes, you'll see a confirmation. You're now ready to generate leads.

---

## Daily workflow — slash commands

Once setup is done, every step is a single slash command in the AI chat. Just type `/` and pick from the menu, or type the full command.

### Path A — Cold outreach (find new leads)

```
/find-leads 25 B2B SaaS founders in France
```

The AI searches the web and saves a CSV in `outputs/`.

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

### Path B — Warm outreach (LinkedIn post engagers)

Anyone who liked or commented on a LinkedIn post is a warm lead. Pull them from any post — yours, a competitor's, an industry leader's.

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

---

## Output file — what you get

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
| `dm_sequence_1` | First LinkedIn DM — ready to send |
| `dm_sequence_2` | Follow-up DM — a fresh angle, not a bump |

---

## Troubleshooting

**"Slash commands don't appear in the chat"** — Two common causes:
1. You opened a parent folder or sub-folder instead of the project root. Close the folder and reopen the one that contains `README.md` and `package.json`.
2. You're running an older AI editor version that doesn't read `.claude/commands/` or `.cursor/commands/` yet. Update your editor to the latest version, or fall back to the long-form prompt: `Read skills/setup/SKILL.md and follow it`.

**"Cannot find module" error** — Run `npm install` in the terminal again from the project folder.

**"Invalid API key" error** — Open `.env` and double-check the key. No quotes, no spaces, and make sure the file is named exactly `.env` (not `.env.txt`).

**Leads come back empty** — Try a broader search query. Instead of "SaaS founders in Lyon", try "SaaS founders in France".

**DMs say `NO_SIGNAL`** — The AI couldn't find specific public information about that prospect. Either widen the search or skip that lead — leaving the DM blank is better than fabricating one.

**LinkedIn profile pull fails during setup** — The `RAPIDAPI_KEY` is optional. Setup will skip that step and use your answers + website only. You can always re-run `/setup` later once the key is added.

---

## License

MIT
