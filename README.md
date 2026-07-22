# IlluQC

IlluQC is a reproducible workflow for parsing Illumina sequencing run quality-control data, loading the resulting CSV files into PostgreSQL, and visualising the data with a Streamlit dashboard.

The project is designed around one important rule:

> Containers contain code and dependencies only. Raw sequencing data, processed CSVs, logs, backups, configuration and PostgreSQL persistence stay outside the containers and are mounted at runtime.

## Main components

| Component | Purpose |
|---|---|
| `db` | PostgreSQL database initialised with the IlluQC schema. |
| `parser` | Parses Illumina run folders and MultiQC outputs. |
| `loader` | Loads processed CSV files into PostgreSQL. |
| `streamlit` | Runs the interactive dashboard. |
| `scripts/` | Operational scripts for setup, parsing, loading, backup and restore. |

## Repository layout

```text
IlluQC/
├── app/
├── parser/
├── db/
├── init_db/
├── scripts/
├── containers/
├── Dockerfile.parser
├── Dockerfile.loader
├── Dockerfile.streamlit
├── docker-compose.yml
├── Makefile
├── .env.example
├── README.md
└── INSTALL.md
```

## External data layout

The data directory should live outside the repository, for example as `../IlluQC_Data`:

```text
NGS_Data/
├── raw_data/
│   ├── illumina/
│   │   ├── RUN_ID/
│   │   │   ├── RunInfo.xml
│   │   │   ├── RunParameters.xml
│   │   │   ├── SampleSheet.csv
│   │   │   └── InterOp/
│   │   └── reference_tables/
│   └── thermofisher/
│       ├── serialized_run.json
│       ├── Plan_run.json
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

## Quick start

```bash
cp .env.example .env
make setup-data-dirs
make up
```

Open the dashboard at:

```text
http://localhost:8501
```

## Save instruments and chemistry reference tables

Before loading any sequencing runs, you must load the reference tables for instruments and sequencing chemistry into the database.

Place the reference CSV files here:

```text
../NGS_Data/raw_data/illumina/reference_tables/
├── sequencing_instruments.csv
└── sequencing_chemistry.csv
```

### sequencing_instruments.csv format

```csv
instrument_id,instrument_name,instrument_model,instrument_type,platform_id
NOVA_01,NovaSeq System 1,NovaSeq 6000,Sequencer,ILLUMINA
MISEQ_01,MiSeq System 1,MiSeq,Sequencer,ILLUMINA
ION_01,Ion Torrent S5 XL,Ion S5 XL,Sequencer,THERMOFISHER
```

**Required columns:**
- `instrument_id`: Unique identifier for the instrument
- `instrument_name`: Human-readable name
- `instrument_model`: Instrument model/version
- `instrument_type`: Type (e.g., "Sequencer")
- `platform_id`: Platform identifier (`ILLUMINA` or `THERMOFISHER`)

### sequencing_chemistry.csv format

```csv
sequencing_chemistry_id,chemistry_name,platform_id
NOVA_S4,NovaSeq S4 Flowcell,ILLUMINA
NOVA_S2,NovaSeq S2 Flowcell,ILLUMINA
ION_520,Ion 520 Chip,THERMOFISHER
```

**Required columns:**
- `sequencing_chemistry_id`: Unique identifier for the chemistry
- `chemistry_name`: Human-readable chemistry name
- `platform_id`: Platform identifier (`ILLUMINA` or `THERMOFISHER`)

### Load reference tables

Then run:

```bash
make load-reference
```

This loads both `sequencing_instruments.csv` and `sequencing_chemistry.csv` into the database.

## Parse one Illumina run

Place the run folder outside the repository:

```text
../NGS_Data/raw_data/Runs_Data/RUN_ID/
```

Then run:

```bash
make parse RUN_ID=RUN_ID DESCRIPTION="Run description"
```

The parser writes output to:

```text
../IlluQC_Data/processed/Runs_Data/
../IlluQC_Data/logs/parser/
```

## Parse multiple runs

To parse all run folders at once, place all raw run folders in:

```text
../NGS_Data/raw_data/Runs_Data/
├── RUN_001/
│   ├── RunInfo.xml
│   ├── RunParameters.xml
│   └── InterOp/
├── RUN_002/
│   ├── RunInfo.xml
│   ├── RunParameters.xml
│   └── InterOp/
└── ...
```

Then run:

```bash
make parse-all
```

## Parse a Thermo Fisher run

Place an Ion Torrent S5 serialized JSON export or a Genexus Plan JSON export
anywhere below `THERMOFISHER_RAW_DATA_DIR`. Then run:

```bash
make parse-thermofisher \
  JSON_FILE=Thermofisher_Data/serialized_run.json \
  DESCRIPTION="Re-sequencing run"
