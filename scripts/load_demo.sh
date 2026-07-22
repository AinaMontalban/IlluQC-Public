#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

if [ ! -d demo ]; then
  echo "ERROR: demo/ folder not found. Create synthetic demo CSVs first." >&2
  exit 1
fi

bash "$SCRIPT_DIR/setup_data_dirs.sh"

# Clear processed directories and create fresh for demo
rm -rf "$PROCESSED_DATA_DIR/Runs_Data" "$PROCESSED_DATA_DIR/Samples_Data"
mkdir -p "$PROCESSED_DATA_DIR/Runs_Data" "$PROCESSED_DATA_DIR/Samples_Data"

# Copy known demo files if they exist. These should be synthetic only.
cp -f demo/sequencing_instruments.csv "$PROCESSED_DATA_DIR/" 2>/dev/null || true
cp -f demo/sequencing_chemistry.csv "$PROCESSED_DATA_DIR/" 2>/dev/null || true
cp -f demo/library.csv "$PROCESSED_DATA_DIR/" 2>/dev/null || true
cp -f demo/RUN_*-sequencing-info.csv "$PROCESSED_DATA_DIR/Runs_Data/" 2>/dev/null || true
cp -f demo/RUN_*-sequencing-metrics.csv "$PROCESSED_DATA_DIR/Runs_Data/" 2>/dev/null || true
cp -f demo/RUN_*-samples-metadata.csv "$PROCESSED_DATA_DIR/Samples_Data/" 2>/dev/null || true
cp -f demo/RUN_*-samples-qc-metrics.csv "$PROCESSED_DATA_DIR/Samples_Data/" 2>/dev/null || true

docker compose up -d db
bash "$SCRIPT_DIR/wait_for_db.sh"
bash "$SCRIPT_DIR/load_reference_tables.sh"
bash "$SCRIPT_DIR/load_all_runs.sh"
docker compose up -d streamlit

echo "Demo loaded. Open http://localhost:${STREAMLIT_PORT:-8501}"
