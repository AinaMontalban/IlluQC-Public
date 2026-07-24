#!/usr/bin/env bash
set -euo pipefail

RUN_ID=$1
LIBRARY_ID=$2

RAW_DATA_DIR="/mnt/corebm/seq/raw_data"
INPUT_FILE="$RAW_DATA_DIR/$RUN_ID/run_samples_servolab.txt"
METRICS_FILE="$RAW_DATA_DIR/$RUN_ID/run_qc/multiqc_data/multiqc_general_stats.txt"

while IFS=$'\t' read -r SAMPLE_ID SEX PANEL_NUM PANEL_METHOD; do
    echo "Processing ${SAMPLE_ID}..."

    ./illuqc ingest-sample "$RUN_ID" "$SAMPLE_ID" \
        --sex "$SEX" \
        --library-id "$LIBRARY_ID" \
        --clinical-method "$PANEL_METHOD" \
        --sample-type "Blood" \
        --metrics-file "$METRICS_FILE" \
        --force < /dev/null

done < "$INPUT_FILE"