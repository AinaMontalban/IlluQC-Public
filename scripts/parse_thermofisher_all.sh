#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

DESCRIPTION="${1:-}"
INSTRUMENT_MODEL="${2:-AUTO}"
INSTRUMENT_MODEL="$(printf '%s' "$INSTRUMENT_MODEL" | tr '[:lower:]' '[:upper:]')"

if [ "$INSTRUMENT_MODEL" != "AUTO" ] \
  && [ "$INSTRUMENT_MODEL" != "S5" ] \
  && [ "$INSTRUMENT_MODEL" != "GENEXUS" ]; then
  echo "ERROR: MODEL must be AUTO, S5, or GENEXUS" >&2
  exit 2
fi

if [ ! -d "$THERMOFISHER_RAW_DATA_DIR" ]; then
  echo "ERROR: Thermo Fisher raw data directory not found: $THERMOFISHER_RAW_DATA_DIR" >&2
  exit 1
fi

found=0
parsed=0
failed=0

while IFS= read -r -d '' json_file; do
  found=$((found + 1))
  echo "Parsing Thermo Fisher export ($INSTRUMENT_MODEL): $json_file"
  model_arg=""
  [ "$INSTRUMENT_MODEL" != "AUTO" ] && model_arg="$INSTRUMENT_MODEL"
  if bash "$SCRIPT_DIR/parse_thermofisher_run.sh" \
    "$json_file" "$DESCRIPTION" "$model_arg"; then
    parsed=$((parsed + 1))
  else
    echo "WARNING: failed to parse: $json_file" >&2
    failed=$((failed + 1))
  fi
done < <(
  case "$INSTRUMENT_MODEL" in
    S5)
      find "$THERMOFISHER_RAW_DATA_DIR" -type f -name 'serialized_*.json' -print0
      ;;
    GENEXUS)
      find "$THERMOFISHER_RAW_DATA_DIR" -type f \
        \( -name 'Plan_*.json' -o -name 'plan_*.json' \) -print0
      ;;
    AUTO)
      find "$THERMOFISHER_RAW_DATA_DIR" -type f \
        \( -name 'serialized_*.json' -o -name 'Plan_*.json' -o -name 'plan_*.json' \) \
        -print0
      ;;
  esac
)

if [ "$found" -eq 0 ]; then
  echo "ERROR: no Thermo Fisher JSON exports found in $THERMOFISHER_RAW_DATA_DIR" >&2
  echo "No files match MODEL=$INSTRUMENT_MODEL." >&2
  exit 1
fi

echo
echo "Thermo Fisher batch parsing finished (MODEL=$INSTRUMENT_MODEL):"
echo "$parsed parsed, $failed failed, $found total."
echo "Outputs: $PROCESSED_DATA_DIR/Runs_Data"

[ "$failed" -eq 0 ]
