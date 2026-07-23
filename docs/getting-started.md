# Getting started

## Prerequisites

Install Git, Make, Docker, and Docker Compose v2. Ensure the Docker daemon is
running and that the account starting IlluQC can read the input directories and
write to processed, log, backup, and PostgreSQL directories.

## 1. Configure the deployment

```bash
cp .env.example .env
```

Edit `.env` before starting anything:

- replace `POSTGRES_PASSWORD` with a long, random password;
- confirm every external directory points to the intended storage;
- on Linux, set `LOCAL_UID` and `LOCAL_GID` to `id -u` and `id -g`;
- choose a stable `ILLUQC_VERSION` image tag.

Do not commit `.env`. It is ignored by Git.

The commands below use the `illuqc` launcher. From a repository checkout, use
`./illuqc`; after installing it on your `PATH`, use `illuqc` from any directory.

## 2. Create external directories

```bash
illuqc setup
```

The default layout is:

```text
../NGS_Data/
├── raw_data/
│   ├── illumina/
│   │   └── reference_tables/
│   └── thermofisher/
│       └── reference_tables/
├── processed/
│   ├── Runs_Data/
│   └── Samples_Data/
├── logs/
│   ├── parser/
│   ├── loader/
│   └── app/
├── backups/
├── postgres_data/
└── config/
```

Raw data is mounted read-only. Parser output, logs, backups, and database files
are writable and persist independently of containers.

## 3. Start services

```bash
illuqc start
```

Confirm health:

```bash
illuqc status
illuqc wait-db
```

Open <http://localhost:8501>. 

## 4. Load reference data

Provide these CSV files in `PROCESSED_DATA_DIR`:

```text
sequencing_instruments.csv
sequencing_chemistry.csv
library.csv
```

Then run:

```bash
illuqc load-lab-data
```

The loader skips a missing reference CSV with a warning. Inspect
`LOG_DIR/loader/` instead of assuming every table was loaded.

## 5. Parse and load an Illumina run

Place the run at `ILLUMINA_RAW_DATA_DIR/RUN_ID`. At minimum, the parser expects
the vendor files appropriate to the instrument and InterOp version; a typical
folder contains `RunInfo.xml`, `RunParameters.xml`, `SampleSheet.csv`, and
`InterOp/`.

```bash
make parse RUN_ID=RUN_ID DESCRIPTION="Run description"
make load RUN_ID=RUN_ID
```

Expected run outputs are written under `PROCESSED_DATA_DIR/Runs_Data`:

```text
RUN_ID-sequencing-info.csv
RUN_ID-sequencing-metrics.csv
```

At present, `make load` loads the first two files.

## 6. Samples data

Parse sample metadata and MultiQC statistics, associate library identifiers,
then load sample data:

```bash
illuqc ingest-samples RUN_ID
```

The command validates metadata, MultiQC sample IDs, sex values, and library
mappings before producing and loading database-ready files.

## 7. Stop safely

```bash
make down
```

This stops containers without deleting `POSTGRES_DATA_DIR`. Back up the
database regularly with `make backup`.
