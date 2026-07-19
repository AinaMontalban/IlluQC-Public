#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

BACKUP="${1:-}"
require_arg "$BACKUP" "BACKUP"

if [ ! -f "$BACKUP" ]; then
  echo "ERROR: backup file not found: $BACKUP" >&2
  exit 1
fi

bash "$SCRIPT_DIR/wait_for_db.sh"

echo "WARNING: this will drop and recreate database: $POSTGRES_DB"
compose exec -T db psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS $POSTGRES_DB;
CREATE DATABASE $POSTGRES_DB;
SQL

gunzip -c "$BACKUP" | compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1

echo "Restore completed from: $BACKUP"
