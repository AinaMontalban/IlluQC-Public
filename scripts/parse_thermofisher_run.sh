#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

JSON_FILE="${1:-}"
DESCRIPTION="${2:-}"
INSTRUMENT_MODEL="${3:-}"
require_arg "$JSON_FILE" "JSON_FILE"

if [ -n "$INSTRUMENT_MODEL" ]; then
  INSTRUMENT_MODEL="$(printf '%s' "$INSTRUMENT_MODEL" | tr '[:lower:]' '[:upper:]')"
  if [ "$INSTRUMENT_MODEL" != "S5" ] && [ "$INSTRUMENT_MODEL" != "GENEXUS" ]; then
    echo "ERROR: instrument model must be S5 or GENEXUS" >&2
    exit 2
  fi
fi

if [[ "$JSON_FILE" = /* ]]; then
  HOST_JSON="$JSON_FILE"
elif [ -f "$JSON_FILE" ]; then
  HOST_JSON="$(cd "$(dirname "$JSON_FILE")" && pwd -P)/$(basename "$JSON_FILE")"
else
  HOST_JSON="$THERMOFISHER_RAW_DATA_DIR/$JSON_FILE"
fi

if [ ! -f "$HOST_JSON" ]; then
  echo "ERROR: Thermo Fisher JSON file not found: $HOST_JSON" >&2
  exit 1
fi

RAW_ROOT="$(cd "$THERMOFISHER_RAW_DATA_DIR" && pwd -P)"
HOST_JSON="$(cd "$(dirname "$HOST_JSON")" && pwd -P)/$(basename "$HOST_JSON")"
case "$HOST_JSON" in
  "$RAW_ROOT"/*) RELATIVE_JSON="${HOST_JSON#"$RAW_ROOT"/}" ;;
  *)
    echo "ERROR: JSON file must be inside THERMOFISHER_RAW_DATA_DIR: $RAW_ROOT" >&2
    exit 1
    ;;
esac

mkdir -p "$PROCESSED_DATA_DIR/Runs_Data" "$LOG_DIR/parser"
LOG_NAME="$(basename "${JSON_FILE%.*}")_thermofisher_parser.log"

PARSER_ARGS=(
  /opt/ngsqc/parser/Thermofisher_Data/ThermoFisher_sequencing_data_parser.py
  --json-file "/data/raw/thermofisher/$RELATIVE_JSON"
  --output-dir /data/processed/Runs_Data
  --run-description "$DESCRIPTION"
  --log-file "/logs/parser/$LOG_NAME"
)
if [ -n "$INSTRUMENT_MODEL" ]; then
  PARSER_ARGS+=(--instrument-model "$INSTRUMENT_MODEL")
fi

# Detach the container from stdin. This is required when the wrapper is called
# from parse_thermofisher_all.sh, whose null-delimited file list also uses stdin.
compose run --rm -T --entrypoint python parser "${PARSER_ARGS[@]}" < /dev/null

echo "Thermo Fisher parser finished."
echo "Input: $HOST_JSON"
echo "Outputs: $PROCESSED_DATA_DIR/Runs_Data"
echo "Log: $LOG_DIR/parser/$LOG_NAME"
