# IlluQC installation guide

This guide explains how to install and run IlluQC with Docker Compose while keeping all data outside the repository and outside the containers.

## 1. Requirements

Install:

- Git
- Docker
- Docker Compose v2
- Make

Check versions:

```bash
git --version
docker --version
docker compose version
make --version
```

## 2. Clone the repository

```bash
git clone <repo-url> IlluQC
cd IlluQC
```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` if needed. The most important variable is:

```bash
ILLUQC_DATA_ROOT=../IlluQC_Data
```

By default, IlluQC expects the external data directory next to the repository.

## 4. Create external data folders

```bash
make setup-data-dirs
```

This creates:

```text
../IlluQC_Data/raw/
../IlluQC_Data/processed/
../IlluQC_Data/logs/
../IlluQC_Data/backups/
../IlluQC_Data/postgres_data/
../IlluQC_Data/config/
```

## 5. Add input data

Put Illumina run folders here:

```text
../NGS_Data/raw_data/illumina/RUN_ID/
```

Each run folder should contain:

```text
RunInfo.xml
RunParameters.xml
SampleSheet.csv
InterOp/
```

Put reference tables here:

```text
../NGS_Data/raw_data/illumina/reference_tables/sequencing_instruments.csv
../NGS_Data/raw_data/illumina/reference_tables/sequencing_chemistry.csv
```

## 6. Build and start services

```bash
make up
```

This starts PostgreSQL and Streamlit. Streamlit is available at:

```text
http://localhost:8501
```

## 7. Parse one run

```bash
make parse RUN_ID=RUN_ID DESCRIPTION="Run description"
```

Expected outputs:

```text
../IlluQC_Data/processed/Runs_Data/RUN_ID-sequencing-info.csv
../IlluQC_Data/processed/Runs_Data/RUN_ID-sequencing-metrics.csv
../IlluQC_Data/logs/parser/RUN_ID_parser.log
```

## 8. Load reference tables

```bash
make load-reference
```

## 9. Load one run

```bash
make load RUN_ID=RUN_ID
```

This attempts to load:

```text
RUN_ID-sequencing-info.csv
RUN_ID-sequencing-metrics.csv
RUN_ID-samples-metadata.csv
RUN_ID-samples-qc-metrics.csv
```

Missing optional files are skipped with a warning.

## 10. Load all processed runs

```bash
make load-all
```

## 11. Backup database

```bash
make backup
```

Backups are written to:

```text
../IlluQC_Data/backups/
```

## 12. Restore database

```bash
make restore BACKUP=../IlluQC_Data/backups/illuqcdb-YYYYMMDD_HHMMSS.sql.gz
```

Warning: restore drops and recreates the configured database.

## 13. Troubleshooting

### PostgreSQL does not start

Check logs:

```bash
make logs
```

If the database directory was created with incompatible data, remove it carefully:

```bash
make down
rm -rf ../IlluQC_Data/postgres_data/*
make up
```

### Parser cannot find a run folder

Check that the run exists on the host:

```bash
ls ../NGS_Data/raw_data/Runs_Data/RUN_ID
```

And that it contains:

```text
RunInfo.xml
RunParameters.xml
SampleSheet.csv
InterOp/
```

### Loader cannot connect to PostgreSQL

Check that the database is healthy:

```bash
bash scripts/wait_for_db.sh
```

### Streamlit cannot connect to database

Check `.env`:

```bash
ILLUQC_DB_URL=postgresql://postgres:postgres@db:5432/illuqcdb
```

Inside Docker Compose, the database host should be `db`, not `localhost`.