```

The parser detects S5 and Genexus formats automatically. To force one format:

```bash
make parse-thermofisher \
  JSON_FILE=Thermofisher_Data/Plan_run.json \
  DESCRIPTION="Genexus run" \
  MODEL=GENEXUS
```

`MODEL` accepts `S5` or `GENEXUS`. `JSON_FILE` may be relative to
`THERMOFISHER_RAW_DATA_DIR` or an absolute path inside it. Normalized run and metric CSVs are
written to `PROCESSED_DATA_DIR/Runs_Data` and can be loaded with the existing
`make load RUN_ID=...` command.

To recursively parse every supported Thermo Fisher JSON export:

```bash
make parse-thermofisher-all MODEL=S5
```

Use `MODEL=S5` for `serialized_*.json` exports or `MODEL=GENEXUS` for
`Plan_*.json`/`plan_*.json` exports. The model limits discovery to matching
files and forces the corresponding parser. Use `MODEL=AUTO` or omit `MODEL` to
parse both formats with automatic detection. The wrapper continues after
individual failures, prints a summary, and returns a failure status if any
export could not be parsed. An optional description can be applied to every
matching export:

```bash
make parse-thermofisher-all \
  MODEL=GENEXUS \
  DESCRIPTION="Imported Genexus runs"
```

### Optional: Use a manifest file with run descriptions

To automatically include descriptions for each run, create an optional manifest file:

```text
../NGS_Data/runs_manifest.csv
```

**Format:**

```csv
RunID,RunDescription
RUN_001,NovaSeq run from 2026-01-15
RUN_002,MiSeq validation run
RUN_003,Quality control re-sequencing
```

When `parse-all` runs, it will:
- Read descriptions from the manifest if it exists
- Use the descriptions for each matching run
- Parse runs without manifest entries with no description (backward compatible)

This will parse all sequencing runs and write the processed CSV files to:

```text
../NGS_Data/processed/Runs_Data/
../NGS_Data/logs/parser/
```

## Load one run into PostgreSQL

```bash
make load RUN_ID=RUN_ID
```

## Load multiple runs into PostgreSQL

To load all processed runs at once, place all processed run folders in:

```text
../NGS_Data/processed/Runs_Data/
├── RUN_001-sequencing-info.csv
├── RUN_001-sequencing-metrics.csv
├── RUN_002-sequencing-info.csv
├── RUN_002-sequencing-metrics.csv
└── ...
```

Then run:

```bash
make load-all
```

This will load all sequencing runs, samples, and QC metrics from the processed directory into the database.

## Load sample metadata and QC metrics

After parsing sample metadata and QC metrics files, load them into the database:

```bash
make load-sample-data
```

This loads:
- Sample metadata (sample ID, sex, virtual panel) into the `samples` table
- Sample QC metrics (FastQC metrics, etc.) into the `sample_qc_metrics` table

## Backup and restore

Create a backup:

```bash
make backup
```

Restore a backup:

```bash
make restore BACKUP=../IlluQC_Data/backups/illuqcdb-YYYYMMDD_HHMMSS.sql.gz
```

## Useful commands

```bash
make up                       # Build and start db + Streamlit
make down                     # Stop services
make reset                    # Stop services and remove containers/volumes
make logs                     # Follow Docker logs
make db-shell                 # Open PostgreSQL shell
make parse RUN_ID=...         # Parse one Illumina run
make parse-all                # Parse all run folders
make parse-multiqc-all        # Parse MultiQC data for all runs
make parse-sample-metadata-all # Parse sample metadata for all runs
make load RUN_ID=...          # Load one processed run
make load-all                 # Load all processed runs
make load-sample-data         # Load sample metadata and QC metrics
make backup                   # Create DB backup
make restore BACKUP=...       # Restore DB backup
```

## Docker vs Apptainer/Singularity

Docker Compose is used for local development and service orchestration. The project is structured so that parser and loader containers can later be converted to Apptainer/Singularity images. This is why all data paths are external and mounted into containers as `/data/raw`, `/data/processed` and `/logs`.
