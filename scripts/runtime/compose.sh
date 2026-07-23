#!/usr/bin/env bash
set -euo pipefail

# Use ILLUQC_COMPOSE_MODE=v2 or ILLUQC_COMPOSE_MODE=legacy to force a specific
# implementation. By default, prefer the Docker Compose v2 CLI plugin and fall
# back to the standalone docker-compose v1 executable.
mode="${ILLUQC_COMPOSE_MODE:-auto}"

case "$mode" in
  auto)
    if docker compose version >/dev/null 2>&1; then
      exec docker compose "$@"
    elif command -v docker-compose >/dev/null 2>&1; then
      exec docker-compose "$@"
    fi
    ;;
  v2)
    if docker compose version >/dev/null 2>&1; then
      exec docker compose "$@"
    fi
    echo "ERROR: Docker Compose v2 ('docker compose') is not available." >&2
    exit 127
    ;;
  legacy)
    if command -v docker-compose >/dev/null 2>&1; then
      exec docker-compose "$@"
    fi
    echo "ERROR: legacy Docker Compose ('docker-compose') is not available." >&2
    exit 127
    ;;
  *)
    echo "ERROR: ILLUQC_COMPOSE_MODE must be auto, v2, or legacy (got: $mode)." >&2
    exit 2
    ;;
esac

cat >&2 <<'MSG'
ERROR: Docker Compose is not available.

Install Docker Compose v2 and verify it with:
  docker compose version

Legacy docker-compose is supported as a fallback only.
MSG
exit 127
