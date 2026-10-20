import Exa from "exa-js";
import fs from "node:fs";
import path from "node:path";
import { estimateFindLeads } from "./lib/costs.mjs";
import { gatePaid } from "./lib/guard.mjs";
import { loadOffer } from "./lib/brain.mjs";
import { writeRunSummary } from "./lib/summary.mjs";

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
    query: "",
    category: "auto",
    numResults: 25,
    out: "",
    run: "find-leads",
  };

  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if ((token === "--query" || token === "-q") && argv[i + 1]) {
      args.query = argv[i + 1];
      i += 1;
    } else if ((token === "--category" || token === "-c") && argv[i + 1]) {
      args.category = String(argv[i + 1]).toLowerCase();
      i += 1;
    } else if ((token === "--num" || token === "-n") && argv[i + 1]) {
      args.numResults = Number.parseInt(argv[i + 1], 10);
      i += 1;
    } else if ((token === "--out" || token === "-o") && argv[i + 1]) {
      args.out = argv[i + 1];
      i += 1;
    } else if (token === "--run" && argv[i + 1]) {
      args.run = argv[i + 1];
      i += 1;
    }
  }

  return args;
}

function detectCategory(query) {
  const q = query.toLowerCase();
  const peopleKeywords = [
    "founder",
    "ceo",
    "cmo",
    "cto",
    "head of",
    "vp ",
    "employee",
    "employees",
    "person",
    "people",
    "profile",
    "profiles",
  ];
  const companyKeywords = [
    "company",
    "companies",
    "startup",
    "startups",
    "agency",
    "agencies",
    "business",
    "businesses",
  ];

  const hasPeopleKeyword = peopleKeywords.some((keyword) => q.includes(keyword));
  if (hasPeopleKeyword) {
    return "people";
  }

  const hasCompanyKeyword = companyKeywords.some((keyword) => q.includes(keyword));
  if (hasCompanyKeyword) {
    return "company";
  }

  return "people";
}

function csvEscape(value) {
  const text = String(value ?? "");
  if (text.includes(",") || text.includes('"') || text.includes("\n")) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function toRows(result, category, query) {
  const items = Array.isArray(result?.results) ? result.results : [];
  return items.map((item, index) => {
    const highlights = Array.isArray(item?.highlights) ? item.highlights.join(" | ") : "";
    const text = item?.text ?? item?.summary ?? "";
    return {
      rank: index + 1,
      category,
      query,
      title: item?.title ?? "",
      url: item?.url ?? "",
      snippet: String(text).slice(0, 300),
      highlights: String(highlights).slice(0, 300),
    };
  });
}

function writeCsv(rows, outputPath) {
  const header = "rank,category,query,title,url,snippet,highlights";
  const lines = rows.map((row) =>
    [
      row.rank,
      row.category,
      row.query,
      row.title,
      row.url,
      row.snippet,
      row.highlights,
    ]
      .map(csvEscape)
      .join(","),
  );
  const content = `\uFEFF${header}\n${lines.join("\n")}\n`;
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, content, "utf8");
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.query) {
    throw new Error('Missing query. Example: node scripts/find_leads_exa.mjs -q "B2B AI founders in San Francisco"');
  }

  const category = args.category === "auto" ? detectCategory(args.query) : args.category;
  if (!["people", "company"].includes(category)) {
    throw new Error('Category must be "auto", "people", or "company".');
  }

  const cost = estimateFindLeads();
  let icp = "";
  try {
    icp = loadOffer().sections.get("ICP") || "";
  } catch (err) {
    icp = "";
    process.stderr.write(`${err.message}\n`);
  }
  const decision = gatePaid({
    argv: process.argv,
    estimate: cost,
    extra: { query: args.query, category, numResultsRequested: args.numResults, icp_loaded: Boolean(icp) },
  });
  const today = new Date().toISOString().slice(0, 10);
  const outPath = args.out || path.join("outputs", `${today}-find-leads.csv`);
  if (decision !== "confirmed") {
    const summary = writeRunSummary({
      run: args.run,
      query: args.query,
      counts: { requested: args.numResults, returned: 0 },
      topLeads: [],
      cost,
      csvPath: null,
      mode: decision,
      notes: icp ? `ICP was read from the brain and was not sent to Exa. The query above is what would be searched.` : "offer.md could not be read. The search query still has to come from Samy.",
    });
    process.stderr.write(`Summary: ${summary}\n`);
    process.exit(decision === "estimate" ? 0 : 2);
  }

  if (!process.env.EXA_API_KEY) {
    throw new Error("Missing EXA_API_KEY in environment.");
  }

  const exa = new Exa(process.env.EXA_API_KEY);
  const result = await exa.search(args.query, {
    category,
    numResults: Number.isFinite(args.numResults) ? args.numResults : 25,
    outputSchema: { type: "text" },
    type: "auto",
    contents: { highlights: true },
  });

  const rows = toRows(result, category, args.query);
  writeCsv(rows, outPath);
  const summary = writeRunSummary({
    run: args.run,
    query: args.query,
    counts: { requested: args.numResults, returned: rows.length },
    topLeads: rows.slice(0, 10).map((row) => ({ name: row.title, url: row.url })),
    cost,
    csvPath: outPath,
    mode: "confirmed",
  });

  const output = {
    query: args.query,
    category,
    numResultsRequested: args.numResults,
    count: rows.length,
    out: outPath,
    summary,
    estimated_usd: cost.estimated_usd,
    calls: cost.calls,
    rows,
  };

  process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exit(1);
});
