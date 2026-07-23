#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

RUN_ID="${1:-}"
SAMPLE_ID="${2:-}"
FORCE="${3:-}"
require_arg "$RUN_ID" "RUN_ID"

if [ -n "$SAMPLE_ID" ] && [[ ! "$SAMPLE_ID" =~ ^[A-Za-z0-9._-]+$ ]]; then
  echo "ERROR: SAMPLE_ID may contain only letters, numbers, dot, underscore, and hyphen." >&2
  exit 2
fi
if [ -n "$FORCE" ] && [ "$FORCE" != "--force" ]; then
  echo "ERROR: the only supported option is --force" >&2
  exit 2
fi

RUN_DIR="$ILLUMINA_RAW_DATA_DIR/$RUN_ID"
if [ ! -d "$RUN_DIR" ]; then
  echo "ERROR: run folder not found: $RUN_DIR" >&2
  exit 1
fi

if [ -f "$RUN_DIR/sample_metadata.tsv" ]; then
  METADATA_FILE="$RUN_DIR/sample_metadata.tsv"
elif [ -f "$RUN_DIR/run_samples_servolab.txt" ]; then
  METADATA_FILE="$RUN_DIR/run_samples_servolab.txt"
else
  echo "ERROR: sample metadata not found. Expected sample_metadata.tsv or run_samples_servolab.txt in $RUN_DIR" >&2
  exit 1
fi

MULTIQC_FILE="$RUN_DIR/multiqc_general_stats.txt"
if [ ! -f "$MULTIQC_FILE" ]; then
  echo "ERROR: MultiQC statistics not found: $MULTIQC_FILE" >&2
  exit 1
fi

if [ -f "$RUN_DIR/sample_libraries.tsv" ]; then
  LIBRARY_FILE="$RUN_DIR/sample_libraries.tsv"
elif [ -f "$RUN_DIR/${RUN_ID}_sample_libraries.txt" ]; then
  LIBRARY_FILE="$RUN_DIR/${RUN_ID}_sample_libraries.txt"
else
  echo "ERROR: library mapping not found. Expected sample_libraries.tsv or ${RUN_ID}_sample_libraries.txt in $RUN_DIR" >&2
  exit 1
fi

VALIDATE_ARGS=(
  --run-id "$RUN_ID"
  --metadata "$METADATA_FILE"
  --multiqc "$MULTIQC_FILE"
  --libraries "$LIBRARY_FILE"
  --known-libraries "$PROCESSED_DATA_DIR/library.csv"
)
[ -n "$SAMPLE_ID" ] && VALIDATE_ARGS+=(--sample-id "$SAMPLE_ID")
python3 "$SCRIPT_DIR/validate_sample_inputs.py" "${VALIDATE_ARGS[@]}"

if [ -n "$SAMPLE_ID" ]; then
  SCOPE_DIR="$PROCESSED_DATA_DIR/Samples_Data/$RUN_ID/samples/$SAMPLE_ID"
  OUTPUT_STEM="${RUN_ID}-${SAMPLE_ID}"
else
  SCOPE_DIR="$PROCESSED_DATA_DIR/Samples_Data/$RUN_ID"
  OUTPUT_STEM="$RUN_ID"
fi
INTERMEDIATE_DIR="$SCOPE_DIR/intermediate"
READY_DIR="$SCOPE_DIR/load-ready"
STAGING_DIR="$SCOPE_DIR/.load-ready-staging-$$"
METADATA_OUTPUT="$STAGING_DIR/samples.csv"
QC_OUTPUT="$STAGING_DIR/sample-qc-metrics.csv"

if { [ -e "$READY_DIR/samples.csv" ] || [ -e "$READY_DIR/sample-qc-metrics.csv" ]; } \
  && [ "$FORCE" != "--force" ]; then
  echo "ERROR: load-ready output already exists under $READY_DIR" >&2
  echo "Re-run with --force only after reviewing the existing files." >&2
  exit 1
