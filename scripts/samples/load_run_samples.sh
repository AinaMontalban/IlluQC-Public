#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

RUN_ID="${1:-}"
SAMPLE_ID="${2:-}"
require_arg "$RUN_ID" "RUN_ID"

if [ -n "$SAMPLE_ID" ]; then
  SCOPE_DIR="$PROCESSED_DATA_DIR/Samples_Data/$RUN_ID/samples/$SAMPLE_ID"
  LOG_STEM="${RUN_ID}-${SAMPLE_ID}"
  CONTAINER_SCOPE="/data/processed/Samples_Data/$RUN_ID/samples/$SAMPLE_ID"
else
  SCOPE_DIR="$PROCESSED_DATA_DIR/Samples_Data/$RUN_ID"
  LOG_STEM="$RUN_ID"
  CONTAINER_SCOPE="/data/processed/Samples_Data/$RUN_ID"
fi
READY_DIR="$SCOPE_DIR/load-ready"

for file in samples.csv sample-qc-metrics.csv; do
  if [ ! -s "$READY_DIR/$file" ]; then
    echo "ERROR: missing load-ready file: $READY_DIR/$file" >&2
    if [ -n "$SAMPLE_ID" ]; then
      echo "Run 'illuqc prepare-sample $RUN_ID $SAMPLE_ID' first." >&2
    else
      echo "Run 'illuqc prepare-samples $RUN_ID' first." >&2
    fi
    exit 1
  fi
done

bash "$SCRIPT_DIR/../runtime/wait_for_database.sh"
mkdir -p "$LOG_DIR/loader"
LOG_FILE="$LOG_DIR/loader/${LOG_STEM}-samples.log"
: > "$LOG_FILE"

load_file() {
  local table="$1"
  local filename="$2"
  echo "Loading $table from $READY_DIR/$filename"
  compose run --rm loader \
    --host db --port 5432 \
    --db "$POSTGRES_DB" --user "$POSTGRES_USER" \
    --table "$table" \
    --csv "$CONTAINER_SCOPE/load-ready/$filename" \
    --fields /opt/illuqc/db/required_fields.json \
    >> "$LOG_FILE" 2>&1
}

load_file samples samples.csv
load_file sample_qc_metrics sample-qc-metrics.csv

echo "Sample loading completed."
echo "Run: $RUN_ID"
echo "Scope: ${SAMPLE_ID:-all samples}"
echo "Log: $LOG_FILE"
