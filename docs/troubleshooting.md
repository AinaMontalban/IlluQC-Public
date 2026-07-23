# Troubleshooting

## Compose rejects the configuration

Run:

```bash
./scripts/runtime/compose.sh config
```

Errors naming `POSTGRES_PASSWORD`, `POSTGRES_DATA_DIR`, or another path indicate
a missing `.env` value. Start from `.env.example` and avoid shell syntax that
Compose cannot parse.

## PostgreSQL does not become healthy

```bash
./scripts/runtime/compose.sh ps
./scripts/runtime/compose.sh logs --tail=200 db
ls -ld "$POSTGRES_DATA_DIR"
```

Common causes are permissions, insufficient disk space, an incompatible data
directory, or credentials changed after initialization. Do not delete the data
directory as a troubleshooting shortcut. Back it up and establish whether a
version upgrade or restore is required.

## Streamlit cannot connect

```bash
./scripts/runtime/compose.sh logs --tail=200 streamlit
./scripts/runtime/compose.sh exec -T streamlit env | grep '^DB_'
./scripts/runtime/compose.sh exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Within Compose, the database host is `db`, not `localhost`. Passwords containing
URL-reserved characters are supported because the app uses SQLAlchemy's
structured URL builder.

## Parser cannot find a run

Verify the host path and Compose mount:

```bash
ls -la "$ILLUMINA_RAW_DATA_DIR/RUN_ID"
./scripts/runtime/compose.sh run --rm --entrypoint sh parser -c 'ls -la /data/raw/illumina'
```

Thermo Fisher JSON must reside below `THERMOFISHER_RAW_DATA_DIR`; the wrapper
rejects files outside that root intentionally.

## Parser writes permission-denied errors

Check `LOCAL_UID`, `LOCAL_GID`, and directory ownership:

```bash
id
ls -ld "$PROCESSED_DATA_DIR" "$LOG_DIR"
```

On Linux, make the configured numeric IDs match the host account that owns the
external directories.

## Loader reports missing required columns

Compare the CSV header with `db/required_fields.json` and the target table in
`init-db/01_schema_ddl.sql`. The live database schema is authoritative for an
existing deployment. Confirm that the selected table actually exists; the JSON
contains some legacy/planned mappings.

## Loader reports foreign-key violations

Load parent records first. Typical corrections are:

- load instruments and chemistry before runs;
- load runs before run metrics;
- load samples and libraries before sample metrics;
- add metric definitions before their values.

## A corrected CSV does not change a row

The loader uses `ON CONFLICT DO NOTHING`. It skips an existing primary key. A
correction requires a reviewed SQL update or deletion followed by reload.

## Sample metrics are skipped or fail

Run `illuqc validate-samples RUN_ID`. Confirm every sample appears in metadata,
MultiQC, and the library mapping; verify referenced libraries and the run are
already loaded.

## Batch command says success despite failures

Some batch wrappers continue after individual failures and may return success
to allow other runs to complete. Read the printed summary and inspect every
corresponding parser/loader log.
