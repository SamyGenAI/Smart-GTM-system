import fs from "node:fs";
import path from "node:path";
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
  const args = { input: "", out: "" };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if ((token === "--username" || token === "-u") && argv[i + 1]) {
      args.input = argv[i + 1];
      i += 1;
    } else if ((token === "--out" || token === "-o") && argv[i + 1]) {
      args.out = argv[i + 1];
      i += 1;
    } else if (!token.startsWith("-") && !args.input) {
      args.input = token;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// Parse username from raw URL or plain handle
// ---------------------------------------------------------------------------
function parseUsername(raw) {
  let clean = raw.split("?")[0].split("#")[0].replace(/\/$/, "");
  if (clean.includes("/in/")) {
    clean = clean.split("/in/")[1].replace(/\/$/, "");
  }
  return clean.split("/").pop() || "";
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  loadEnv();

  const args = parseArgs(process.argv);

  if (!args.input) {
    console.error(
      JSON.stringify({
        error: "missing_input",
        hint: "pass LinkedIn username or URL via --username / -u, or as a positional arg",
      })
    );
    process.exit(2);
  }

  const username = parseUsername(args.input);
  if (!username) {
    console.error(JSON.stringify({ error: "could_not_parse_username", input: args.input }));
    process.exit(2);
  }

  const cost = estimateRapidApi({ requests: 1 });
  const decision = gatePaid({
    argv: process.argv,
    estimate: cost,
    extra: { username, calls_detail: "1 RapidAPI profile request" },
  });
  if (decision !== "confirmed") {
    const summary = writeRunSummary({
      run: "linkedin-profile",
      query: username,
      counts: { requests: 1 },
      topLeads: [],
      cost,
      csvPath: args.out || null,
      mode: decision,
    });
    process.stderr.write(`Summary: ${summary}\n`);
    process.exit(decision === "estimate" ? 0 : 2);
  }

  const key = process.env.RAPIDAPI_KEY;
  if (!key) {
    console.error(JSON.stringify({ error: "missing_credential", var: "RAPIDAPI_KEY" }));
    process.exit(3);
  }

  const url = `https://linkedin-api8.p.rapidapi.com/profile-data-connection-count-posts?username=${encodeURIComponent(username)}`;

  let result;
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "x-rapidapi-key": key,
        "x-rapidapi-host": "linkedin-api8.p.rapidapi.com",
        "Content-Type": "application/json",
      },
    });

    const text = await response.text();

    if (!response.ok) {
      console.error(JSON.stringify({ error: `http_${response.status}`, username }));
      console.error(text);
      process.exit(4);
    }

    result = text;
  } catch (err) {
    console.error(JSON.stringify({ error: "fetch_failed", message: err.message }));
    process.exit(5);
  }

  if (args.out) {
    fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
    fs.writeFileSync(args.out, result, "utf8");
    console.error(`Profile saved → ${args.out}`);
  } else {
    console.log(result);
  }
}

main();
