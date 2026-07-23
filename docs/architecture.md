# Architecture

## Overview

IlluQC separates executable code from laboratory data. Code is built into three
application images; PostgreSQL uses an upstream image. All durable or
site-specific state is mounted from the host.

```text
Raw run folders ──> parser ──> normalized CSV files ──> loader ──> PostgreSQL
                         │                              │              │
                         └──────── parser logs ─────────┘              │
                                                                        v
                                                              Streamlit dashboard
```

## Components

### PostgreSQL (`db`)

PostgreSQL stores dimensions, run metadata, metric definitions, and metric
observations. On first initialization it executes
`init-db/01_schema_ddl.sql` followed by `init-db/02_schema_seed.sql`.

Initialization scripts run only when `POSTGRES_DATA_DIR` is empty. Editing SQL
does not migrate an existing database.

### Parser (`parser`)

The parser image contains:

- the Illumina InterOp parser;
- the Thermo Fisher S5/Genexus JSON parser;
- the MultiQC general-statistics parser;
- sample metadata normalization;
- sample/library enrichment utilities.

Raw Illumina and Thermo Fisher directories are distinct read-only mounts.
Normalized files are written to `/data/processed`; parser logs go to `/logs`.

### Loader (`loader`)

The loader validates a CSV against `db/required_fields.json` and the live table
schema. It inserts compatible columns in batches with `ON CONFLICT DO NOTHING`.
This makes repeated loads non-destructive but also means a repeat load does not
update an existing row.

### Dashboard (`streamlit`)

The Streamlit app reads PostgreSQL through SQLAlchemy and psycopg2. Database
credentials come from `DB_*` environment variables injected by Compose. Query
functions live in `app/queries.py`; page modules render their results.

Detailed errors are logged inside the container. Users receive sanitized error
messages to avoid exposing SQL, paths, or credentials.

## Container boundaries

| Service | Reads | Writes | Long-running |
|---|---|---|---|
| `db` | initialization SQL, PostgreSQL data | PostgreSQL data | yes |
| `parser` | raw data, parser code | processed CSVs, parser logs | no |
| `loader` | processed CSVs, loader code | PostgreSQL, loader logs | no |
| `streamlit` | application code, config | application logs | yes |

Parser and loader services use the Compose `tools` profile and are normally
created for individual `compose run --rm` operations.

## Data-model strategy

Run and sample metrics use long format: metric identity is stored in
`qc_metric_definitions`, while values are stored in metric fact tables. New
metrics generally require seed/config changes rather than new database columns.

## Idempotency and ordering

Recommended load order:

1. seed data created during database initialization;
2. instruments, chemistry, and libraries;
3. run metadata;
4. run metrics;
5. sample metadata;
6. library-enriched sample metrics.

Foreign keys enforce much of this order. Duplicate primary keys are skipped,
not updated.

## Operational scripts

The `scripts/` directory is grouped by responsibility: `runtime/` for Compose
v2 and setup, `runs/` for run parsing/loading, `samples/` for sample workflows,
`lab/` for reference data, `database/` for backup/restore/demo, `lib/` for
shared shell helpers, and `tools/` for standalone utilities. Operators should
normally use the top-level `illuqc` command rather than invoke these scripts
directly.
