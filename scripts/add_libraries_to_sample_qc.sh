#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

# Directories
INPUT_RUNS_DIR="$ILLUMINA_RAW_DATA_DIR"
PROCESSED_SAMPLES_DIR="$PROCESSED_DATA_DIR/Samples_Data"
LOG_DIR="${LOG_DIR:-$PWD/logs}"
mkdir -p "$LOG_DIR"

if [ ! -d "$PROCESSED_SAMPLES_DIR" ]; then
  echo "ERROR: Processed samples directory not found: $PROCESSED_SAMPLES_DIR" >&2
  exit 1
fi

echo "Adding library IDs to sample QC metrics..."
echo "Input runs: $INPUT_RUNS_DIR"
echo "Processed samples: $PROCESSED_SAMPLES_DIR"
echo "Logs: $LOG_DIR"

enriched_count=0
failed_count=0

# Iterate through each run folder (set +e to prevent early exit on error)
set +e
for run_folder in "$INPUT_RUNS_DIR"/R*/; do
  [ -d "$run_folder" ] || continue
  
  run_id=$(basename "$run_folder")
  library_file="$run_folder/${run_id}_sample_libraries.txt"
  input_qc_csv="$PROCESSED_SAMPLES_DIR/${run_id}-samples-qc-metrics.csv"
  output_qc_csv="$PROCESSED_SAMPLES_DIR/${run_id}-samples-qc-metrics-enriched.csv"
  log_file="$LOG_DIR/${run_id}-add-libraries.log"
  
  # Skip if library mapping file doesn't exist
  if [ ! -f "$library_file" ]; then
    echo "⚠ Library mapping not found for $run_id: $library_file"
    continue
  fi
  
  # Skip if input QC CSV doesn't exist
  if [ ! -f "$input_qc_csv" ]; then
    echo "⚠ Input QC metrics not found for $run_id: $input_qc_csv"
    continue
  fi
  
  echo "Processing $run_id..."
  if python "$SCRIPT_DIR/../parser/Samples_Quality/add_libraries_to_qc.py" \
    --input-csv "$input_qc_csv" \
    --output-csv "$output_qc_csv" \
    --library-file "$library_file" \
    --log-file "$log_file" > /dev/null 2>&1; then
    
    # Replace the original with the enriched version
    mv "$output_qc_csv" "$input_qc_csv"
    echo "✓ Enriched: $run_id"
    ((enriched_count++))
  else
    echo "⚠ Failed to enrich: $run_id (see $log_file)"
    ((failed_count++))
  fi
done
set -e

echo ""
echo "Library ID addition complete:"
echo "  ✓ Processed: $enriched_count runs"
if [ "$failed_count" -gt 0 ]; then
  echo "  ⚠ Failed: $failed_count runs"
  exit 1
fi
exit 0
