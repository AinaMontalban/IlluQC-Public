#!/usr/bin/env bash
set -euo pipefail

COMMON_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

load_env() {
  if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
  fi

  export PROJECT_NAME="${PROJECT_NAME:-illuqc}"
  export NGS_DATA_ROOT="${NGS_DATA_ROOT:-../NGS_Data}"
  # RAW_DATA_DIR remains a fallback for older .env files.
  export ILLUMINA_RAW_DATA_DIR="${ILLUMINA_RAW_DATA_DIR:-${RAW_DATA_DIR:-$NGS_DATA_ROOT/raw_data/illumina}}"
  export THERMOFISHER_RAW_DATA_DIR="${THERMOFISHER_RAW_DATA_DIR:-$NGS_DATA_ROOT/raw_data/thermofisher}"
  export PROCESSED_DATA_DIR="${PROCESSED_DATA_DIR:-$NGS_DATA_ROOT/processed}"
  export LOG_DIR="${LOG_DIR:-$NGS_DATA_ROOT/logs}"
  export BACKUP_DIR="${BACKUP_DIR:-$NGS_DATA_ROOT/backups}"
  export POSTGRES_DATA_DIR="${POSTGRES_DATA_DIR:-$NGS_DATA_ROOT/postgres_data}"
  export CONFIG_DIR="${CONFIG_DIR:-$NGS_DATA_ROOT/config}"
  export POSTGRES_USER="${POSTGRES_USER:-illuqc}"
  if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "ERROR: POSTGRES_PASSWORD must be set in .env" >&2
    exit 1
  fi
  if [ "$POSTGRES_PASSWORD" = "replace-with-a-long-random-password" ] \
    || [ "$POSTGRES_PASSWORD" = "replace-this-password" ]; then
    echo "ERROR: replace the example POSTGRES_PASSWORD before running IlluQC" >&2
    exit 1
  fi
  if [ "${#POSTGRES_PASSWORD}" -lt 16 ]; then
    echo "WARNING: POSTGRES_PASSWORD should contain at least 16 characters" >&2
  fi
  export POSTGRES_DB="${POSTGRES_DB:-illuqcdb}"
  export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
}

compose() {
  bash "$COMMON_SCRIPT_DIR/../runtime/compose.sh" "$@"
}

require_arg() {
  local value="$1"
  local name="$2"
  if [ -z "$value" ]; then
    echo "ERROR: missing required argument: $name" >&2
    exit 1
  fi
}
