import fs from "node:fs";
import path from "node:path";

function loadEnv() {
  const envPath = path.resolve(process.cwd(), ".env");
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const val = trimmed.slice(eq + 1).trim().replace(/^["']|["']$/g, "");
    if (!process.env[key]) process.env[key] = val;
  }
}
loadEnv();

function parseArgs(argv) {
  const args = {
    input: "",
    outCsv: "",
    model: "claude-haiku-4-5-20251001",
    minScore: 60,
    maxLeads: 0,
    sleepMs: 1500,
    webSearches: 1,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if ((token === "--input" || token === "-i") && argv[i + 1]) {
      args.input = argv[i + 1];
      i += 1;
    } else if ((token === "--out-csv" || token === "-o") && argv[i + 1]) {
      args.outCsv = argv[i + 1];
      i += 1;
    } else if ((token === "--model" || token === "-m") && argv[i + 1]) {
      args.model = argv[i + 1];
      i += 1;
    } else if ((token === "--min-score" || token === "-s") && argv[i + 1]) {
      args.minScore = Number.parseInt(argv[i + 1], 10);
      i += 1;
    } else if ((token === "--max-leads" || token === "-n") && argv[i + 1]) {
      args.maxLeads = Number.parseInt(argv[i + 1], 10);
      i += 1;
    } else if ((token === "--sleep-ms") && argv[i + 1]) {
      args.sleepMs = Number.parseInt(argv[i + 1], 10);
      i += 1;
    } else if ((token === "--web-searches") && argv[i + 1]) {
      args.webSearches = Number.parseInt(argv[i + 1], 10);
      i += 1;
    }
  }

  return args;
}

function parseCsvLine(line) {
  const out = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        cur += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === "," && !inQuotes) {
      out.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

function readCsv(filePath) {
  const raw = fs.readFileSync(filePath, "utf8").replace(/^\uFEFF/, "");
  const lines = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < raw.length; i += 1) {
    const ch = raw[i];
    if (ch === '"') {
      if (inQuotes && raw[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if ((ch === "\n" || ch === "\r") && !inQuotes) {
      if (ch === "\r" && raw[i + 1] === "\n") i += 1;
      if (current.trim().length > 0) lines.push(current);
      current = "";
      continue;
    }
    current += ch;
  }
  if (current.trim().length > 0) lines.push(current);
  if (lines.length < 2) return [];

  const headers = parseCsvLine(lines[0]);
  const rows = [];
  for (let i = 1; i < lines.length; i += 1) {
    const cols = parseCsvLine(lines[i]);
    const row = {};
    for (let j = 0; j < headers.length; j += 1) {
      row[headers[j]] = cols[j] ?? "";
    }
    rows.push(row);
  }
  return rows;
}

function csvEscape(value) {
  const text = String(value ?? "");
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Normalize a raw CSV row from any supported input format into the internal schema.
 *
 * Supported source formats:
 *  - Pipeline output (find-leads / score-leads): already has title, url, score, etc.
 *  - LinkedIn Connections export (inputs/connections/): First Name, Last Name, URL, Position, Company
 *  - Post-engagers export (inputs/post-engagers/): profile_name or name, profile_url or url, headline
 */
function normalizeRow(row) {
  const r = { ...row };

  if (!r.title) {
    if (r["First Name"] || r["Last Name"]) {
      const fname = String(r["First Name"] || "").trim();
      const lname = String(r["Last Name"] || "").trim();
      r.title = [fname, lname].filter(Boolean).join(" ");
    } else if (r["profile_name"]) {
      r.title = String(r["profile_name"]).trim();
    } else if (r["name"]) {
      r.title = String(r["name"]).trim();
    }
  }

  if (!r.url) {
    r.url = r["URL"] || r["Profile URL"] || r["profile_url"] || r["linkedin_url"] || "";
  }

  if (!r.snippet) {
    if (r["Position"] || r["Company"]) {
      const parts = [r["Position"], r["Company"]].filter(Boolean);
      r.snippet = parts.join(" at ");
    } else if (r["headline"]) {
      r.snippet = String(r["headline"]).trim();
    }
  }

  return r;
}

function extractFirstName(title) {
  if (!title) return "";
  const beforePipe = String(title).split("|")[0].trim();
  const firstWord = beforePipe.split(/\s+/)[0] || "";
  return firstWord.replace(/[^\p{L}\p{M}\-']/gu, "");
}

const MAX_BRIEF_CHARS = 1500;

function loadContext() {
  if (!fs.existsSync("context/brief/brief.md")) {
    throw new Error(
      "Missing context/brief/brief.md. Create a short brief (offer + ICP + angle bias, ~150 words) before running enrichment.",
    );
  }
  const raw = fs.readFileSync("context/brief/brief.md", "utf8");
  const trimmed = raw.length > MAX_BRIEF_CHARS ? raw.slice(0, MAX_BRIEF_CHARS) : raw;
  return { brief: trimmed };
}

function buildSystemPrompt({ brief }) {
  return `You write short, post-connection LinkedIn DMs from one founder to another. Assume the connection request was just accepted.

COMPANY BRIEF (so you know who is sending and who they sell to):
${brief}

Treat every DM as a post-connection note, not a cold pitch. Frame it as research so the prospect doesn't wonder "why is this stranger asking me?".

CORE PRINCIPLES (apply to every DM):

1. **Unexpected**
    
    You’ve noticed a very specific detail, the prospect gets curious → “How did he know ?”
    
2. **Useful**
    - Saves time
    - Compliment/makes them feel good
    - Reduce confusion
    - Removes friction
    - Helps NOW not “someday”
3. **Optional**

**The moment they feel pressured, forced → You lose trust.**

In practice : 

- Would it be useful if I shared X ?
- I can send the second part through if you’d be open to it ?
- Happy to send this if you want

HOW TO ASK THE QUESTION:
- One at a time. "What's been your biggest focus this week?" beats "How's business? What's challenging? What's your strategy?"
- Make it specific. A focused question proves you were paying attention. "What's been the hardest part of solving [specific problem] so far?" beats "What's the biggest challenge in your business?"
- Frame it as genuine curiosity, not prying. Offer them an easy fork: "Was it more about [option 1] or [option 2]?" This steers toward a real insight while staying easy to answer.


DM2 takes a different angle from DM1 and gives the prospect something worth their time: a sharp observation about their domain that you want their take on, a contrast or tension you've noticed in their space, or a related angle that opens a new thread. Open directly with the new content, not with a meta line.

DM2 must NEVER contain any of these words or phrases (even softened): "follow-up", "follow up", "following up", "Quick follow-up", "Just following up", "circling back", "bumping this", "to add to my last message", "one more thing". Don't reference the previous DM at all. Just start the new thread.

TRUTH AND ATTRIBUTION:
- Never attribute words or beliefs to them ("you wrote/said/posted that...", "your take/point that...", "you mentioned...") unless that exact claim has a real source URL in EVIDENCE. Otherwise rephrase as a neutral observation or drop it.
- Every fact in a DM (number, launch, methodology, quote, belief) must appear in EVIDENCE with its source. Not in EVIDENCE means not in the DM.
- Never invent anything. If nothing real and sourced is left, output NO_SIGNAL.

LENGTH AND STYLE (hard limits):
- Each DM is at most 2 short sentences. Shorter is better. If it reads like a paragraph, cut it.
- Exactly one question per DM.
- Never use the em dash character. Use a comma instead.
- No buzzwords, no flattery beyond a simple "thanks for connecting", no pitch. Ask, don't sell.

Output format (strict, exact delimiters, no markdown, no commentary):
<<<OUTREACH>>>
<one sentence outreach angle, or NO_SIGNAL>
<<<EVIDENCE>>>
<for each concrete fact you used: the fact, then "->", then the source URL or "snippet" if it came from the lead data provided. One per line. If NO_SIGNAL, leave this empty.>
<<<DM1>>>
<the first DM, ready to send>
<<<DM2>>>
<the follow-up DM, ready to send>
<<<END>>>`;
}

function clip(text, max) {
  const s = String(text || "").replace(/\s+/g, " ").trim();
  return s.length > max ? `${s.slice(0, max)}...` : s;
}

function buildUserPrompt(lead, firstName) {
  return `Research this lead via web search and write the DMs.

Lead:
- First name (use this name in the DMs): ${firstName || "(unknown, leave the greeting generic)"}
- Title / role: ${clip(lead.title, 300)}
- LinkedIn URL: ${lead.url || ""}
- Snippet: ${clip(lead.snippet, 300)}
- Highlights: ${clip(lead.highlights, 500)}
- Source query (how they were found): ${clip(lead.query, 120)}
- ICP score: ${lead.score || ""}
- ICP-fit reason: ${clip(lead.why_match, 240)}

Find ONE real, specific thing about this person. It can be a recent dated event (raise, hire, launch, talk in the last 60 days), a specific product or methodology they own, an exact phrase from their bio, a stated belief or contrarian take. Anchor the DM on that one thing and ask one focused question that shows you actually understood it.

Make it about them, keep each DM to at most 2 short sentences, and ask exactly one question. No em dashes, no pitch.

Only attribute a belief or quote to them if it is near-verbatim from a real source. Otherwise frame it as a neutral observation, not as their words. List every concrete fact and its source in the EVIDENCE block.

If nothing real and specific shows up, output NO_SIGNAL.

Output ONLY the five delimiters.`;
}

async function enrichLead(lead, systemPrompt, model, webSearches) {
  const firstName = extractFirstName(lead.title);
  const payload = {
    model,
    max_tokens: 2048,
    temperature: 0.3,
    system: systemPrompt,
    tools: [
      {
        type: "web_search_20250305",
        name: "web_search",
        max_uses: webSearches,
      },
    ],
    messages: [
      { role: "user", content: buildUserPrompt(lead, firstName) },
    ],
  };

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": process.env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Anthropic API error (${res.status}): ${text}`);
  }

  const data = await res.json();
  const content = Array.isArray(data?.content) ? data.content : [];

  const textBlocks = content
    .filter((c) => c?.type === "text")
    .map((c) => c?.text || "");

  // Collect the URLs the model actually fetched via web search. These blocks are
  // returned by the API alongside the text and would otherwise be discarded, leaving
  // no way to audit whether a DM's claims came from a real source.
  const searchUrls = [];
  for (const block of content) {
    if (block?.type !== "web_search_tool_result") continue;
    const results = Array.isArray(block.content) ? block.content : [];
    for (const r of results) {
      if (r?.url) searchUrls.push(r.url);
    }
  }

  return { text: textBlocks.join("\n"), searchUrls };
}

function parseEnrichment(text, searchUrls = []) {
  const safe = String(text || "");
  const mOut = safe.match(/<<<OUTREACH>>>([\s\S]*?)<<<EVIDENCE>>>/);
  const mEvid = safe.match(/<<<EVIDENCE>>>([\s\S]*?)<<<DM1>>>/);
  const mDm1 = safe.match(/<<<DM1>>>([\s\S]*?)<<<DM2>>>/);
  const mDm2 = safe.match(/<<<DM2>>>([\s\S]*?)<<<END>>>/);

  const outreach = (mOut?.[1] || "").trim();
  const evidence = (mEvid?.[1] || "").trim();
  const dm1 = (mDm1?.[1] || "").trim();
  const dm2 = (mDm2?.[1] || "").trim();

  if (!outreach || /^NO_SIGNAL$/i.test(outreach)) {
    return { outreach_angle: "", dm_sequence_1: "", dm_sequence_2: "", evidence: "" };
  }

  // Append the actual fetched URLs so the evidence column always shows what the model
  // searched, even if it forgot to cite a URL in its own EVIDENCE block.
  const uniqueUrls = [...new Set(searchUrls)];
  const sources = uniqueUrls.length ? `Searched: ${uniqueUrls.join(" | ")}` : "";
  const evidenceCombined = [evidence, sources].filter(Boolean).join("\n");

  return {
    outreach_angle: outreach,
    dm_sequence_1: dm1,
    dm_sequence_2: dm2,
    evidence: evidenceCombined,
  };
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.input) {
    throw new Error(
      "Missing --input. Examples:\n" +
      "  node scripts/enrich_leads_haiku.mjs -i outputs/leads-scored.csv -o outputs/leads-enriched.csv\n" +
      "  node scripts/enrich_leads_haiku.mjs -i inputs/connections/my-connections.csv -o outputs/connections-enriched.csv\n" +
      "  node scripts/enrich_leads_haiku.mjs -i inputs/post-engagers/engagers.csv -o outputs/engagers-enriched.csv",
    );
  }
  if (!args.outCsv) {
    throw new Error("Missing --out-csv. This script writes CSV output only.");
  }
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("Missing ANTHROPIC_API_KEY in environment.");
  }

  const rawLeads = readCsv(args.input);
  if (rawLeads.length === 0) {
    throw new Error("Input CSV has no leads.");
  }

  const allLeads = rawLeads.map(normalizeRow);

  const hasScoreCol = Object.prototype.hasOwnProperty.call(rawLeads[0], "score");
  if (!hasScoreCol) {
    throw new Error(
      "Input CSV is missing required 'score' column.\n" +
      "Score your leads first:\n" +
      "  node scripts/score_leads_haiku.mjs -i <your-csv> -o outputs/leads-scored.csv\n" +
      "Inputs from inputs/connections/ and inputs/post-engagers/ must be scored before enrichment.",
    );
  }

  const minScore = Number.isFinite(args.minScore) ? args.minScore : 60;
  const eligible = allLeads.filter((lead) => {
    const s = Number.parseInt(String(lead.score ?? "0"), 10);
    return Number.isFinite(s) && s >= minScore;
  });

  const cap = args.maxLeads > 0 ? Math.min(args.maxLeads, eligible.length) : eligible.length;
  const target = eligible.slice(0, cap);

  const systemPrompt = buildSystemPrompt(loadContext());

  const enrichmentByUrl = new Map();
  let processed = 0;
  let skipped = 0;
  for (const lead of target) {
    const url = String(lead.url ?? "").trim();
    try {
      const { text, searchUrls } = await enrichLead(lead, systemPrompt, args.model, args.webSearches);
      const parsed = parseEnrichment(text, searchUrls);
      enrichmentByUrl.set(url, parsed);
      if (!parsed.outreach_angle) skipped += 1;
      processed += 1;
      process.stderr.write(
        `[${processed}/${target.length}] ${parsed.outreach_angle ? "ok" : "no-signal"} :: ${lead.title?.slice(0, 80) || url}\n`,
      );
    } catch (err) {
      process.stderr.write(`[${processed + 1}/${target.length}] error :: ${err.message}\n`);
      enrichmentByUrl.set(url, { outreach_angle: "", dm_sequence_1: "", dm_sequence_2: "", evidence: "" });
      processed += 1;
    }
    if (args.sleepMs > 0) await sleep(args.sleepMs);
  }

  const inputHeaders = Object.keys(allLeads[0]);
  const newCols = ["outreach_angle", "dm_sequence_1", "dm_sequence_2", "evidence"];
  const outputHeaders = [...inputHeaders];
  for (const col of newCols) {
    if (!outputHeaders.includes(col)) outputHeaders.push(col);
  }

  const outputRows = allLeads.map((lead) => {
    const url = String(lead.url ?? "").trim();
    const enrich = enrichmentByUrl.get(url) ?? { outreach_angle: "", dm_sequence_1: "", dm_sequence_2: "", evidence: "" };
    const row = { ...lead, ...enrich };
    return outputHeaders.map((h) => csvEscape(row[h] ?? "")).join(",");
  });

  fs.mkdirSync(path.dirname(args.outCsv), { recursive: true });
  fs.writeFileSync(args.outCsv, `${outputHeaders.join(",")}\n${outputRows.join("\n")}\n`, "utf8");

  process.stdout.write(
    `${JSON.stringify(
      {
        input: args.input,
        model: args.model,
        totalLeads: allLeads.length,
        eligible: eligible.length,
        processed: target.length,
        skippedNoSignal: skipped,
        outCsv: args.outCsv,
      },
      null,
      2,
    )}\n`,
  );
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exit(1);
});
