import fs from "node:fs";
import path from "node:path";

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

function extractFirstName(title) {
  if (!title) return "";
  const beforePipe = String(title).split("|")[0].trim();
  const firstWord = beforePipe.split(/\s+/)[0] || "";
  return firstWord.replace(/[^\p{L}\p{M}\-']/gu, "");
}

const MAX_BRIEF_CHARS = 1500;

function loadContext() {
  if (!fs.existsSync("context/brief.md")) {
    throw new Error(
      "Missing context/brief.md. Create a short brief (offer + ICP + angle bias, ~150 words) before running enrichment.",
    );
  }
  const raw = fs.readFileSync("context/brief.md", "utf8");
  const trimmed = raw.length > MAX_BRIEF_CHARS ? raw.slice(0, MAX_BRIEF_CHARS) : raw;
  return { brief: trimmed };
}

function buildSystemPrompt({ brief }) {
  return `You write short, post-connection LinkedIn DMs from one founder to another. Assume the connection request was just accepted.

COMPANY BRIEF (so you know who is sending and who they sell to):
${brief}

How to write the DMs:

- Research the prospect: their posts, bio, website, articles. The research is for YOU. It does not appear in the DM. Never cite or attribute a post.
- Frame the DM as research, not a pitch. The frame: you are researching how a specific type of company handles a specific process or challenge, and you want to know if the prospect personally handles it. This frame answers the implicit "why is this stranger asking me?" and positions you as someone trying to learn, not sell.

Frame to adapt (do NOT copy verbatim, swap in real specifics from your research):
"Hey [first_name], thanks for connecting. I'm researching how [type of company they run] handle [specific process from their world]. Is that something you deal with, or someone else on your team?"

The "[type of company]" must be specific (e.g. "B2B SEO agencies", "ABM consultancies for B2B SaaS", "AI-content studios"), not generic ("companies", "founders").
The "[specific process]" must come from your research: a methodology they use, a metric they track, a transition their industry is in, a tradeoff they wrestle with. Not a fabricated detail.

Length: max 2 short sentences, around 30 words. If a sentence has more than one comma, it is too long.
Vary the topic and phrasing across leads. Don't mechanically reuse the exact same wording.

Hard constraints:
- Use the actual first name provided in the lead context. Never output "{{first_name}}", "[first_name]", or any placeholder.
- Never invent facts. If no real, specific process or angle shows up in research, output NO_SIGNAL and leave both DMs empty.
- Never cite a LinkedIn post or article in the DM text. Treat all post and article content as background research.
- No em dash. Use a period or comma.
- No buzzwords (synergy, leverage, touch base, circle back, alignment, move the needle, deep dive, bandwidth, innovative, cutting-edge, world-class, game-changing, disruptive, etc.).
- No pleasantries beyond a simple "thanks for connecting".
- Do not pitch. Ask a question.

DM2 takes a different angle from DM1 and gives the prospect something worth their time: a sharp observation about their domain that you want their take on, a contrast or tension you've noticed in their space, or a related angle that opens a new thread. Open directly with the new content, not with a meta line.

DM2 must NEVER contain any of these words or phrases (even softened): "follow-up", "follow up", "following up", "Quick follow-up", "Just following up", "circling back", "bumping this", "to add to my last message", "one more thing". Don't reference the previous DM at all. Just start the new thread.

Output format (strict, exact delimiters, no markdown, no commentary):
<<<OUTREACH>>>
<one sentence outreach angle, or NO_SIGNAL>
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

Find ONE real, specific thing about this person. It can be a recent dated event (raise, hire, launch, talk in the last 60 days), a specific product or methodology they own, an exact phrase from their bio, a stated belief or contrarian take. Anchor the DM on that one thing and ask a question that shows you actually understood it.

If nothing real and specific shows up, output NO_SIGNAL.

Output ONLY the four delimiters.`;
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

  const systemPrompt = buildSystemPrompt(loadContext());

  const enrichmentByUrl = new Map();
  let processed = 0;
  let skipped = 0;
  for (const lead of target) {
    const url = String(lead.url ?? "").trim();
    try {
      const raw = await enrichLead(lead, systemPrompt, args.model, args.webSearches);
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