fi
rm -rf "$STAGING_DIR"
mkdir -p "$INTERMEDIATE_DIR" "$STAGING_DIR" "$LOG_DIR/parser"
trap 'rm -rf "$STAGING_DIR"' EXIT

CONTAINER_SCOPE="/data/processed/Samples_Data/$RUN_ID"
if [ -n "$SAMPLE_ID" ]; then
  CONTAINER_SCOPE="$CONTAINER_SCOPE/samples/$SAMPLE_ID"
fi
CONTAINER_STAGING="$CONTAINER_SCOPE/$(basename "$STAGING_DIR")"

METADATA_ARGS=(
  /opt/illuqc/parser/Sample_Metadata/parse_sample_metadata.py
  --input-file "/data/raw/illumina/$RUN_ID/$(basename "$METADATA_FILE")"
  --output-file "$CONTAINER_STAGING/samples.csv"
  --log-file "/logs/parser/${OUTPUT_STEM}-metadata.log"
)
[ -n "$SAMPLE_ID" ] && METADATA_ARGS+=(--sample-id "$SAMPLE_ID")
compose run --rm --entrypoint python parser "${METADATA_ARGS[@]}"

MULTIQC_ARGS=(
  /opt/illuqc/parser/MultiQC/multiqc_data_parser.py
  "/data/raw/illumina/$RUN_ID/multiqc_general_stats.txt"
  --run-id "$RUN_ID"
  --format csv
  --output-dir "$CONTAINER_SCOPE/intermediate"
)
[ -n "$SAMPLE_ID" ] && MULTIQC_ARGS+=(--sample-id "$SAMPLE_ID")
compose run --rm --entrypoint python parser "${MULTIQC_ARGS[@]}"

compose run --rm --entrypoint python parser \
  /opt/illuqc/parser/Samples_Quality/add_libraries_to_qc.py \
  --input-csv "$CONTAINER_SCOPE/intermediate/${OUTPUT_STEM}-samples-qc-metrics.csv" \
  --output-csv "$CONTAINER_STAGING/sample-qc-metrics.csv" \
  --library-file "/data/raw/illumina/$RUN_ID/$(basename "$LIBRARY_FILE")" \
  --log-file "/logs/parser/${OUTPUT_STEM}-library-enrichment.log"

python3 - "$METADATA_OUTPUT" "$QC_OUTPUT" <<'PY'
import csv
import sys
from pathlib import Path

metadata_path, qc_path = map(Path, sys.argv[1:])
expected = {
    metadata_path: {"sample_id", "sex"},
    qc_path: {"sample_id", "library_id", "run_id", "metric_id", "value_number"},
}
for path, required in expected.items():
    if not path.is_file():
        raise SystemExit(f"ERROR: expected output not created: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        rows = list(reader)
    if missing:
        raise SystemExit(f"ERROR: {path} missing columns: {sorted(missing)}")
    if not rows:
        raise SystemExit(f"ERROR: {path} contains no data rows")
print(f"Load-ready metadata rows: {sum(1 for _ in csv.DictReader(metadata_path.open()))}")
print(f"Load-ready QC rows: {sum(1 for _ in csv.DictReader(qc_path.open()))}")
PY

if [ -d "$READY_DIR" ]; then
  rm -rf "$READY_DIR"
fi
mv "$STAGING_DIR" "$READY_DIR"
trap - EXIT

cat > "$SCOPE_DIR/preparation-summary.txt" <<SUMMARY
Run: $RUN_ID
Scope: ${SAMPLE_ID:-all samples}
Metadata source: $METADATA_FILE
MultiQC source: $MULTIQC_FILE
Library source: $LIBRARY_FILE
Prepared at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Load-ready directory: $READY_DIR
SUMMARY

echo "Sample preparation completed."
echo "Run: $RUN_ID"
echo "Scope: ${SAMPLE_ID:-all samples}"
echo "Load-ready directory: $READY_DIR"
