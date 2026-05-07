import Exa from "exa-js";
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
    query: "",
    category: "auto",
    numResults: 25,
    out: "",
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
  const content = `${header}\n${lines.join("\n")}\n`;
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, content, "utf8");
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args.query) {
    throw new Error('Missing query. Example: node scripts/find_leads_exa.mjs -q "B2B AI founders in San Francisco"');
  }

  if (!process.env.EXA_API_KEY) {
    throw new Error("Missing EXA_API_KEY in environment.");
  }

  const category = args.category === "auto" ? detectCategory(args.query) : args.category;
  if (!["people", "company"].includes(category)) {
    throw new Error('Category must be "auto", "people", or "company".');
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
  if (args.out) {
    writeCsv(rows, args.out);
  }

  const output = {
    query: args.query,
    category,
    numResultsRequested: args.numResults,
    count: rows.length,
    out: args.out || null,
    rows,
  };

  process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exit(1);
});
