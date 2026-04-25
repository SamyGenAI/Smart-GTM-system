#!/usr/bin/env bash
# Fetch LinkedIn profile via RapidAPI linkedin-api8.
# Usage: rapidapi-linkedin.sh <linkedin-username-or-url>
# Reads RAPIDAPI_KEY from env.

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo '{"error":"missing_input","hint":"pass LinkedIn username or URL"}' >&2
  exit 2
fi

if [[ -z "${RAPIDAPI_KEY:-}" ]]; then
  echo '{"error":"missing_credential","var":"RAPIDAPI_KEY"}' >&2
  exit 3
fi

raw="$1"
clean="${raw%%\?*}"
clean="${clean%%#*}"
clean="${clean%/}"
username="${clean##*/in/}"
username="${username##*/}"

if [[ -z "$username" ]]; then
  echo '{"error":"could_not_parse_username","input":"'"$raw"'"}' >&2
  exit 2
fi

http_code=$(curl -sS -o /tmp/rapidapi_li_body.json -w '%{http_code}' \
  --get "https://linkedin-api8.p.rapidapi.com/profile-data-connection-count-posts" \
  --data-urlencode "username=${username}" \
  -H "X-RapidAPI-Key: ${RAPIDAPI_KEY}" \
  -H "X-RapidAPI-Host: linkedin-api8.p.rapidapi.com")

if [[ "$http_code" != "200" ]]; then
  echo "{\"error\":\"http_${http_code}\",\"username\":\"${username}\"}" >&2
  cat /tmp/rapidapi_li_body.json >&2 || true
  exit 4
fi

cat /tmp/rapidapi_li_body.json
