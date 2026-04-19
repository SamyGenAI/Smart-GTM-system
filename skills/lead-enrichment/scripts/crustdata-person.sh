#!/usr/bin/env bash
# Enrich a person via Crustdata /person/enrich.
# Usage: crustdata-person.sh <linkedin-url>
# Reads CRUSTDATA_API_KEY from env.

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo '{"error":"missing_input","hint":"pass LinkedIn profile URL"}' >&2
  exit 2
fi

if [[ -z "${CRUSTDATA_API_KEY:-}" ]]; then
  echo '{"error":"missing_credential","var":"CRUSTDATA_API_KEY"}' >&2
  exit 3
fi

url="$1"

payload=$(printf '{"professional_network_profile_urls":["%s"]}' "$url")

http_code=$(curl -sS -o /tmp/crustdata_person_body.json -w '%{http_code}' \
  -X POST "https://api.crustdata.com/person/enrich" \
  -H "Authorization: Bearer ${CRUSTDATA_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "x-api-version: 2025-11-01" \
  --data "$payload")

if [[ "$http_code" != "200" ]]; then
  echo "{\"error\":\"http_${http_code}\",\"url\":\"${url}\"}" >&2
  cat /tmp/crustdata_person_body.json >&2 || true
  exit 4
fi

cat /tmp/crustdata_person_body.json
