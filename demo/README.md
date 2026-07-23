# IlluQC demo data

This folder contains **synthetic, non-sensitive** demo CSV files for testing the IlluQC containerized workflow.

## Files

- `sequencing_instruments.csv`: synthetic reference instruments.
- `sequencing_chemistry.csv`: synthetic sequencing chemistry reference rows.
- `R###-sequencing-info.csv`: synthetic MiSeq run-level metadata.
- `R###-sequencing-metrics.csv`: synthetic MiSeq run-level QC metrics.
- `R###-samples-metadata.csv`: synthetic sample metadata.
- `R###-samples-qc-metrics.csv`: synthetic HLA and ALLOSEQ sample metrics.

The dataset contains two synthetic MiSeq instruments, two libraries (`HLA` and
`ALLOSEQ`), and two sequencing chemistries (`MISEQ_V2` and `MISEQ_V3`). Run
`R010` uses MiSeq v3 chemistry. Run `R011` repeats samples `S001`–`S005` from
`R001` using the same MiSeq v2 chemistry, allowing longitudinal comparison
without a chemistry change. Each run is assigned entirely to either `HLA` or
`ALLOSEQ`; its run description, sample clinical method, QC library, and library
mapping all use the same value.

## Usage

From the repository root:

```bash
cp .env.example .env
./illuqc setup
./illuqc demo
```

`illuqc demo` reports the resolved paths and input counts, refreshes the
configured processed run/sample directories, loads reference, run, and sample
data, prints database row counts, and starts Streamlit.

## Important

These files are intended as a portable test dataset. They do not contain patient data, real sample identifiers, real instrument serials, or real sequencing results.

If your current database schema uses different required fields for `instruments`, `sequencing_chemistry`, `samples`, or `sample_qc_metrics`, update these CSV headers to match `db/required_fields.json`.
