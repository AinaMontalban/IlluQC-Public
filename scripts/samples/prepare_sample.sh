#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

RUN_ID="${1:-}"
SAMPLE_ID="${2:-}"
require_arg "$RUN_ID" "RUN_ID"
require_arg "$SAMPLE_ID" "SAMPLE_ID"
shift 2

python3 "$SCRIPT_DIR/prepare_sample.py" \
  "$RUN_ID" "$SAMPLE_ID" \
  --processed-data-dir "$PROCESSED_DATA_DIR" \
  --known-libraries "$PROCESSED_DATA_DIR/library.csv" \
  --config "$SCRIPT_DIR/../../parser/MultiQC/multiqc_parser_config.json" \
  "$@"
