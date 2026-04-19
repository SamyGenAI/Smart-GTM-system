#!/usr/bin/env bash
# Query Crustdata /job/search for recent job postings at a company.
# Usage: crustdata-jobs.sh <company_id> [since_yyyy_mm_dd] [limit]
# Reads CRUSTDATA_API_KEY from env.
# company_id comes from Crustdata (company.basic_info.company_id). If you only
# have a domain or name, resolve it upstream first.

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo '{"error":"missing_input","hint":"pass Crustdata company_id"}' >&2
  exit 2
fi

if [[ -z "${CRUSTDATA_API_KEY:-}" ]]; then
  echo '{"error":"missing_credential","var":"CRUSTDATA_API_KEY"}' >&2
  exit 3
fi

company_id="$1"
since="${2:-2025-01-01}"
limit="${3:-10}"

payload=$(cat <<EOF
{
  "filters": {
    "op": "and",
    "conditions": [
      { "field": "company.basic_info.company_id", "type": "=",  "value": ${company_id} },
      { "field": "metadata.date_added",           "type": "=>", "value": "${since}" }
    ]
  },
  "fields": [
    "job_details.title",
    "job_details.category",
    "job_details.url",
    "metadata.date_added",
    "location.country",
    "location.city"
  ],
  "sorts": [
    { "column": "metadata.date_added", "order": "desc" }
  ],
  "limit": ${limit}
}
EOF
)

http_code=$(curl -sS -o /tmp/crustdata_jobs_body.json -w '%{http_code}' \
  -X POST "https://api.crustdata.com/job/search" \
  -H "Authorization: Bearer ${CRUSTDATA_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "x-api-version: 2025-11-01" \
  --data "$payload")

if [[ "$http_code" != "200" ]]; then
  echo "{\"error\":\"http_${http_code}\",\"company_id\":\"${company_id}\"}" >&2
  cat /tmp/crustdata_jobs_body.json >&2 || true
  exit 4
fi

cat /tmp/crustdata_jobs_body.json
