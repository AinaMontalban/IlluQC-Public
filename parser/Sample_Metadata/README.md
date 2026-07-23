# Sample Metadata Parser

Parser that extracts sample metadata from a tab-delimited file and writes it as a CSV file ready for database upload.

## Input

The parser expects a tab-delimited file with `sample_id` and `sex` columns. A
header is recommended; legacy headerless two-column files remain supported.

```
sample_id  sex
S001       F
```

## Output

A CSV file is generated with the following columns:

| Column | Description |
|---|---|
| `sample_id` | Sample identifier |
| `sex` | Sex of the sample |

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

### Single file

```bash
python parse_sample_metadata.py \
  --input-file /path/to/sample_metadata.txt \
  --output-file /path/to/output.csv \
  --log-file "/path/to/logs/parse.log"
```

For the supported containerized workflow, prefer
`illuqc prepare-samples RUN_ID` or `illuqc prepare-sample ...` instead of
calling this low-level parser directly.

## Arguments reference

| Argument | Required | Default | Description |
|---|---|---|---|
| `--input-file` | Yes | — | Path to the input tab-delimited metadata file |
| `--output-file` | Yes | — | Path to the output CSV file |
| `--log` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `--log-file` | No | *stderr* | Path to a log file (instead of console) |
| `--sample-id` | No | all samples | Only emit the matching sample ID |
