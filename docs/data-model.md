# Data model and file contracts

## Relationship summary

```text
sequencing_platforms
├── instruments
├── sequencing_chemistry
└── qc_metric_definitions

day ──> sequencing_run <── instruments / sequencing_chemistry
              ├── sequencing_qc_metrics ──> qc_metric_definitions
              └── sample_qc_metrics ──> samples / library / qc_metric_definitions
```

## Tables

### Dimensions

- `sequencing_platforms`: stable platform identifiers.
- `instruments`: instrument identity, model, type, and platform.
- `sequencing_chemistry`: named chemistry/flow-cell/chip products.
- `samples`: minimal sample metadata used by the dashboard.
- `library`: library preparation/enrichment definitions.
- `day`: dates from 2020-01-01 through 2050-12-31, seeded at initialization.
- `qc_metric_definitions`: metric labels, scope, workflow step, units, type, and platform.

### Facts

- `sequencing_run`: one row per run, uniquely keyed by `(run_id, day_id)` and
  also constrained unique on `run_id`.
- `sequencing_qc_metrics`: one numeric observation per run/date/metric.
- `sample_qc_metrics`: one numeric observation per sample/run/library/metric.

### Metadata

`schema_metadata` records the logical schema name/version. It does not replace a
database migration history.

## CSV contracts

### Sequencing run

```csv
run_id,run_folder,run_description,day_id,instrument_id,platform_id,sequencing_chemistry_id,num_cycles,num_samples
```

Dates must be PostgreSQL-compatible ISO dates. Referenced instrument, platform,
and chemistry records must exist before loading.

### Run metric

```csv
run_id,day_id,metric_id,value_number
```

The `(run_id, day_id)` pair must exist in `sequencing_run`; `metric_id` must
exist in `qc_metric_definitions`.

### Sample metadata

```csv
sample_id,sex,clinical_method,sample_type
```

The loader's minimum for `samples` is `sample_id,sex`. Other metadata columns
are optional. `registration_date` is not taken from the CSV: PostgreSQL assigns
`CURRENT_DATE` when the sample row is first inserted. Reloading an existing
sample does not change its date because duplicate primary keys are skipped.

### Sample metric

```csv
sample_id,run_id,library_id,metric_id,value_number
```

All four identifiers participate in relationships or the primary key.

## Metric extension procedure

To add a metric safely:

1. choose a stable uppercase `metric_id`;
2. add an idempotent seed row to `02_schema_seed.sql` for new databases;
3. migrate existing databases with an explicit `INSERT ... ON CONFLICT`;
4. add the vendor-field mapping to the relevant parser configuration;
5. parse a representative fixture and confirm units and scale;
6. confirm the dashboard label and platform filtering.

Do not reuse an identifier for a metric with different semantics or units.

## Known contract caveats

`db/required_fields.json` contains mappings for some legacy or planned tables
that are not created by the current DDL. Their presence does not make those
tables loadable. The live schema remains authoritative.

Seed SQL still contains historical `IlluQC` labels in comments and
`schema_metadata`; these labels do not change runtime table names.
