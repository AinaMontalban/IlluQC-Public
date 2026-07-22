# IlluQC demo data

This folder contains **synthetic, non-sensitive** demo CSV files for testing the IlluQC containerized workflow.

## Files

- `sequencing_instruments.csv`: synthetic reference instruments.
- `sequencing_chemistry.csv`: synthetic sequencing chemistry reference rows.
- `DEMO_RUN_*-sequencing-info.csv`: synthetic run-level metadata.
- `DEMO_RUN_*-sequencing-metrics.csv`: synthetic run-level QC metrics.
- `DEMO_RUN_*-samples-metadata.csv`: synthetic sample metadata.
- `DEMO_RUN_*-samples-qc-metrics.csv`: synthetic sample-level QC metrics.

## Usage

From the repository root:

```bash
cp .env.example .env
make setup-data-dirs
make demo
```

The `make demo` target should copy these files into the external data directory configured in `.env`, start PostgreSQL, load the reference tables, load all demo runs, and start Streamlit.

## Important

These files are intended as a portable test dataset. They do not contain patient data, real sample identifiers, real instrument serials, or real sequencing results.

If your current database schema uses different required fields for `instruments`, `sequencing_chemistry`, `samples`, or `sample_qc_metrics`, update these CSV headers to match `db/required_fields.json`.
