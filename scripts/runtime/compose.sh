#!/usr/bin/env bash
set -euo pipefail

if docker compose version >/dev/null 2>&1; then
  exec docker compose "$@"
fi

cat >&2 <<'MSG'
ERROR: Docker Compose is not available.

Install Docker Compose v2 and verify it with:
  docker compose version

MSG
exit 127
