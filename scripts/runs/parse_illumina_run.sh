#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

RUN_ID="${1:-}"
DESCRIPTION="${2:-}"
require_arg "$RUN_ID" "RUN_ID"

HOST_RUN_DIR="$ILLUMINA_RAW_DATA_DIR/$RUN_ID"
if [ ! -d "$HOST_RUN_DIR" ]; then
  echo "ERROR: run folder not found: $HOST_RUN_DIR" >&2
  exit 1
fi

mkdir -p "$PROCESSED_DATA_DIR/Runs_Data" "$LOG_DIR/parser"

compose run --rm parser \
  --run-folder "/data/raw/illumina/$RUN_ID/run_qc/illumina" \
  --output-dir "/data/processed/Runs_Data" \
  --run-description "$DESCRIPTION" \
  --log-file "/logs/parser/${RUN_ID}_parser.log"

echo "Parser finished for run: $RUN_ID"
echo "Outputs: $PROCESSED_DATA_DIR/Runs_Data"
echo "Log: $LOG_DIR/parser/${RUN_ID}_parser.log"
