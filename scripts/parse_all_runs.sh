#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

RUNS_DIR="$ILLUMINA_RAW_DATA_DIR"
if [ ! -d "$RUNS_DIR" ]; then
  echo "ERROR: runs directory not found: $RUNS_DIR" >&2
  exit 1
fi

# Check for optional manifest file
MANIFEST_FILE="$ILLUMINA_RAW_DATA_DIR/runs_manifest.csv"
declare -A run_descriptions

if [ -f "$MANIFEST_FILE" ]; then
  echo "Loading run descriptions from manifest: $MANIFEST_FILE"
  # Skip header line and read RunID,RunDescription pairs
  while IFS=$'\t' read -r run_id description; do
    # Skip header and empty lines
    [ "$run_id" = "RunID" ] && continue
    [ -z "$run_id" ] && continue
    # Trim whitespace
    run_id=$(echo "$run_id" | xargs)
    description=$(echo "$description" | xargs)
    run_descriptions["$run_id"]="$description"
  done < "$MANIFEST_FILE"
  echo "Loaded descriptions for ${#run_descriptions[@]} run(s)"
fi

# print the run descriptions for debugging
if [ "${#run_descriptions[@]}" -gt 0 ]; then
  echo "Run descriptions loaded:"
  for run_id in "${!run_descriptions[@]}"; do
    echo "  $run_id: ${run_descriptions[$run_id]}"
  done
fi

found=0
failed=0
for run_dir in "$RUNS_DIR"/*/; do
  [ -d "$run_dir" ] || continue
  found=1
  run_id="$(basename "$run_dir")"
  # Look up description from manifest, default to empty string
  description="${run_descriptions[$run_id]:-}"
  echo "Parsing run: $run_id (Description: ${description:-none provided})"
  
  # Parse run and skip if it fails
  if bash "$SCRIPT_DIR/parse_run.sh" "$run_id" "$description"; then
    echo "✓ Successfully parsed: $run_id"
  else
    echo "⚠ Failed to parse: $run_id (skipping)"
    ((failed++))
  fi
done

if [ "$found" -eq 0 ]; then
  echo "No run folders found in $RUNS_DIR"
  exit 1
fi

if [ "$failed" -gt 0 ]; then
  echo "⚠ Parsing completed with $failed error(s) - skipped missing/invalid runs"
  exit 0
else
  echo "✓ All runs parsed successfully"
  exit 0
fi
