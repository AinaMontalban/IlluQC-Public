#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

RUN_ID="${1:-}"
require_arg "$RUN_ID" "RUN_ID"

bash "$SCRIPT_DIR/../runtime/wait_for_database.sh"
mkdir -p "$LOG_DIR/loader"

load_if_exists() {
  local table="$1"
  local container_csv="$2"
  local host_csv="$3"

  if [ ! -f "$host_csv" ]; then
    echo "WARNING: skipping missing CSV for $table: $host_csv" >&2
    return 0
  fi

  echo "Loading $table from $host_csv"
  compose run --rm loader \
    --host db \
    --port 5432 \
    --db "$POSTGRES_DB" \
    --user "$POSTGRES_USER" \
    --table "$table" \
    --csv "$container_csv" \
    --fields "/opt/illuqc/db/required_fields.json" \
    >> "$LOG_DIR/loader/${RUN_ID}_loader.log" 2>&1
}

: > "$LOG_DIR/loader/${RUN_ID}_loader.log"

load_if_exists sequencing_run \
  "/data/processed/Runs_Data/${RUN_ID}-sequencing-info.csv" \
  "$PROCESSED_DATA_DIR/Runs_Data/${RUN_ID}-sequencing-info.csv"

load_if_exists sequencing_qc_metrics \
  "/data/processed/Runs_Data/${RUN_ID}-sequencing-metrics.csv" \
  "$PROCESSED_DATA_DIR/Runs_Data/${RUN_ID}-sequencing-metrics.csv"

echo "Run loading finished for $RUN_ID. Log: $LOG_DIR/loader/${RUN_ID}_loader.log"
