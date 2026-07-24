#!/usr/bin/env bash
set -x
RUN_ID=$1
LIBRARY_ID=$2
ANALYSIS_ID=$3

echo "Ingesting samples for run: $RUN_ID, library: $LIBRARY_ID, analysis: $ANALYSIS_ID"

if [ -z "$RUN_ID" ] || [ -z "$LIBRARY_ID" ] || [ -z "$ANALYSIS_ID" ]; then
    echo "Usage: $0 <RUN_ID> <LIBRARY_ID> <ANALYSIS_ID>"
    exit 1
fi

RAW_DATA_DIR="/mnt/corebm/seq/raw_data"
RESULTS_DIR="/mnt/corebm/seq/results/by_sample"
INPUT_FILE="$RAW_DATA_DIR/$RUN_ID/run_samples_servolab.txt"
MULTIQC_METRICS_FILE="$RAW_DATA_DIR/$RUN_ID/run_qc/multiqc_data/multiqc_general_stats.txt"

while IFS=$'\t' read -r SAMPLE_ID SEX PANEL_NUM PANEL_METHOD; do
    echo "Processing ${SAMPLE_ID}..."
    COVERAGE_METRICS_FILE="$RESULTS_DIR/${SAMPLE_ID}/${SAMPLE_ID}_${ANALYSIS_ID}/coverage/${SAMPLE_ID}_summary_coverage_full.csv"
    #COVERAGE_METRICS_FILE="$RESULTS_DIR/${SAMPLE_ID}/${ANALYSIS_ID}/coverage/${SAMPLE_ID}_summary_coverage_full.csv"
    ./illuqc ingest-sample "$RUN_ID" "$SAMPLE_ID" \
        --sex "$SEX" \
        --library-id "$LIBRARY_ID" \
        --clinical-method "$PANEL_METHOD" \
        --sample-type "Blood" \
        --metrics-file "$MULTIQC_METRICS_FILE" \
        --metrics-file "$COVERAGE_METRICS_FILE" \
        --force < /dev/null
done < "$INPUT_FILE"