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

// ---------------------------------------------------------------------------
// Arg parser
// ---------------------------------------------------------------------------
function parseArgs(argv) {
  const args = { input: "", out: "" };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if ((token === "--out" || token === "-o") && argv[i + 1]) {
      args.out = argv[i + 1];
      i += 1;
    } else if (!token.startsWith("-") && !args.input) {
      args.input = token;
    }
  }
  return args;
}

// ---------------------------------------------------------------------------
// HTML entity decoder
// ---------------------------------------------------------------------------
const HTML_ENTITIES = {
  "&amp;": "&",
  "&lt;": "<",
  "&gt;": ">",
  "&quot;": '"',
  "&#39;": "'",
  "&apos;": "'",
  "&nbsp;": " ",
  "&#x27;": "'",
  "&#x2F;": "/",
  "&#x60;": "`",
  "&#x3D;": "=",
};

function decodeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&[a-z0-9#]+;/gi, (entity) => HTML_ENTITIES[entity] ?? entity)
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
}

function clean(value) {
  return decodeHtml(String(value ?? "")).trim();
}

// ---------------------------------------------------------------------------
// Date helpers
// ---------------------------------------------------------------------------
function formatDate(obj) {
  if (!obj) return "";
  const { year, month, day } = obj;
  if (year && month) return `${monthName(month)} ${year}`;
  if (year) return String(year);
  return "";
}

function monthName(n) {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return months[(Number(n) - 1) % 12] ?? String(n);
}

function dateRange(start, end) {
  const s = formatDate(start);
  const e = end ? formatDate(end) : "Present";
  if (!s) return "";
  return `${s} – ${e}`;
}

// ---------------------------------------------------------------------------
// Markdown builder
// ---------------------------------------------------------------------------
function buildMarkdown(raw) {
  // Support both direct data object and wrapped { connection, data } shape
  const profile = raw?.data ?? raw;
  const connection = raw?.connection ?? null;

  const firstName = clean(profile?.firstName);
  const lastName = clean(profile?.lastName);
  const fullName = [firstName, lastName].filter(Boolean).join(" ") || "Unknown";
  const headline = clean(profile?.headline);
  const summary = clean(profile?.summary);

  // Location
  const geo = profile?.geo;
  const location = clean(geo?.full ?? geo?.city ?? geo?.country ?? "");

  // Stats
  const followers = profile?.followerCount ?? null;
  const connections = connection ?? profile?.connectionCount ?? null;
  const isPremium = profile?.isPremium ?? false;
  const isCreator = profile?.isCreator ?? false;

  // Experience
  const positions = Array.isArray(profile?.position) ? profile.position : [];

  // Education
  const educations = Array.isArray(profile?.educations) ? profile.educations : [];

  // Skills
  const skills = Array.isArray(profile?.skills) ? profile.skills : [];

  // --- Build markdown ---
  const lines = [];

  lines.push(`# ${fullName}`);
  lines.push("");

  if (headline) lines.push(`**${headline}**`);
  lines.push("");

  lines.push("## Overview");
  lines.push("");
  if (location) lines.push(`- **Location:** ${location}`);
  if (connections !== null) lines.push(`- **Connections:** ${connections.toLocaleString()}`);
  if (followers !== null) lines.push(`- **Followers:** ${followers.toLocaleString()}`);
  lines.push(`- **Premium:** ${isPremium ? "Yes" : "No"}`);
  lines.push(`- **Creator mode:** ${isCreator ? "Yes" : "No"}`);
  lines.push("");

  if (summary) {
    lines.push("## About");
    lines.push("");
    lines.push(summary);
    lines.push("");
  }

  if (positions.length > 0) {
    lines.push("## Experience");
    lines.push("");
    const shown = positions.slice(0, 5);
    for (const pos of shown) {
      const title = clean(pos?.title);
      const company = clean(pos?.companyName ?? pos?.company?.name ?? pos?.company);
      const range = dateRange(pos?.start ?? pos?.timePeriod?.startDate, pos?.end ?? pos?.timePeriod?.endDate);
      const description = clean(pos?.description);

      lines.push(`### ${title || "(Role unknown)"}${company ? ` · ${company}` : ""}`);
      if (range) lines.push(`*${range}*`);
      if (description) {
        const snippet = description.length > 300 ? `${description.slice(0, 300)}…` : description;
        lines.push("");
        lines.push(snippet);
      }
      lines.push("");
    }
  }

  if (educations.length > 0) {
    lines.push("## Education");
    lines.push("");
    const shown = educations.slice(0, 3);
    for (const edu of shown) {
      const school = clean(edu?.schoolName ?? edu?.school?.name ?? edu?.school);
      const degree = clean(edu?.degreeName ?? edu?.degree);
      const field = clean(edu?.fieldOfStudy);
      const range = dateRange(edu?.start ?? edu?.timePeriod?.startDate, edu?.end ?? edu?.timePeriod?.endDate);

      const degreeField = [degree, field].filter(Boolean).join(", ");
      lines.push(`### ${school || "(School unknown)"}`);
      if (degreeField) lines.push(degreeField);
      if (range) lines.push(`*${range}*`);
      lines.push("");
    }
  }

  if (skills.length > 0) {
    lines.push("## Top Skills");
    lines.push("");
    const shown = skills.slice(0, 10);
    for (const skill of shown) {
      const name = clean(skill?.name ?? skill);
      if (name) lines.push(`- ${name}`);
    }
    lines.push("");
  }

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const args = parseArgs(process.argv);

  if (!args.input) {
    console.error(
      [
        "Usage:",
        "  node scripts/parse_linkedin_profile.mjs <input.json>",
        "  node scripts/parse_linkedin_profile.mjs <input.json> --out <output.md>",
        "",
        "Reads a raw LinkedIn profile JSON produced by rapidapi_linkedin_profile.mjs --out",
        "and outputs a clean markdown summary.",
      ].join("\n")
    );
    process.exit(1);
  }

  if (!fs.existsSync(args.input)) {
    console.error(`File not found: ${args.input}`);
    process.exit(1);
  }

  let raw;
  try {
    raw = JSON.parse(fs.readFileSync(args.input, "utf8").replace(/^\uFEFF/, ""));
  } catch (err) {
    console.error(`Failed to parse JSON: ${err.message}`);
    process.exit(1);
  }

  const markdown = buildMarkdown(raw);

  if (args.out) {
    fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
    fs.writeFileSync(args.out, markdown, "utf8");
    console.error(`Profile summary saved → ${args.out}`);
  } else {
    process.stdout.write(markdown + "\n");
  }
}

main().catch((err) => {
  console.error("Fatal:", err.message);
  process.exit(1);
});
