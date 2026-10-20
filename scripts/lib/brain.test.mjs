import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { enrichmentBrief, parseH2, scoringRubric } from "./brain.mjs";
import { estimateEnrich, estimateFindLeads, estimateRapidApi, estimateScore } from "./costs.mjs";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../..");

test("parseH2 keeps section text and ignores other heading levels", () => {
  const sections = parseH2("# Title\n\nintro\n\n## ICP\nFounders\n\n### Detail\nstill ICP\n\n## Anti-ICP\nAgencies\n");
  assert.equal(sections.get("ICP"), "Founders\n\n### Detail\nstill ICP");
  assert.equal(sections.get("Anti-ICP"), "Agencies");
  assert.equal(sections.has("Title"), false);
});

test("scoring rubric uses offer sections and default bands", () => {
  const sections = new Map([
    ["ICP", "Founders who want time back"],
    ["Anti-ICP", "Agencies"],
    ["Positioning", "Less screen time"],
  ]);
  const rubric = scoringRubric(sections);
  assert.match(rubric, /Founders who want time back/);
  assert.match(rubric, /80-100/);
  assert.doesNotMatch(rubric, /Europe, US/);
});

test("enrichment brief includes voice and proof files", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gtm-brain-"));
  fs.writeFileSync(path.join(dir, "voice.md"), "short sentences");
  fs.writeFileSync(path.join(dir, "proof.md"), "newsletter readers");
  process.env.GTM_VOICE_PATH = path.join(dir, "voice.md");
  process.env.GTM_PROOF_PATH = path.join(dir, "proof.md");
  const sections = new Map([
    ["Offer", "Smart Operating System"],
    ["ICP", "Creators"],
    ["Positioning", "Time back"],
    ["Anti-ICP", "Enterprise"],
  ]);
  const brief = enrichmentBrief(sections);
  assert.match(brief, /Smart Operating System/);
  assert.match(brief, /short sentences/);
  assert.match(brief, /newsletter readers/);
  delete process.env.GTM_VOICE_PATH;
  delete process.env.GTM_PROOF_PATH;
});

test("cost estimates count calls and stay positive", () => {
  assert.deepEqual(estimateFindLeads().calls, { anthropic: 0, exa: 1, rapidapi: 0 });
  assert.equal(estimateScore({ leadCount: 25, batchSize: 20 }).calls.anthropic, 2);
  assert.equal(estimateEnrich({ leadCount: 3, webSearches: 1 }).calls.anthropic_web_search, 3);
  assert.equal(estimateRapidApi({ requests: 10 }).calls.rapidapi, 10);
  assert.ok(estimateFindLeads().estimated_usd > 0);
});

function runNode(script, args, extraEnv = {}) {
  return spawnSync(process.execPath, [script, ...args], {
    cwd: root,
    encoding: "utf8",
    env: { ...process.env, ...extraEnv },
  });
}

test("find-leads --estimate makes no Exa call", () => {
  const result = runNode("scripts/find_leads_exa.mjs", ["-q", "founders", "-n", "10", "--estimate"], {
    EXA_API_KEY: "",
    GTM_OFFER_PATH: path.join(os.tmpdir(), "missing-offer.md"),
  });
  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.calls.exa, 1);
  assert.equal(payload.paid_calls, false);
  assert.match(result.stderr, /Summary:/);
});

test("find-leads without --confirm refuses", () => {
  const result = runNode("scripts/find_leads_exa.mjs", ["-q", "founders", "-n", "10"], {
    EXA_API_KEY: "should-not-be-used",
    GTM_OFFER_PATH: path.join(os.tmpdir(), "missing-offer.md"),
  });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /--confirm/);
  assert.equal(JSON.parse(result.stdout).paid_calls, false);
});

test("score --estimate counts batches from the CSV and does not call Anthropic", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "gtm-score-"));
  const csv = path.join(dir, "leads.csv");
  fs.writeFileSync(csv, "title,url\nAda,https://linkedin.com/in/ada\nGrace,https://linkedin.com/in/grace\n");
  const result = runNode("scripts/score_leads_haiku.mjs", ["-i", csv, "-b", "20", "--estimate"], {
    ANTHROPIC_API_KEY: "",
  });
  assert.equal(result.status, 0, result.stderr);
  const payload = JSON.parse(result.stdout);
  assert.equal(payload.calls.anthropic, 1);
  assert.equal(payload.leadCount, 2);
  assert.equal(payload.paid_calls, false);
});
