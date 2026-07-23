#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  if compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    echo "PostgreSQL is ready."
    exit 0
  fi
  echo "Waiting for PostgreSQL... attempt $attempt/$MAX_ATTEMPTS"
  sleep "$SLEEP_SECONDS"
done

echo "ERROR: PostgreSQL did not become ready in time." >&2
exit 1
