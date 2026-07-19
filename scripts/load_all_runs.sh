#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

RUNS_PROCESSED_DIR="$PROCESSED_DATA_DIR/Runs_Data"
if [ ! -d "$RUNS_PROCESSED_DIR" ]; then
  echo "ERROR: processed runs directory not found: $RUNS_PROCESSED_DIR" >&2
  exit 1
fi

found=0
for info_csv in "$RUNS_PROCESSED_DIR"/*-sequencing-info.csv; do
  [ -f "$info_csv" ] || continue
  found=1
  base="$(basename "$info_csv")"
  run_id="${base%-sequencing-info.csv}"
  echo "Loading run: $run_id"
  bash "$SCRIPT_DIR/load_run.sh" "$run_id"
done

if [ "$found" -eq 0 ]; then
  echo "No processed sequencing-info CSV files found in $RUNS_PROCESSED_DIR"
fi
