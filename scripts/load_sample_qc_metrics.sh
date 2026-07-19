#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

bash "$SCRIPT_DIR/wait_for_db.sh"
mkdir -p "$LOG_DIR/loader"

SAMPLES_DIR="$PROCESSED_DATA_DIR/Samples_Data"
if [ ! -d "$SAMPLES_DIR" ]; then
  echo "ERROR: samples data directory not found: $SAMPLES_DIR" >&2
  exit 1
fi

load_sample_qc_file() {
  local table="$1"
  local file_pattern="$2"
  
  echo "Loading $table from $file_pattern files..."
  
  found=0
  failed=0
  for csv_file in "$SAMPLES_DIR"/$file_pattern; do
    [ -f "$csv_file" ] || continue
    found=1
    filename=$(basename "$csv_file")
    
    echo "Loading: $filename into $table"
    if compose run --rm loader \
      --host db \
      --port 5432 \
      --db "$POSTGRES_DB" \
      --user "$POSTGRES_USER" \
      --password "$POSTGRES_PASSWORD" \
      --table "$table" \
      --csv "/data/processed/Samples_Data/$filename" \
      --fields "/opt/ngsqc/db/required_fields.json" \
      > "$LOG_DIR/loader/${filename%.csv}_loader.log" 2>&1; then
      echo "✓ Loaded: $filename"
    else
      echo "⚠ Failed to load: $filename"
      ((failed++))
    fi
  done
  
  if [ "$found" -eq 0 ]; then
    echo "⚠ No $file_pattern files found in $SAMPLES_DIR"
    return 1
  fi
  
  if [ "$failed" -gt 0 ]; then
    echo "⚠ Loaded $((found - failed))/$found files (with $failed errors)"
    return 0
  else
    echo "✓ All $file_pattern files loaded successfully"
    return 0
  fi
}

# Load only sample QC metrics
load_sample_qc_file "sample_qc_metrics" "*-samples-qc-metrics.csv"

echo "Sample QC metrics loading finished. Logs: $LOG_DIR/loader"
