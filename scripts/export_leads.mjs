import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

// ---------------------------------------------------------------------------
// Arg parser
// ---------------------------------------------------------------------------
function parseArgs(argv) {
  const args = { input: "", out: "", minScore: 0, campaign: "leads" };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if ((token === "--input" || token === "-i") && argv[i + 1]) {
      args.input = argv[i + 1]; i += 1;
    } else if ((token === "--out" || token === "-o") && argv[i + 1]) {
      args.out = argv[i + 1]; i += 1;
    } else if ((token === "--min-score" || token === "-s") && argv[i + 1]) {
      args.minScore = Number.parseInt(argv[i + 1], 10); i += 1;
    } else if ((token === "--campaign" || token === "-c") && argv[i + 1]) {
      args.campaign = argv[i + 1]; i += 1;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// CSV helpers
// ---------------------------------------------------------------------------
function parseCsvLine(line) {
  const out = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') { cur += '"'; i += 1; }
      else inQuotes = !inQuotes;
    } else if (ch === "," && !inQuotes) {
      out.push(cur); cur = "";
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

function readCsv(filePath) {
  const raw = fs.readFileSync(filePath, "utf8").replace(/^\uFEFF/, "");
  const lines = raw.split(/\r?\n/).filter((l) => l.trim());
  if (lines.length < 2) return { headers: [], rows: [] };
  const headers = parseCsvLine(lines[0]);
  const rows = lines.slice(1).map((line) => {
    const vals = parseCsvLine(line);
    const obj = {};
    headers.forEach((h, i) => { obj[h] = (vals[i] ?? "").trim(); });
    return obj;
  });
  return { headers, rows };
}

function csvCell(val) {
  const s = String(val ?? "");
  if (s.includes(",") || s.includes('"') || s.includes("\n")) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function csvRow(fields) { return fields.map(csvCell).join(","); }

// ---------------------------------------------------------------------------
// Column normalizer — maps messy upstream column names to clean output names
// ---------------------------------------------------------------------------
function pick(row, ...keys) {
  for (const k of keys) {
    if (row[k] !== undefined && row[k] !== "") return row[k];
  }
  return "";
}

function scoreTier(score) {
  const n = Number.parseInt(score, 10);
  if (Number.isNaN(n)) return "";
  if (n >= 80) return "tier1";
  if (n >= 60) return "tier2";
  if (n >= 40) return "tier3";
  return "exclude";
}

function normalize(row) {
  return {
    lead_id:        pick(row, "lead_id") || crypto.randomUUID(),
    name:           pick(row, "name", "fullName", "title", "First Name"),
    headline:       pick(row, "headline", "title", "Position", "occupation"),
    linkedin_url:   pick(row, "linkedin_url", "url", "profileUrl", "URL"),
    score:          pick(row, "score"),
    tier:           scoreTier(pick(row, "score")),
    why_match:      pick(row, "why_match"),
    outreach_angle: pick(row, "outreach_angle"),
    dm_sequence_1:  pick(row, "dm_sequence_1"),
    dm_sequence_2:  pick(row, "dm_sequence_2"),
    source:         pick(row, "source"),
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const args = parseArgs(process.argv);

  if (!args.input) {
    console.error([
      "Usage: node scripts/export_leads.mjs -i <enriched-csv> [-o <out>] [-s <min-score>] [-c <campaign>]",
      "  -i / --input      Enriched CSV (output of enrich_leads_haiku.mjs)",
      "  -o / --out        Output path (default: outputs/[date]-[campaign]-leads.csv)",
      "  -s / --min-score  Only export rows at or above this score (default: 0 = all)",
      "  -c / --campaign   Campaign label for the filename (default: leads)",
    ].join("\n"));
    process.exit(1);
  }

  const { rows } = readCsv(args.input);

  const today = new Date().toISOString().slice(0, 10);
  const outPath = args.out || path.join("outputs", `${today}-${args.campaign}-leads.csv`);
  fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });

  const OUTPUT_COLS = [
    "lead_id", "name", "headline", "linkedin_url",
    "score", "tier", "why_match",
    "outreach_angle", "dm_sequence_1", "dm_sequence_2",
    "source",
  ];

  const filtered = rows
    .map(normalize)
    .filter((r) => {
      if (args.minScore <= 0) return true;
      const n = Number.parseInt(r.score, 10);
      return !Number.isNaN(n) && n >= args.minScore;
    });

  const lines = [OUTPUT_COLS.join(",")];
  for (const r of filtered) {
    lines.push(csvRow(OUTPUT_COLS.map((col) => r[col])));
  }

  fs.writeFileSync(outPath, lines.join("\n"), "utf8");

  console.log(`Export complete.`);
  console.log(`CSV  : ${outPath}`);
  console.log(`Rows : ${filtered.length}`);
}

main().catch((err) => { console.error("Fatal:", err.message); process.exit(1); });
