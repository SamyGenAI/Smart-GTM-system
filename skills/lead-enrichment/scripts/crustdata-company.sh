#!/usr/bin/env bash
# Resolve a company's Crustdata company_id from its primary domain.
# Usage: crustdata-company.sh <domain>
# Reads CRUSTDATA_API_KEY from env.

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo '{"error":"missing_input","hint":"pass company primary domain, e.g. retool.com"}' >&2
  exit 2
fi

if [[ -z "${CRUSTDATA_API_KEY:-}" ]]; then
  echo '{"error":"missing_credential","var":"CRUSTDATA_API_KEY"}' >&2
  exit 3
fi

raw="$1"
# Normalize: strip scheme, www., trailing slash.
domain="${raw#http://}"
domain="${domain#https://}"
domain="${domain#www.}"
domain="${domain%%/*}"

payload=$(cat <<EOF
{
  "filters": {
    "field": "basic_info.primary_domain",
    "type": "=",
    "value": "${domain}"
  },
  "limit": 1,
  "fields": [
    "crustdata_company_id",
    "basic_info.name",
    "basic_info.primary_domain",
    "basic_info.year_founded",
    "headcount.total",
    "locations.hq_country",
    "funding.total_investment_usd"
  ]
}
EOF
)

http_code=$(curl -sS -o /tmp/crustdata_company_body.json -w '%{http_code}' \
  -X POST "https://api.crustdata.com/company/search" \
  -H "Authorization: Bearer ${CRUSTDATA_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "x-api-version: 2025-11-01" \
  --data "$payload")

if [[ "$http_code" != "200" ]]; then
  echo "{\"error\":\"http_${http_code}\",\"domain\":\"${domain}\"}" >&2
  cat /tmp/crustdata_company_body.json >&2 || true
  exit 4
fi

cat /tmp/crustdata_company_body.json
