#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "$SCRIPT_DIR/../lib/common.sh"
load_env

section() {
  printf '\n== %s ==\n' "$1"
}

if [ ! -d demo ]; then
  echo "ERROR: demo/ folder not found. Run this command from the IlluQC repository root." >&2
  exit 1
fi

shopt -s nullglob
run_info_files=(demo/R*-sequencing-info.csv)
run_metric_files=(demo/R*-sequencing-metrics.csv)
sample_metadata_files=(demo/R*-samples-metadata.csv)
sample_metric_files=(demo/R*-samples-qc-metrics.csv)

for required_file in \
  demo/sequencing_instruments.csv \
  demo/sequencing_chemistry.csv \
  demo/library.csv; do
  if [ ! -f "$required_file" ]; then
    echo "ERROR: required demo file not found: $required_file" >&2
    exit 1
  fi
done

if [ "${#run_info_files[@]}" -eq 0 ] \
  || [ "${#run_info_files[@]}" -ne "${#run_metric_files[@]}" ] \
  || [ "${#run_info_files[@]}" -ne "${#sample_metadata_files[@]}" ] \
  || [ "${#run_info_files[@]}" -ne "${#sample_metric_files[@]}" ]; then
  echo "ERROR: demo run, run-metric, sample-metadata, and sample-metric file counts must match." >&2
  exit 1
fi

section "IlluQC demo configuration"
printf 'Project:                 %s\n' "$PROJECT_NAME"
printf 'IlluQC version:          %s\n' "${ILLUQC_VERSION:-0.1.0}"
printf 'Repository:              %s\n' "$(pwd -P)"
printf 'Demo source:             %s/demo\n' "$(pwd -P)"
printf 'Processed data:          %s\n' "$PROCESSED_DATA_DIR"
printf 'Run output:              %s/Runs_Data\n' "$PROCESSED_DATA_DIR"
printf 'Sample output:           %s/Samples_Data\n' "$PROCESSED_DATA_DIR"
printf 'Logs:                    %s\n' "$LOG_DIR"
printf 'PostgreSQL data:         %s\n' "$POSTGRES_DATA_DIR"
printf 'Database name:           %s\n' "$POSTGRES_DB"
printf 'Database user:           %s\n' "$POSTGRES_USER"
printf 'Dashboard URL:           http://localhost:%s\n' "${STREAMLIT_PORT:-8501}"
printf 'Demo runs:               %d\n' "${#run_info_files[@]}"
printf 'Run metric files:        %d\n' "${#run_metric_files[@]}"
printf 'Sample metadata files:   %d\n' "${#sample_metadata_files[@]}"
printf 'Sample metric files:     %d\n' "${#sample_metric_files[@]}"
printf 'Note: database passwords are never printed.\n'

section "1/6 Create external data directories"
bash "$SCRIPT_DIR/../runtime/setup_data_directories.sh"

section "2/6 Refresh processed demo files"
printf 'Clearing: %s/Runs_Data\n' "$PROCESSED_DATA_DIR"
printf 'Clearing: %s/Samples_Data\n' "$PROCESSED_DATA_DIR"
rm -rf "$PROCESSED_DATA_DIR/Runs_Data" "$PROCESSED_DATA_DIR/Samples_Data"
mkdir -p "$PROCESSED_DATA_DIR/Runs_Data" "$PROCESSED_DATA_DIR/Samples_Data"

cp -f demo/sequencing_instruments.csv "$PROCESSED_DATA_DIR/sequencing_instruments.csv"
cp -f demo/sequencing_chemistry.csv "$PROCESSED_DATA_DIR/sequencing_chemistry.csv"
# Keep both filenames: the lab loader consumes libraries.csv, while sample
# validation uses library.csv as its local catalogue.
cp -f demo/library.csv "$PROCESSED_DATA_DIR/library.csv"
cp -f demo/library.csv "$PROCESSED_DATA_DIR/libraries.csv"
cp -f "${run_info_files[@]}" "$PROCESSED_DATA_DIR/Runs_Data/"
cp -f "${run_metric_files[@]}" "$PROCESSED_DATA_DIR/Runs_Data/"
cp -f "${sample_metadata_files[@]}" "$PROCESSED_DATA_DIR/Samples_Data/"
cp -f "${sample_metric_files[@]}" "$PROCESSED_DATA_DIR/Samples_Data/"

printf 'Copied reference data to:\n'
printf '  %s/sequencing_instruments.csv\n' "$PROCESSED_DATA_DIR"
printf '  %s/sequencing_chemistry.csv\n' "$PROCESSED_DATA_DIR"
printf '  %s/library.csv\n' "$PROCESSED_DATA_DIR"
printf '  %s/libraries.csv\n' "$PROCESSED_DATA_DIR"
printf 'Copied %d run file pairs to %s/Runs_Data\n' \
  "${#run_info_files[@]}" "$PROCESSED_DATA_DIR"
printf 'Copied %d sample file pairs to %s/Samples_Data\n' \
  "${#sample_metadata_files[@]}" "$PROCESSED_DATA_DIR"

section "3/6 Start PostgreSQL"
compose up -d db
bash "$SCRIPT_DIR/../runtime/wait_for_database.sh"
printf 'PostgreSQL is ready: database=%s user=%s service=db\n' \
  "$POSTGRES_DB" "$POSTGRES_USER"

section "4/6 Load laboratory reference data"
bash "$SCRIPT_DIR/../lab/load_lab_data.sh"

section "5/6 Load run and sample data"
bash "$SCRIPT_DIR/../runs/load_runs.sh"
bash "$SCRIPT_DIR/../legacy/load_sample_data.sh"

section "6/6 Start dashboard and report"
compose up -d streamlit

printf '\nDatabase row counts after loading:\n'
compose exec -T db psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -P pager=off \
  -c "SELECT 'instruments' AS table_name, COUNT(*) AS rows FROM instruments
      UNION ALL SELECT 'sequencing_chemistry', COUNT(*) FROM sequencing_chemistry
      UNION ALL SELECT 'library', COUNT(*) FROM library
      UNION ALL SELECT 'sequencing_run', COUNT(*) FROM sequencing_run
      UNION ALL SELECT 'samples', COUNT(*) FROM samples
      UNION ALL SELECT 'sequencing_qc_metrics', COUNT(*) FROM sequencing_qc_metrics
      UNION ALL SELECT 'sample_qc_metrics', COUNT(*) FROM sample_qc_metrics
      ORDER BY table_name;"

section "Demo ready"
printf 'Dashboard:               http://localhost:%s\n' "${STREAMLIT_PORT:-8501}"
printf 'Loader logs:             %s/loader\n' "$LOG_DIR"
printf 'Parser logs:             %s/parser\n' "$LOG_DIR"
printf 'Application logs:        %s/app\n' "$LOG_DIR"
printf 'Container status command: ./illuqc status\n'
printf 'Log command:              ./illuqc logs\n'
