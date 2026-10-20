import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { estimateRapidApi } from "./lib/costs.mjs";
import { gatePaid } from "./lib/guard.mjs";
import { writeRunSummary } from "./lib/summary.mjs";

// ---------------------------------------------------------------------------
// Env loader
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Arg parser
// ---------------------------------------------------------------------------
function parseArgs(argv) {
  const args = {
    urls: [],
    urlsFile: "",
    maxPages: 5,
    reactionType: "",
    out: "",
  };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if ((token === "--urls" || token === "-u") && argv[i + 1]) {
      args.urls = argv[i + 1].split(",").map((s) => s.trim()).filter(Boolean);
      i += 1;
    } else if ((token === "--urls-file" || token === "-f") && argv[i + 1]) {
      args.urlsFile = argv[i + 1];
      i += 1;
    } else if ((token === "--max-pages" || token === "-p") && argv[i + 1]) {
      args.maxPages = Number.parseInt(argv[i + 1], 10) || 5;
      i += 1;
    } else if ((token === "--reaction-type" || token === "-r") && argv[i + 1]) {
      args.reactionType = argv[i + 1];
      i += 1;
    } else if ((token === "--out" || token === "-o") && argv[i + 1]) {
      args.out = argv[i + 1];
      i += 1;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// CSV helpers
// ---------------------------------------------------------------------------
function csvCell(val) {
  const s = String(val ?? "");
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function csvRow(fields) {
  return fields.map(csvCell).join(",");
}

const CSV_HEADERS = [
  "lead_id",
  "name",
  "headline",
  "linkedin_url",
  "engagement_count",
  "repeat_engager",
  "latest_engagement_date",
  "reaction_types",
  "engaged_posts",
  "source",
];

// ---------------------------------------------------------------------------
// API call — one page of reactions for a post URL
// ---------------------------------------------------------------------------
async function fetchReactionsPage(postUrl, page, reactionType, key) {
  const response = await fetch("https://linkedin-api8.p.rapidapi.com/get-post-reactions", {
    method: "POST",
    headers: {
      "x-rapidapi-key": key,
      "x-rapidapi-host": "linkedin-api8.p.rapidapi.com",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: postUrl, page, reactionType }),
  });

  const text = await response.text();

  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for page ${page}: ${text.slice(0, 200)}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error(`Invalid JSON on page ${page}: ${text.slice(0, 200)}`);
  }

  return parsed;
}

// ---------------------------------------------------------------------------
// Extract reactor list from API response
// Shape: { success, data: { currentPage, totalPages, total, items: [...] } }
// ---------------------------------------------------------------------------
function extractReactors(payload) {
  // Primary shape from linkedin-api8
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  // Fallback shapes
  const candidates = [payload?.items, payload?.data, payload?.reactions, payload?.elements, payload?.result];
  for (const c of candidates) {
    if (Array.isArray(c) && c.length > 0) return c;
  }
  if (Array.isArray(payload)) return payload;
  return [];
}

// ---------------------------------------------------------------------------
// Normalize a single reactor entry into a flat object
// Fields from linkedin-api8: fullName, headline, url, reactionType, profileType
// ---------------------------------------------------------------------------
function normalizeReactor(entry) {
  const name =
    entry?.fullName ??
    entry?.name ??
    [entry?.firstName, entry?.lastName].filter(Boolean).join(" ") ??
    entry?.actor?.name ??
    "";

  const headline =
    entry?.headline ??
    entry?.title ??
    entry?.occupation ??
    entry?.actor?.headline ??
    "";

  const linkedin_url =
    entry?.url ??
    entry?.profileUrl ??
    entry?.navigationUrl ??
    entry?.actor?.url ??
    (entry?.publicIdentifier ? `https://www.linkedin.com/in/${entry.publicIdentifier}` : "") ??
    "";

  const reactionType = entry?.reactionType ?? entry?.type ?? entry?.reaction ?? "";
  const profileType = entry?.profileType ?? "user";

  return { name, headline, linkedin_url, reactionType, profileType };
}

// ---------------------------------------------------------------------------
// Check if there are more pages
// Shape: payload.data.totalPages / payload.data.currentPage
// ---------------------------------------------------------------------------
function hasMorePages(payload, currentPage) {
  const totalPages = payload?.data?.totalPages ?? payload?.totalPages ?? null;
  if (totalPages !== null) return currentPage < totalPages;
  // Fallback: keep going if we got a full page of items
  const items = extractReactors(payload);
  return items.length >= 10;
}

// ---------------------------------------------------------------------------
// Fetch all reactions for a single post (all pages)
// ---------------------------------------------------------------------------
async function fetchAllReactionsForPost(postUrl, maxPages, reactionType, key) {
  const allReactors = [];
  let page = 1;

  console.error(`  Fetching reactions for: ${postUrl}`);

  while (page <= maxPages) {
    let payload;
    try {
      payload = await fetchReactionsPage(postUrl, page, reactionType, key);
    } catch (err) {
      console.error(`  [warn] page ${page} failed: ${err.message}`);
      break;
    }

    const reactors = extractReactors(payload);
    if (reactors.length === 0) break;

    console.error(`    page ${page}: ${reactors.length} reactors`);
    allReactors.push(...reactors);

    if (!hasMorePages(payload, page)) break;
    page += 1;

    // Polite delay between pages
    await new Promise((r) => setTimeout(r, 600));
  }

  return allReactors;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  loadEnv();

  const args = parseArgs(process.argv);

  // Collect post URLs
  let postUrls = [...args.urls];
  if (args.urlsFile) {
    if (!fs.existsSync(args.urlsFile)) {
      console.error(`URLs file not found: ${args.urlsFile}`);
      process.exit(2);
    }
    const lines = fs.readFileSync(args.urlsFile, "utf8").split("\n");
    postUrls.push(...lines.map((l) => l.trim()).filter((l) => l && !l.startsWith("#")));
  }

  if (postUrls.length === 0) {
    console.error(
      [
        "Usage:",
        "  node scripts/rapidapi_post_reactions.mjs --urls <url1,url2,...>",
        "  node scripts/rapidapi_post_reactions.mjs --urls-file inputs/post-engagers/post-urls.txt",
        "Options:",
        "  --max-pages / -p     Max pages per post (default: 5, ~50-100 reactors/post)",
        "  --reaction-type / -r Filter: LIKE | CELEBRATE | SUPPORT | LOVE | INSIGHTFUL | FUNNY",
        "  --out / -o           Output CSV path (default: inputs/post-engagers/[date]-post-engagers-raw.csv)",
      ].join("\n")
    );
    process.exit(2);
  }

  const today = new Date().toISOString().slice(0, 10);
  const outPath = args.out || path.join("inputs", "post-engagers", `${today}-post-engagers-raw.csv`);
  const cost = estimateRapidApi({ requests: postUrls.length * args.maxPages });
  const decision = gatePaid({
    argv: process.argv,
    estimate: cost,
    extra: { posts: postUrls.length, maxPages: args.maxPages, note: cost.note },
  });
  if (decision !== "confirmed") {
    const summary = writeRunSummary({
      run: "post-engagers",
      query: postUrls.join(" "),
      counts: { posts: postUrls.length, maxPages: args.maxPages, rapidapi_calls_upper_bound: cost.calls.rapidapi },
      topLeads: [],
      cost,
      csvPath: outPath,
      mode: decision,
      notes: "Upper bound assumes every post uses every page. The live run stops when a post runs out of reactions.",
    });
    process.stderr.write(`Summary: ${summary}\n`);
    process.exit(decision === "estimate" ? 0 : 2);
  }

  const key = process.env.RAPIDAPI_KEY;
  if (!key) {
    console.error(JSON.stringify({ error: "missing_credential", var: "RAPIDAPI_KEY" }));
    process.exit(3);
  }

  fs.mkdirSync(path.dirname(path.resolve(outPath)), { recursive: true });

  // Aggregate reactors across all posts: keyed by linkedin_url (or name fallback)
  // Map<key, { name, headline, linkedin_url, engagement_count, reaction_types: Set, engaged_posts: Set, latest_engagement_date }>
  const byPerson = new Map();
  const today_date = new Date().toISOString().slice(0, 10);

  for (const postUrl of postUrls) {
    const reactors = await fetchAllReactionsForPost(postUrl, args.maxPages, args.reactionType, key);

    for (const entry of reactors) {
      const { name, headline, linkedin_url, reactionType, profileType } = normalizeReactor(entry);

      // Skip company pages — keep only person profiles
      if (profileType === "company") continue;

      const personKey = linkedin_url || name;
      if (!personKey) continue;

      if (!byPerson.has(personKey)) {
        byPerson.set(personKey, {
          name,
          headline,
          linkedin_url,
          engagement_count: 0,
          reaction_types: new Set(),
          engaged_posts: new Set(),
          latest_engagement_date: today_date,
        });
      }

      const p = byPerson.get(personKey);
      p.engagement_count += 1;
      if (reactionType) p.reaction_types.add(reactionType);
      p.engaged_posts.add(postUrl);
      // Update headline/name if richer data came in later
      if (!p.headline && headline) p.headline = headline;
      if (!p.name && name) p.name = name;
    }

    // Polite delay between posts
    if (postUrls.indexOf(postUrl) < postUrls.length - 1) {
      await new Promise((r) => setTimeout(r, 800));
    }
  }

  // Build CSV rows
  const rows = [CSV_HEADERS.join(",")];

  for (const [, p] of byPerson) {
    const lead_id = crypto.randomUUID();
    const repeat_engager = p.engaged_posts.size > 1 ? "true" : "false";
    rows.push(
      csvRow([
        lead_id,
        p.name,
        p.headline,
        p.linkedin_url,
        p.engagement_count,
        repeat_engager,
        p.latest_engagement_date,
        [...p.reaction_types].join("|") || "LIKE",
        [...p.engaged_posts].join("|"),
        "post-engagers",
      ])
    );
  }

  fs.writeFileSync(outPath, `\uFEFF${rows.join("\n")}\n`, "utf8");

  const summary = writeRunSummary({
    run: "post-engagers",
    query: postUrls.join(" "),
    counts: { posts: postUrls.length, unique_engagers: byPerson.size },
    topLeads: [...byPerson.values()].slice(0, 10).map((p) => ({ name: p.name, url: p.linkedin_url, why_match: p.headline })),
    cost,
    csvPath: outPath,
    mode: "confirmed",
  });

  console.log(`\nPost-engagers pull complete.`);
  console.log(`Posts processed : ${postUrls.length}`);
  console.log(`Unique engagers : ${byPerson.size}`);
  console.log(`Output          : ${outPath}`);
  console.log(`Summary         : ${summary}`);
  console.log(`\nNext step: Read skills/score-leads/SKILL.md and score this list with Claude Haiku.`);
  console.log(`  node scripts/score_leads_haiku.mjs -i ${outPath} -o outputs/${today}-post-engagers-scored.csv -b 8`);
}

main().catch((err) => {
  console.error("Fatal:", err.message);
  process.exit(1);
});
