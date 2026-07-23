#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

ROOT="$PROCESSED_DATA_DIR/Samples_Data"
found=0
failed=0
for ready_dir in "$ROOT"/*/load-ready; do
  [ -d "$ready_dir" ] || continue
  found=$((found + 1))
  run_id="$(basename "$(dirname "$ready_dir")")"
  echo "Loading samples for $run_id"
  if ! bash "$SCRIPT_DIR/load_run_samples.sh" "$run_id"; then
    failed=$((failed + 1))
  fi
done

echo "Sample loading summary: $((found - failed)) succeeded, $failed failed, $found total."
[ "$found" -gt 0 ] && [ "$failed" -eq 0 ]
