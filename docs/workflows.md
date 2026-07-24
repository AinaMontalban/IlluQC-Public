# Ingestion workflows

## Reference data

The current scripts expect reference CSVs directly in `PROCESSED_DATA_DIR`:

| File | Target table | Required columns |
|---|---|---|
| `sequencing_instruments.csv` | `instruments` | `instrument_id`, `instrument_name`, `instrument_type` |
| `sequencing_chemistry.csv` | `sequencing_chemistry` | `sequencing_chemistry_id`, `chemistry_name`, `platform_id` |
| `library.csv` | `library` | `library_id`, `library_name`, `library_version`, `library_type` |

Run `illuqc load-lab-data`. Missing files are skipped; review loader logs.

Referenced `platform_id` values must already exist. The seed SQL provides
`ILLUMINA` and `THERMOFISHER`.

## Illumina runs

### One run

```bash
illuqc parse RUN_ID "Description"
```

The wrapper verifies `ILLUMINA_RAW_DATA_DIR/RUN_ID`, mounts it read-only, and
runs the InterOp parser. Output filenames and columns are controlled by
`parser/Illumina_Runs/illumina_parser_config.json`.

Load normalized run data:

```bash
illuqc load RUN_ID
```

### All runs

```bash
illuqc parse-illumina-runs
illuqc load-runs
```

`parse-illumina-runs` visits each immediate subdirectory of
`ILLUMINA_RAW_DATA_DIR`.
Descriptions may be supplied through `runs_manifest.csv`. The current script
reads tab-delimited `RunID` and `RunDescription` fields despite the `.csv`
extension; preserve that format unless the script is changed.

Batch parser scripts report individual failures but some intentionally return
success after partial completion. Always inspect their summary and log files.

## Thermo Fisher runs

Supported input families are S5 serialized JSON and Genexus plan JSON.

```bash
illuqc parse-thermofisher serialized_run.json S5 "Description"
```

`JSON_FILE` must resolve inside `THERMOFISHER_RAW_DATA_DIR`. `MODEL` accepts
`S5`, `GENEXUS`, or automatic detection when omitted.

Batch discovery:

```bash
illuqc parse-thermofisher-all AUTO
illuqc parse-thermofisher-all S5
illuqc parse-thermofisher-all GENEXUS
```

S5 discovery matches `serialized_*.json`; Genexus discovery matches
`Plan_*.json` and `plan_*.json` recursively.

## Sample-level workflow

Each run should provide these three inputs:

```text
RUN_ID/
├── sample_metadata.tsv
├── multiqc_general_stats.txt
└── sample_libraries.tsv
```

`run_samples_servolab.txt` and `RUN_ID_sample_libraries.txt` remain supported as
legacy filenames. Metadata is tab-delimited with `sample_id` and `sex` columns.
The library mapping is tab-delimited with `sample_id` and `library_id` columns.

Validate without creating files or changing the database:

```bash
illuqc validate-samples RUN_ID
```

Prepare normalized, library-enriched files:

```bash
illuqc prepare-samples RUN_ID
```

Load the prepared files:

```bash
illuqc load-samples RUN_ID
```

The normal operator command combines preparation and loading:

```bash
illuqc ingest-samples RUN_ID
```

The run must already exist in PostgreSQL, and every referenced library must
already be loaded. Existing load-ready files are protected; use `--force` only
after reviewing them.

### One sample

For a new single sample, pass its metadata as options and provide a MultiQC
general-statistics TSV or semicolon-delimited sample-metrics CSV explicitly:

```bash
illuqc prepare-sample RUN_ID SAMPLE_ID \
  --sex F \
  --library-id LIBRARY_ID \
  --clinical-method WES \
  --sample-type Blood \
  --metrics-file /path/to/multiqc_general_stats.txt

illuqc load-sample RUN_ID SAMPLE_ID
```

`--metrics-file` can be repeated when metrics are split across files. Duplicate
metric values are merged; conflicting values fail validation. The sample's
registration date is assigned by PostgreSQL when `load-sample` first inserts
the sample. Existing load-ready output is protected unless `--force` is used.

The semicolon format is detected from its header, beginning with `sample` and
the configured BAM/coverage metric columns. MultiQC and semicolon files can be
provided together:

```bash
illuqc ingest-sample RUN_ID SAMPLE_ID \
  --sex F \
  --library-id LIBRARY_ID \
  --metrics-file /path/to/multiqc_general_stats.txt \
  --metrics-file /path/to/sample_metrics.csv
```

Preparation and loading can be combined by replacing `prepare-sample` with
`ingest-sample`.

The older run-folder form remains available when metadata, MultiQC statistics,
and library mappings are already stored together:

```bash
illuqc validate-sample RUN_ID SAMPLE_ID
illuqc prepare-sample RUN_ID SAMPLE_ID
illuqc load-sample RUN_ID SAMPLE_ID
```

Or combine the last two stages:

```bash
illuqc ingest-sample RUN_ID SAMPLE_ID
```

Single-sample files are isolated from run-wide files.

### Every run

```bash
illuqc prepare-samples-all
illuqc load-samples-all
```

Bulk commands return a failure status if any requested run fails.

### Output layout

```text
Samples_Data/RUN_ID/
├── intermediate/
│   └── RUN_ID-samples-qc-metrics.csv
├── load-ready/
│   ├── samples.csv
│   └── sample-qc-metrics.csv
├── samples/SAMPLE_ID/
│   ├── intermediate/
│   └── load-ready/
└── preparation-summary.txt
```

Intermediate MultiQC output is preserved. Library enrichment writes a separate
database-ready file instead of replacing the parser output.

## Loader behavior

The loader:

1. verifies the CSV and required-fields mapping exist;
2. verifies the target table exists;
3. checks required columns against CSV and database schema;
4. ignores extra CSV columns unless `--strict` is used;
5. normalizes empty numeric metric values to SQL `NULL`;
6. inserts in batches;
7. skips conflicting primary keys with `ON CONFLICT DO NOTHING`.

It is an append/idempotent loader, not an upsert tool. Correcting an already
loaded record requires an explicit reviewed database update or delete/reload.
