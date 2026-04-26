import fs from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const args = {
    input: "",
    outCsv: "",
    model: "claude-sonnet-4-6",
    minScore: 60,
    maxLeads: 0,
    sleepMs: 1500,
    webSearches: 3,
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

const SYSTEM_PROMPT = `You are an SDR researcher writing ready-to-send LinkedIn DM copy for Igentiv, a premium LinkedIn content + lead gen studio for B2B founders.

For each lead you are given, you produce three artifacts:
1. outreach_angle — ONE sentence naming the specific concrete trigger signal you found via web search (recent LinkedIn post, fundraise, hiring, launch, podcast, etc).
2. dm_sequence_1 — first DM, filled with real context (no brackets).
3. dm_sequence_2 — follow-up DM, filled with real context.

DM sequence 1 template (opener, question-led):
"Hey {{first_name}}, [give a compliment, something you noticed, connect genuinely]. I'm researching how [ICP role] like you handle [problem I'm solving]. Does it take [pain point] and how do you ensure [specific result]?"

DM sequence 2 template (follow-up, value-add / curiosity):
"Reply with genuine interest, I'd love to learn more about it to help me refine my offer and positioning. Would you be open for a quick chat (not a sales call, just want to learn)?"

Strict rules (apply to every DM):
1. The FIRST sentence must be about THEM. Not your company, not your product, not your excitement about reaching out.
2. Reference the SPECIFIC trigger signal. If signal is a fundraise, name the round. If a LinkedIn post, reference its core message. If a job posting, name the role. Generic = fail.
3. No buzzwords. Banned list: synergy, leverage, touch base, circle back, ping, loop in, alignment, move the needle, low-hanging fruit, deep dive, bandwidth, at the end of the day, innovative, cutting-edge, best-in-class, world-class, game-changing, disruptive.
4. No pleasantries that waste the first line. No "I hope this email finds you well." No "I hope you are having a great week." No "Happy [day of week]."
5. Ask a question, do not pitch. Questions create engagement; pitches create delete buttons.
6. The follow-up must add NEW value, a new angle, or genuine interest in their reply. Never "just following up", "bumping this", "wanted to circle back."
7. READY TO SEND. No placeholder brackets like [Company Name] or [Pain Point]. Fill in everything from the research. The ONLY acceptable variable is the prospect's first name, written exactly as {{first_name}}.

If web search returns no concrete recent signal, output NO_SIGNAL as the outreach_angle and leave both DMs empty.

Output format (strict, exact delimiters, no other commentary, no markdown):
<<<OUTREACH>>>
<one sentence outreach angle, or NO_SIGNAL>
<<<DM1>>>
<dm_sequence_1 text>
<<<DM2>>>
<dm_sequence_2 text>
<<<END>>>`;

function buildUserPrompt(lead) {
  return `Research this lead via web search and produce the 3 artifacts in the strict output format.

Lead:
- Title / role: ${lead.title || ""}
- LinkedIn URL: ${lead.url || ""}
- Snippet: ${lead.snippet || ""}
- Highlights: ${lead.highlights || ""}
- Source query (how they were found): ${lead.query || ""}
- ICP score: ${lead.score || ""}
- ICP-fit reason: ${lead.why_match || ""}

Search for recent signals (last 90 days preferred): LinkedIn posts, fundraise, hiring, product launch, podcast/interview, conference talk. Pick ONE concrete signal as the trigger.

Output ONLY the strict format with the four delimiters.`;
}

async function enrichLead(lead, model, webSearches) {
  const payload = {
    model,
    max_tokens: 2048,
    temperature: 0.3,
    system: SYSTEM_PROMPT,
    tools: [
      {
        type: "web_search_20250305",
        name: "web_search",
        max_uses: webSearches,
      },
    ],
    messages: [
      { role: "user", content: buildUserPrompt(lead) },
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
  const textBlocks = Array.isArray(data?.content)
    ? data.content.filter((c) => c?.type === "text").map((c) => c?.text || "")
    : [];
  return textBlocks.join("\n");
}

function parseEnrichment(text) {
  const safe = String(text || "");
  const m1 = safe.match(/<<<OUTREACH>>>([\s\S]*?)<<<DM1>>>/);
  const m2 = safe.match(/<<<DM1>>>([\s\S]*?)<<<DM2>>>/);
  const m3 = safe.match(/<<<DM2>>>([\s\S]*?)<<<END>>>/);

  const outreach = (m1?.[1] || "").trim();
  const dm1 = (m2?.[1] || "").trim();
  const dm2 = (m3?.[1] || "").trim();

  if (!outreach || /^NO_SIGNAL$/i.test(outreach)) {
    return { outreach_angle: "", dm_sequence_1: "", dm_sequence_2: "" };
  }

  return {
    outreach_angle: outreach,
    dm_sequence_1: dm1,
    dm_sequence_2: dm2,
  };
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.input) {
    throw new Error("Missing --input. Example: node scripts/enrich_leads_sonnet.mjs -i outputs/leads-scored.csv -o outputs/leads-enriched.csv");
  }
  if (!args.outCsv) {
    throw new Error("Missing --out-csv. This script writes CSV output only.");
  }
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("Missing ANTHROPIC_API_KEY in environment.");
  }

  const allLeads = readCsv(args.input);
  if (allLeads.length === 0) {
    throw new Error("Input CSV has no leads.");
  }
  if (!Object.prototype.hasOwnProperty.call(allLeads[0], "score")) {
    throw new Error("Input CSV is missing required 'score' column. Run skills/score-leads first.");
  }

  const minScore = Number.isFinite(args.minScore) ? args.minScore : 60;
  const eligible = allLeads.filter((lead) => {
    const s = Number.parseInt(String(lead.score ?? "0"), 10);
    return Number.isFinite(s) && s >= minScore;
  });

  const cap = args.maxLeads > 0 ? Math.min(args.maxLeads, eligible.length) : eligible.length;
  const target = eligible.slice(0, cap);

  const enrichmentByUrl = new Map();
  let processed = 0;
  let skipped = 0;
  for (const lead of target) {
    const url = String(lead.url ?? "").trim();
    try {
      const raw = await enrichLead(lead, args.model, args.webSearches);
      const parsed = parseEnrichment(raw);
      enrichmentByUrl.set(url, parsed);
      if (!parsed.outreach_angle) skipped += 1;
      processed += 1;
      process.stderr.write(
        `[${processed}/${target.length}] ${parsed.outreach_angle ? "ok" : "no-signal"} :: ${lead.title?.slice(0, 80) || url}\n`,
      );
    } catch (err) {
      process.stderr.write(`[${processed + 1}/${target.length}] error :: ${err.message}\n`);
      enrichmentByUrl.set(url, { outreach_angle: "", dm_sequence_1: "", dm_sequence_2: "" });
      processed += 1;
    }
    if (args.sleepMs > 0) await sleep(args.sleepMs);
  }

  const inputHeaders = Object.keys(allLeads[0]);
  const newCols = ["outreach_angle", "dm_sequence_1", "dm_sequence_2"];
  const outputHeaders = [...inputHeaders];
  for (const col of newCols) {
    if (!outputHeaders.includes(col)) outputHeaders.push(col);
  }

  const outputRows = allLeads.map((lead) => {
    const url = String(lead.url ?? "").trim();
    const enrich = enrichmentByUrl.get(url) ?? { outreach_angle: "", dm_sequence_1: "", dm_sequence_2: "" };
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
