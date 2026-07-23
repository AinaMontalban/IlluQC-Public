#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

RUN_ID="${1:-}"
SAMPLE_ID="${2:-}"
require_arg "$RUN_ID" "RUN_ID"
RUN_DIR="$ILLUMINA_RAW_DATA_DIR/$RUN_ID"

if [ -f "$RUN_DIR/sample_metadata.tsv" ]; then
  METADATA_FILE="$RUN_DIR/sample_metadata.tsv"
else
  METADATA_FILE="$RUN_DIR/run_samples_servolab.txt"
fi
if [ -f "$RUN_DIR/sample_libraries.tsv" ]; then
  LIBRARY_FILE="$RUN_DIR/sample_libraries.tsv"
else
  LIBRARY_FILE="$RUN_DIR/${RUN_ID}_sample_libraries.txt"
fi

ARGS=(
  --run-id "$RUN_ID"
  --metadata "$METADATA_FILE"
  --multiqc "$RUN_DIR/multiqc_general_stats.txt"
  --libraries "$LIBRARY_FILE"
  --known-libraries "$PROCESSED_DATA_DIR/library.csv"
)
[ -n "$SAMPLE_ID" ] && ARGS+=(--sample-id "$SAMPLE_ID")
python3 "$SCRIPT_DIR/validate_sample_inputs.py" "${ARGS[@]}"
