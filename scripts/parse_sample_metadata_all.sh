#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

RUNS_DIR="$RAW_DATA_DIR/"
OUT_DIR="$PROCESSED_DATA_DIR/Samples_Data"
mkdir -p "$OUT_DIR" "$LOG_DIR/parser"

found=0
failed=0

# Look for sample metadata files in each run folder
for run_dir in "$RUNS_DIR"/*/; do
  [ -d "$run_dir" ] || continue
  run_id="$(basename "$run_dir")"
  
  # Check for common sample metadata file patterns
  metadata_file=""
  if [ -f "$run_dir/run_samples_servolab.txt" ]; then
    metadata_file="$run_dir/run_samples_servolab.txt"
  elif [ -f "$run_dir/SampleSheet.csv" ]; then
    metadata_file="$run_dir/SampleSheet.csv"
  fi
  
  if [ -n "$metadata_file" ]; then
    found=1
    output_file="$OUT_DIR/${run_id}-samples-metadata.csv"
    echo "Parsing sample metadata for run: $run_id"
    
    if compose run --rm --entrypoint python parser \
      /opt/ngsqc/parser/Sample_Metadata/parse_sample_metadata.py \
      --input-file "/data/raw/$run_id/$(basename "$metadata_file")" \
      --output-file "/data/processed/Samples_Data/${run_id}-samples-metadata.csv" \
      --log-file "/logs/parser/${run_id}_sample_metadata.log" \
      > "$LOG_DIR/parser/${run_id}_sample_metadata.log" 2>&1; then
      echo "✓ Successfully parsed: $run_id"
    else
      echo "⚠ Failed to parse: $run_id (skipping)"
      ((failed++))
    fi
  fi
done

if [ "$found" -eq 0 ]; then
  echo "No sample metadata files found in $RUNS_DIR"
  exit 1
fi

if [ "$failed" -gt 0 ]; then
  echo "⚠ Sample metadata parsing completed with $failed error(s)"
  exit 0
else
  echo "✓ All sample metadata files parsed successfully"
  exit 0
fi
