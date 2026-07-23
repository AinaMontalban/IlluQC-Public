#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

bash "$SCRIPT_DIR/../runtime/wait_for_database.sh"
mkdir -p "$LOG_DIR/loader"

load_table() {
  local table="$1"
  local csv_path="$2"
  if [ ! -f "$PROCESSED_DATA_DIR/$csv_path" ]; then
    echo "WARNING: missing reference CSV: $PROCESSED_DATA_DIR/reference_tables/$csv_path" >&2
    return 0
  fi

  echo "Loading reference table: $table"
  compose run --rm loader \
    --host db \
    --port 5432 \
    --db "$POSTGRES_DB" \
    --user "$POSTGRES_USER" \
    --table "$table" \
    --csv "/data/processed/$csv_path" \
    --fields "/opt/illuqc/db/required_fields.json" \
    > "$LOG_DIR/loader/${table}_loader.log" 2>&1
}

load_table instruments sequencing_instruments.csv
load_table sequencing_chemistry sequencing_chemistry.csv
load_table library libraries.csv

echo "Reference table loading finished. Logs: $LOG_DIR/loader"
