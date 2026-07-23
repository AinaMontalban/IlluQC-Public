# Operations runbook

## Routine commands

| Command | Effect |
|---|---|
| `illuqc start` | Build and start services. |
| `illuqc dashboard` | Build/start Streamlit and dependencies. |
| `illuqc stop` | Stop services; host-mounted database data remains. |
| `illuqc logs [SERVICE]` | Follow Compose service logs. |
| `illuqc db-shell` | Open `psql` in the database container. |
| `illuqc backup` | Create a compressed logical PostgreSQL backup. |
| `illuqc restore BACKUP` | Drop, recreate, and restore the configured database. |
| `illuqc audit` | Scan pinned Python dependencies with `pip-audit`. |

## Health checks

```bash
./scripts/runtime/compose.sh ps
./scripts/runtime/compose.sh exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
curl --fail http://localhost:${STREAMLIT_PORT:-8501}/_stcore/health
```

The wrapper `scripts/runtime/wait_for_database.sh` retries database readiness 30 times with a
two-second delay by default. Override `MAX_ATTEMPTS` and `SLEEP_SECONDS` when
slow storage requires a longer initialization window.

## Logs

- Compose logs: `./scripts/runtime/compose.sh logs SERVICE`.
- Parser logs: `LOG_DIR/parser/`.
- Loader logs: `LOG_DIR/loader/`.
- Streamlit process output: Compose logs for `streamlit`.

Retain logs according to institutional policy. Logs can contain run and sample
identifiers even when credentials are sanitized.

## Backup

```bash
illuqc backup
```

The script uses `pg_dump`, compresses the SQL stream, and names it
`DATABASE-YYYYMMDD_HHMMSS.sql.gz` under `BACKUP_DIR`.

A backup is not proven until restored and checked. Periodically restore into an
isolated database and verify schema metadata, row counts, and representative
dashboard queries. Copy backups to storage with independent failure and access
boundaries.

## Restore

```bash
illuqc restore /absolute/path/to/backup.sql.gz
```

This is destructive: active sessions are terminated and the configured
database is dropped and recreated. Before restoring:

1. confirm the backup path and target database;
2. stop ingestion and dashboard traffic;
3. create a fresh backup if the current state may be needed;
4. verify sufficient disk space;
5. restore and inspect logs/exit status;
6. validate row counts and application behavior.

## Upgrade procedure

1. Read release notes and identify schema/parser changes.
2. Back up PostgreSQL and `.env` separately.
3. Test the new version against a copy of production data.
4. Run `illuqc audit` and static validation.
5. Apply explicit migrations to existing databases; initialization SQL is not a migration.
6. Set `ILLUQC_VERSION` to the approved version.
7. Rebuild and restart services.
8. validate health, counts, recent runs, and representative charts.
9. Retain a rollback image tag and compatible database backup.

### Removing legacy chemistry-attribute tables

New databases no longer create the discontinued chemistry-attribute tables.
For an existing database, first make and verify a backup, then apply:

```bash
./scripts/runtime/compose.sh exec -T db psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -f /dev/stdin < migrations/001_remove_chemistry_attributes.sql
```

This permanently deletes any values stored in those legacy tables.

### Enable automatic sample registration dates

New databases assign `samples.registration_date` automatically. Apply the same
default to an existing database with:

```bash
./scripts/runtime/compose.sh exec -T db psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -f /dev/stdin < migrations/002_default_sample_registration_date.sql
```

The migration affects future inserts only. It does not invent dates for
existing rows whose registration date is unknown.

### Rename the sample clinical field

New databases use `samples.clinical_method`. Rename the existing
`clinical_test` column without changing its values by applying:

```bash
./scripts/runtime/compose.sh exec -T db psql \
  -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -v ON_ERROR_STOP=1 \
  -f /dev/stdin < migrations/003_rename_clinical_test_to_clinical_method.sql
```

## Capacity considerations

Long-format metrics can produce many rows per run and sample. Monitor database
size, backup duration, query latency, filesystem free space, and log growth.
Large deployments may need indexes derived from observed query plans; add them
through reviewed migrations rather than editing a live container.
