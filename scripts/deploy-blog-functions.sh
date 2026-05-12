#!/usr/bin/env bash
# Deploy Pages Functions + wrangler.toml (D1 binding) with correct _valid-paths for your tree.
#
# Usage:
#   ./scripts/deploy-blog-functions.sh /path/to/your-static-site-root
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE="${1:-}"

if [[ -z "${SITE}" || ! -d "${SITE}" ]]; then
  echo "Usage: $0 /absolute/path/to/production/site/root"
  exit 1
fi

node "${ROOT}/scripts/sync-functions-for-static-site.mjs" "${SITE}"

echo "Deploying Pages project db-garage-doors from ${SITE} …"
cd "${SITE}"
exec npx wrangler pages deploy . --project-name=db-garage-doors --branch=main --commit-dirty=true
