#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_common.sh
source "$SCRIPT_DIR/_common.sh"
load_env

mkdir -p "$ILLUMINA_RAW_DATA_DIR"
mkdir -p "$ILLUMINA_RAW_DATA_DIR/reference_tables"
mkdir -p "$THERMOFISHER_RAW_DATA_DIR"
mkdir -p "$THERMOFISHER_RAW_DATA_DIR/reference_tables"
mkdir -p "$PROCESSED_DATA_DIR/Runs_Data"
mkdir -p "$PROCESSED_DATA_DIR/Samples_Data"
mkdir -p "$LOG_DIR/parser"
mkdir -p "$LOG_DIR/loader"
mkdir -p "$LOG_DIR/app"
mkdir -p "$BACKUP_DIR"
mkdir -p "$POSTGRES_DATA_DIR"
mkdir -p "$CONFIG_DIR"

cat <<MSG
IlluQC external data directories created:
  ILLUMINA_RAW_DATA_DIR=$ILLUMINA_RAW_DATA_DIR
  THERMOFISHER_RAW_DATA_DIR=$THERMOFISHER_RAW_DATA_DIR
  PROCESSED_DATA_DIR=$PROCESSED_DATA_DIR
  LOG_DIR=$LOG_DIR
  BACKUP_DIR=$BACKUP_DIR
  POSTGRES_DATA_DIR=$POSTGRES_DATA_DIR
  CONFIG_DIR=$CONFIG_DIR
MSG
