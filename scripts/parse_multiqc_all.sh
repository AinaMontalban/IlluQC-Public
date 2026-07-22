#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

RUNS_DIR="$ILLUMINA_RAW_DATA_DIR"
OUT_DIR="/data/processed/Samples_Data"
mkdir -p "$PROCESSED_DATA_DIR/Samples_Data" "$LOG_DIR/parser"

found=0
failed=0
for run_dir in "$RUNS_DIR"/*/; do
  [ -d "$run_dir" ] || continue
  run_id="$(basename "$run_dir")"
  multiqc_file="$run_dir/multiqc_general_stats.txt"
  if [ -f "$multiqc_file" ]; then
    found=1
    echo "Processing MultiQC for run: $run_id"
    if compose run --rm --entrypoint python parser \
      /opt/ngsqc/parser/MultiQC/multiqc_data_parser.py \
      "/data/raw/illumina/$run_id/multiqc_general_stats.txt" \
      --run-id "$run_id" \
      --format csv \
      --output-dir "$OUT_DIR" \
      > "$LOG_DIR/parser/${run_id}_multiqc.log" 2>&1; then
      echo "✓ Successfully processed: $run_id"
    else
      echo "⚠ Failed to process: $run_id (skipping)"
      ((failed++))
    fi
  fi
done

if [ "$found" -eq 0 ]; then
  echo "No multiqc_general_stats.txt files found in $RUNS_DIR"
  exit 1
fi

if [ "$failed" -gt 0 ]; then
  echo "⚠ MultiQC parsing completed with $failed error(s)"
  exit 0
else
  echo "✓ All MultiQC files parsed successfully"
  exit 0
fi
