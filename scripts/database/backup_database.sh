#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

bash "$SCRIPT_DIR/../runtime/wait_for_database.sh"
mkdir -p "$BACKUP_DIR"

stamp="$(date +%Y%m%d_%H%M%S)"
backup_file="$BACKUP_DIR/${POSTGRES_DB}-${stamp}.sql.gz"

compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$backup_file"

echo "Backup written to: $backup_file"
