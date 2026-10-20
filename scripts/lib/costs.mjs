// Approximate public list prices in USD. Printed before any paid call.
// They are estimates, not invoices. Update the numbers when a vendor changes price.

export const RATES = {
  exaSearchUsd: 0.007,
  anthropicHaikuInputPerMTok: 1,
  anthropicHaikuOutputPerMTok: 5,
  anthropicWebSearchUsd: 0.01,
  rapidApiLinkedinUsd: 0.005,
};

function roundUsd(n) {
  return Math.round(n * 10000) / 10000;
}

function money(inputTokens, outputTokens, extra = 0) {
  const usd =
    (inputTokens / 1_000_000) * RATES.anthropicHaikuInputPerMTok +
    (outputTokens / 1_000_000) * RATES.anthropicHaikuOutputPerMTok +
    extra;
  return roundUsd(usd);
}

export function estimateFindLeads() {
  return {
    calls: { anthropic: 0, exa: 1, rapidapi: 0 },
    estimated_usd: RATES.exaSearchUsd,
    note: "One Exa search. Result count does not add calls.",
  };
}

export function estimateScore({ leadCount, batchSize }) {
  const size = batchSize > 0 ? batchSize : 20;
  const leads = Math.max(0, leadCount);
  const batches = leads === 0 ? 0 : Math.ceil(leads / size);
  const inputTokens = batches * 700 + leads * 180;
  const outputTokens = leads * 70;
  return {
    calls: { anthropic: batches, exa: 0, rapidapi: 0 },
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    estimated_usd: money(inputTokens, outputTokens),
    note: "One Anthropic Messages call per batch. No web search.",
  };
}

export function estimateEnrich({ leadCount, webSearches }) {
  const leads = Math.max(0, leadCount);
  const searchesEach = webSearches > 0 ? webSearches : 0;
  const inputTokens = leads * 1400;
  const outputTokens = leads * 450;
  const searchCalls = leads * searchesEach;
  return {
    calls: { anthropic: leads, exa: 0, rapidapi: 0, anthropic_web_search: searchCalls },
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    estimated_usd: money(inputTokens, outputTokens, searchCalls * RATES.anthropicWebSearchUsd),
    note: "One Anthropic Messages call per lead, plus up to --web-searches server-side searches each.",
  };
}

export function estimateRapidApi({ requests }) {
  const n = Math.max(0, requests);
  return {
    calls: { anthropic: 0, exa: 0, rapidapi: n },
    estimated_usd: roundUsd(n * RATES.rapidApiLinkedinUsd),
    note: "RapidAPI linkedin-api8 price depends on the subscribed plan. This uses $0.005 per request as a ceiling-style placeholder.",
  };
}
