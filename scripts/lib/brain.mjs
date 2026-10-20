import fs from "node:fs";
import path from "node:path";

// ICP, positioning, voice, and proof live in the private vault.
// This repo never copies that text. Scripts read it in place.

export const REQUIRED_OFFER_HEADINGS = ["Offer", "ICP", "Anti-ICP", "Positioning"];

export const OPTIONAL_OFFER_HEADINGS = ["Geography", "Buyer", "Scoring", "LinkedIn", "Competitors"];

export function offerPath() {
  return process.env.GTM_OFFER_PATH || path.join("brain", "raw", "me", "offer.md");
}

export function siblingMe(name) {
  const envKey = name === "voice.md" ? "GTM_VOICE_PATH" : name === "proof.md" ? "GTM_PROOF_PATH" : "";
  if (envKey && process.env[envKey]) return process.env[envKey];
  return path.join(path.dirname(offerPath()), name);
}

// Split a markdown file on level-2 headings. The heading text is the map key.
export function parseH2(markdown) {
  const sections = new Map();
  let current = null;
  const buf = [];
  const flush = () => {
    if (current) sections.set(current, buf.join("\n").trim());
    buf.length = 0;
  };
  for (const line of String(markdown ?? "").split(/\r?\n/)) {
    const match = /^##\s+(.+?)\s*$/.exec(line);
    if (match) {
      flush();
      current = match[1].trim();
    } else if (current) {
      buf.push(line);
    }
  }
  flush();
  return sections;
}

export function loadOffer({ required = REQUIRED_OFFER_HEADINGS } = {}) {
  const file = offerPath();
  if (!fs.existsSync(file)) {
    throw new Error(
      [
        `Missing ${file}.`,
        "ICP and positioning are read from the vault, not from local templates.",
        "Check the brain submodule out, then add the headings listed in context/README.md.",
        "git submodule add -b main https://github.com/SamyGenAI/Samy-SmartOS.git brain",
      ].join("\n"),
    );
  }
  const text = fs.readFileSync(file, "utf8");
  const sections = parseH2(text);
  const missing = required.filter((heading) => !sections.get(heading));
  if (missing.length > 0) {
    throw new Error(
      `${file} is missing ${missing.map((h) => `## ${h}`).join(", ")}. Add those headings in the vault. Do not copy the offer into this repo.`,
    );
  }
  return { path: file, text, sections };
}

export function readClipped(file, maxChars) {
  if (!file || !fs.existsSync(file)) return "";
  const raw = fs.readFileSync(file, "utf8").trim();
  if (raw.length <= maxChars) return raw;
  return `${raw.slice(0, maxChars)}\n[truncated]`;
}

// Text the scorer sends. The who/what comes only from offer.md.
export function scoringRubric(sections) {
  const parts = ["## ICP", sections.get("ICP"), "## Anti-ICP", sections.get("Anti-ICP")];
  for (const heading of ["Geography", "Buyer", "Positioning", "Scoring"]) {
    const body = sections.get(heading);
    if (body) parts.push(`## ${heading}`, body);
  }
  if (!sections.get("Scoring")) {
    parts.push(
      "## Scoring",
      "80-100: strong fit on the ICP above.",
      "60-79: decent fit, one important signal missing.",
      "40-59: weak or ambiguous.",
      "0-39: poor fit or anti-ICP.",
    );
  }
  return parts.filter(Boolean).join("\n\n");
}

// Text the enrichment prompt sends: offer + voice + proof, clipped.
export function enrichmentBrief(sections) {
  const parts = [
    "## Offer",
    sections.get("Offer"),
    "## ICP",
    sections.get("ICP"),
    "## Positioning",
    sections.get("Positioning"),
  ];
  for (const heading of ["Anti-ICP", "Buyer"]) {
    const body = sections.get(heading);
    if (body) parts.push(`## ${heading}`, body);
  }
  const voice = readClipped(siblingMe("voice.md"), 1500);
  const proof = readClipped(siblingMe("proof.md"), 1500);
  if (voice) parts.push("## Voice", voice);
  if (proof) parts.push("## Proof", proof);
  const brief = parts.filter(Boolean).join("\n\n");
  return brief.length > 4500 ? `${brief.slice(0, 4500)}\n[truncated]` : brief;
}

export function brainCheckedOut() {
  return fs.existsSync(path.join("brain", ".git")) || fs.existsSync(path.join("brain", "raw", "me"));
}
