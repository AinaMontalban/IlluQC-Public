# IlluQC installation guide

This guide covers the recommended Docker Compose installation. Native Python
and Apptainer/Singularity options are documented in
[INSTALLATION_OPTIONS.md](INSTALLATION_OPTIONS.md).

For architecture, configuration, workflow, data-model, operations, security,
and troubleshooting references, see the [documentation index](docs/README.md).

## Requirements

- Git
- Docker with Docker Compose v2
- Make

IlluQC invokes Docker Compose v2 through `scripts/runtime/compose.sh`.

## Configure IlluQC

```bash
git clone <repo-url> IlluQC
cd IlluQC
cp .env.example .env
chmod 600 .env
```

Edit `.env` and replace `POSTGRES_PASSWORD` with a long random password. The
external paths default to directories below `../NGS_Data`; adjust them before
starting services if your data belongs elsewhere.

Create the external directories and start PostgreSQL and Streamlit:

```bash
./illuqc setup
./illuqc start
```

The dashboard is available at <http://localhost:8501>. PostgreSQL data is
persisted at `POSTGRES_DATA_DIR`, outside the repository and containers.

## Input layout

Place Illumina runs at:

```text
../NGS_Data/raw_data/illumina/RUN_ID/
├── RunInfo.xml
├── RunParameters.xml
├── SampleSheet.csv
└── InterOp/
```

Place Thermo Fisher JSON exports below:

```text
../NGS_Data/raw_data/thermofisher/
```

Place reference tables in `PROCESSED_DATA_DIR`:

```text
../NGS_Data/processed/
├── sequencing_instruments.csv
├── sequencing_chemistry.csv
└── library.csv
```

## Common workflow

```bash
illuqc load-lab-data
illuqc parse RUN_ID "Run description"
illuqc load RUN_ID
```

Thermo Fisher exports can be parsed with:

```bash
illuqc parse-thermofisher serialized_run.json S5
illuqc parse-thermofisher-all AUTO
```

Processed output is written below `../NGS_Data/processed`; logs are written
below `../NGS_Data/logs`.

## Backup and restore

```bash
illuqc backup
illuqc restore ../NGS_Data/backups/illuqcdb-YYYYMMDD_HHMMSS.sql.gz
```

Restore drops and recreates the configured database. Keep independent,
regularly verified copies of important backups.

## Troubleshooting

Inspect service state and logs:

```bash
./scripts/runtime/compose.sh ps
illuqc logs
bash scripts/runtime/wait_for_database.sh
```

The Compose database host is `db`. Confirm that `.env` defines the same
`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values used when the
database directory was first initialized. Changing initialization credentials
does not rewrite an existing PostgreSQL data directory.

To stop services without deleting persistent data:

```bash
illuqc stop
```
