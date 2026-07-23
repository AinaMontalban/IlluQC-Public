# Configuration reference

IlluQC loads `.env` through both Make and `scripts/lib/common.sh`. Docker Compose
also reads `.env` for interpolation. Keep values simple shell assignments and
quote values containing spaces when sourcing them from shell scripts.

## General and container settings

| Variable | Default/example | Purpose |
|---|---|---|
| `PROJECT_NAME` | `illuqc` | Prefix for locally built image names. |
| `ILLUQC_VERSION` | `0.1.0` | Image tag used by Compose. |
| `ILLUQC_COMPOSE_MODE` | `auto` | Select `auto`, `v2`, or `legacy` Compose invocation. |
| `LOCAL_UID` | `10001` | Runtime UID for parser, loader, and dashboard. |
| `LOCAL_GID` | `10001` | Runtime GID for parser, loader, and dashboard. |
| `NGS_DATA_ROOT` | `../NGS_Data` | Fallback root used by shell helpers. |
| `STREAMLIT_PORT` | `8501` | Host port mapped to Streamlit. |
| `PARSER_LOG_LEVEL` | `INFO` | Parser log verbosity where supported. |

On Linux, host ownership is usually best preserved with:

```dotenv
LOCAL_UID=1000
LOCAL_GID=1000
```

Use the actual output of `id -u` and `id -g`, not these example numbers.

## External paths

| Variable | Container use | Access |
|---|---|---|
| `ILLUMINA_RAW_DATA_DIR` | `/data/raw/illumina` | parser read-only |
| `THERMOFISHER_RAW_DATA_DIR` | `/data/raw/thermofisher` | parser read-only |
| `PROCESSED_DATA_DIR` | `/data/processed` | parser write, loader read-only |
| `LOG_DIR` | `/logs` | parser/loader/dashboard write |
| `BACKUP_DIR` | host-side backup destination | host scripts write |
| `POSTGRES_DATA_DIR` | `/var/lib/postgresql` | PostgreSQL write |
| `CONFIG_DIR` | `/config` | dashboard read-only |

Use absolute paths in production to make service behavior independent of the
repository's location. Ensure `POSTGRES_DATA_DIR` is on a filesystem suitable
for PostgreSQL, not an object-store mount or intermittently connected share.

## PostgreSQL

| Variable | Required | Purpose |
|---|---|---|
| `POSTGRES_USER` | no | Database owner; defaults to `illuqc`. |
| `POSTGRES_PASSWORD` | yes | Database password; no insecure fallback exists. |
| `POSTGRES_DB` | no | Database name; defaults to `illuqcdb`. |
| `POSTGRES_HOST` | native tools | Hostname for non-Compose access. |
| `POSTGRES_PORT` | no | Port; defaults to `5432`. |

Compose passes the same values to the loader and maps them to `DB_*` variables
for Streamlit. Changing user, password, or database after initial PostgreSQL
initialization does not rewrite existing roles or databases.

## Compose-time validation

All IlluQC scripts and Make targets call `scripts/runtime/compose.sh`. In `auto` mode
the wrapper prefers Docker Compose v2 (`docker compose`) and uses the legacy
`docker-compose` executable only when the v2 plugin is unavailable. Force one
implementation when diagnosing a host installation:

```bash
ILLUQC_COMPOSE_MODE=v2 ./scripts/runtime/compose.sh version
ILLUQC_COMPOSE_MODE=legacy ./scripts/runtime/compose.sh version
```

Required variables use Compose's `:?` syntax. Check interpolation without
starting containers:

```bash
./scripts/runtime/compose.sh config --quiet
```

## Example production-oriented file

```dotenv
PROJECT_NAME=illuqc
ILLUQC_VERSION=0.1.0
ILLUQC_COMPOSE_MODE=auto
LOCAL_UID=1000
LOCAL_GID=1000

ILLUMINA_RAW_DATA_DIR=/srv/illuqc/raw/illumina
THERMOFISHER_RAW_DATA_DIR=/srv/illuqc/raw/thermofisher
PROCESSED_DATA_DIR=/srv/illuqc/processed
LOG_DIR=/var/log/illuqc
BACKUP_DIR=/srv/illuqc/backups
POSTGRES_DATA_DIR=/srv/illuqc/postgres
CONFIG_DIR=/etc/illuqc

POSTGRES_USER=illuqc
POSTGRES_PASSWORD=replace-with-a-secret-generated-for-this-deployment
POSTGRES_DB=illuqcdb
POSTGRES_HOST=db
POSTGRES_PORT=5432
STREAMLIT_PORT=8501
PARSER_LOG_LEVEL=INFO
```
