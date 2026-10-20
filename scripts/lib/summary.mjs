import fs from "node:fs";
import path from "node:path";
import { brainCheckedOut } from "./brain.mjs";

const SHEETS_FOLDER = "https://drive.google.com/drive/folders/1JuNMJvV8uTT9o41m8TpZLO5F0tuh3Jow";

function slug(value) {
  return String(value || "run")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 40) || "run";
}

export function summaryDir(run) {
  const date = new Date().toISOString().slice(0, 10);
  const folder = `${date}-${slug(run)}`;
  const root = brainCheckedOut()
    ? path.join("brain", "outputs", "gtm")
    : path.join("outputs", "gtm-pending");
  return path.join(root, folder);
}

function leadLine(lead) {
  const name = lead.name || lead.title || "(no name)";
  const url = lead.url || lead.linkedin_url || "";
  const score = lead.score ?? "";
  const why = lead.why_match || lead.why || "";
  return `| ${name.replaceAll("|", "/")} | ${url} | ${score} | ${String(why).replaceAll("|", "/").slice(0, 140)} |`;
}

export function writeRunSummary({ run, query, counts, topLeads, cost, csvPath, mode, notes }) {
  const dir = summaryDir(run);
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, "summary.md");
  const calls = cost?.calls ?? {};
  const leads = Array.isArray(topLeads) ? topLeads.slice(0, 10) : [];
  const countLines = Object.entries(counts ?? {})
    .map(([key, value]) => `- ${key}: ${value}`)
    .join("\n");
  const body = [
    `# GTM run: ${run}`,
    "",
    `- Date: ${new Date().toISOString()}`,
    `- Mode: ${mode || "confirmed"}`,
    `- Query: ${query || "(none)"}`,
    "",
    "## Counts",
    "",
    countLines || "- (none)",
    "",
    "## Cost",
    "",
    `- Anthropic calls: ${calls.anthropic ?? 0}`,
    `- Anthropic web searches: ${calls.anthropic_web_search ?? 0}`,
    `- Exa calls: ${calls.exa ?? 0}`,
    `- RapidAPI calls: ${calls.rapidapi ?? 0}`,
    `- Estimated USD: ${cost?.estimated_usd ?? 0}`,
    cost?.note ? `- Note: ${cost.note}` : "",
    "",
    "## Top leads",
    "",
    leads.length ? "| Name | URL | Score | Why |\n|---|---|---|---|\n" + leads.map(leadLine).join("\n") : "No leads in this step.",
    "",
    "## Output",
    "",
    `- CSV: ${csvPath || "(none)"}`,
    `- Sheets folder: ${SHEETS_FOLDER}`,
    `- Summary: ${file}`,
    brainCheckedOut()
      ? null
      : "- Brain submodule is not checked out. This summary is staged under outputs/gtm-pending/ until `brain/` is available. Move it to `brain/outputs/gtm/` in the vault. Do not copy raw/.",
    "",
    "## Review",
    "",
    "Nothing was sent, enrolled, or posted. Samy reviews this list, then hands it to the Grok Bot GTM team. See pipelines/handoffs.md.",
    notes ? `\n${notes}` : null,
    "",
  ]
    .filter((line) => line !== null)
    .join("\n");
  fs.writeFileSync(file, `${body}\n`, "utf8");
  return file;
}
