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
    batchSize: 20,
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
    } else if ((token === "--batch-size" || token === "-b") && argv[i + 1]) {
      args.batchSize = Number.parseInt(argv[i + 1], 10);
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

function parseScoreCsv(text) {
  const cleaned = text
    .trim()
    .replace(/^```csv\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/\s*```$/, "");
  const lines = cleaned.split(/\r?\n/).filter((line) => line.trim().length > 0);
  const dataLines = lines[0]?.toLowerCase().includes("url") ? lines.slice(1) : lines;
  const scoredByUrl = new Map();
  for (const line of dataLines) {
    const cols = parseCsvLine(line);
    if (cols.length < 3) continue;
    const url = String(cols[0] ?? "").trim();
    if (!url) continue;
    const parsed = Number.parseInt(String(cols[1] ?? "0"), 10);
    const score = Number.isFinite(parsed) ? Math.max(0, Math.min(100, parsed)) : 0;
    const whyMatch = String(cols.slice(2).join(",") ?? "").trim();
    scoredByUrl.set(url, { score, why_match: whyMatch });
  }
  return scoredByUrl;
}

/**
 * Normalize a raw CSV row from any supported input format into the internal schema.
 *
 * Supported source formats:
 *  - Pipeline output (find-leads): already has url, title, snippet, etc.
 *  - LinkedIn Connections export (inputs/connections/): First Name, Last Name, URL, Position, Company
 *  - Post-engagers export (inputs/post-engagers/): profile_name or name, profile_url or url, headline
 */
function normalizeRow(row) {
  const r = { ...row };

  if (!r.url) {
    r.url = r["URL"] || r["Profile URL"] || r["profile_url"] || r["linkedin_url"] || "";
  }

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

const ICP_SCORING_RUBRIC = `
Target profile:
- Founder/agency owner/Director/Co-founder/Head of Sales/Growth/GTM
- Europe, US, NZ, AU
- Team size ideally 1-30 (up to 50 acceptable)
- Signals of LinkedIn activity and growth intent
- Headline looks professional : no buzzwords, clear social proof and / or title.
- Not an AI related business.


Scoring guidance:
- 80-100: strong ICP fit with clear B2B founder + likely region + relevant offer
- 60-79: decent fit but missing evidence on one or more key signals
- 40-59: weak fit, ambiguous relevance
- 0-39: poor fit / likely anti-ICP
`;

async function scoreWithClaude(leads, model) {
  const payload = {
    model,
    max_tokens: 8192,
    temperature: 0.2,
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text:
              "Score each lead against the ICP and return ONLY CSV (no markdown, no commentary). " +
              "Return exactly these columns in this order: url,score,why_match. " +
              "Score must be integer 0-100. why_match must be a short sentence (max 140 chars) " +
              "explaining concretely why this lead matches (or does not match) the ICP. " +
              "Do NOT write outreach copy or DM angles here.\n\n" +
              `ICP Rubric:\n${ICP_SCORING_RUBRIC}\n\nLeads JSON:\n${JSON.stringify(leads)}`,
          },
        ],
      },
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
  return Array.isArray(data?.content)
    ? data.content.find((c) => c?.type === "text")?.text ?? ""
    : "";
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.input) {
    throw new Error("Missing --input. Example: node scripts/score_leads_haiku.mjs -i outputs/leads.csv");
  }
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error("Missing ANTHROPIC_API_KEY in environment.");
  }
  if (!args.outCsv) {
    throw new Error("Missing --out-csv. This script writes CSV output only.");
  }

  const leads = readCsv(args.input).map(normalizeRow);
  if (leads.length === 0) {
    throw new Error("Input CSV has no leads.");
  }

  const batchSize = Number.isFinite(args.batchSize) && args.batchSize > 0 ? args.batchSize : 20;
  const scoredByUrl = new Map();
  for (let i = 0; i < leads.length; i += batchSize) {
    const batch = leads.slice(i, i + batchSize);
    const batchCsv = await scoreWithClaude(batch, args.model);
    const parsed = parseScoreCsv(batchCsv);
    for (const lead of batch) {
      const url = String(lead.url ?? "").trim();
      if (!url) continue;
      const score = parsed.get(url) ?? { score: 0, why_match: "" };
      scoredByUrl.set(url, score);
    }
  }

  const inputHeaders = Object.keys(leads[0] ?? {});
  const outputHeaders = [...inputHeaders];
  if (!outputHeaders.includes("score")) outputHeaders.push("score");
  if (!outputHeaders.includes("why_match")) outputHeaders.push("why_match");

  const outputRows = leads.map((lead) => {
    const url = String(lead.url ?? "").trim();
    const enrichment = scoredByUrl.get(url) ?? { score: 0, why_match: "" };
    const row = { ...lead, score: enrichment.score, why_match: enrichment.why_match };
    return outputHeaders.map((h) => csvEscape(row[h] ?? "")).join(",");
  });

  fs.mkdirSync(path.dirname(args.outCsv), { recursive: true });
  fs.writeFileSync(args.outCsv, `${outputHeaders.join(",")}\n${outputRows.join("\n")}\n`, "utf8");

  process.stdout.write(
    `${JSON.stringify(
      {
        input: args.input,
        model: args.model,
        count: leads.length,
        outCsv: args.outCsv || null,
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
