#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

found=0
failed=0
for run_dir in "$ILLUMINA_RAW_DATA_DIR"/*/; do
  [ -d "$run_dir" ] || continue
  found=$((found + 1))
  run_id="$(basename "$run_dir")"
  echo "Preparing samples for $run_id"
  if ! bash "$SCRIPT_DIR/prepare_run_samples.sh" "$run_id" "" "${1:-}"; then
    failed=$((failed + 1))
  fi
done

echo "Sample preparation summary: $((found - failed)) succeeded, $failed failed, $found total."
[ "$found" -gt 0 ] && [ "$failed" -eq 0 ]
