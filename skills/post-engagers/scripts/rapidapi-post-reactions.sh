#!/usr/bin/env bash
# Fetch reactors on a LinkedIn post via RapidAPI linkedin-api8 /get-post-reactions.
# Usage: rapidapi-post-reactions.sh <post_url> [page] [reaction_type]
# Reads RAPIDAPI_KEY from env.
# reaction_type: "" (all), "LIKE", "CELEBRATE", "SUPPORT", "LOVE", "INSIGHTFUL", "FUNNY"

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo '{"error":"missing_input","hint":"pass LinkedIn post URL"}' >&2
  exit 2
fi

if [[ -z "${RAPIDAPI_KEY:-}" ]]; then
  echo '{"error":"missing_credential","var":"RAPIDAPI_KEY"}' >&2
  exit 3
fi

post_url="$1"
page="${2:-1}"
reaction_type="${3:-}"

payload=$(printf '{"url":"%s","page":%d,"reactionType":"%s"}' "$post_url" "$page" "$reaction_type")

http_code=$(curl -sS -o /tmp/rapidapi_reactions_body.json -w '%{http_code}' \
  -X POST "https://linkedin-api8.p.rapidapi.com/get-post-reactions" \
  -H "X-RapidAPI-Key: ${RAPIDAPI_KEY}" \
  -H "X-RapidAPI-Host: linkedin-api8.p.rapidapi.com" \
  -H "Content-Type: application/json" \
  --data "$payload")

if [[ "$http_code" != "200" ]]; then
  echo "{\"error\":\"http_${http_code}\",\"post_url\":\"${post_url}\",\"page\":${page}}" >&2
  cat /tmp/rapidapi_reactions_body.json >&2 || true
  exit 4
fi

cat /tmp/rapidapi_reactions_body.json
