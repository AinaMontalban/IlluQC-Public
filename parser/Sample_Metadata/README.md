# Sample Metadata Parser

Parser that extracts sample metadata from a tab-delimited file and writes it as a CSV file ready for database upload.

## Input

The parser expects a tab-delimited file with at least 4 columns:

```
<sample_id>  <sex>  <column2>  <method_name>  ...
```

Column positions:
- Column 0: `sample_id`
- Column 1: `sex`
- Column 3: `method_name`

## Output

A CSV file is generated with the following columns:

| Column | Description |
|---|---|
| `sample_id` | Sample identifier |
| `sex` | Sex of the sample |
| `method_name` | Method/protocol name |

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

### Batch processing

```bash
INPUT_DIR=/Users/amontalban/HCB-Work/Doctorat/IlluQC/Input_Data/Illumina_Runs_Data
OUTPUT_DIR=/Users/amontalban/HCB-Work/Doctorat/IlluQC/Upload_Data/Samples_Data

for metadata_file in "$INPUT_DIR"/*/run_samples_servolab.txt; do
    echo $metadata_file
    [ -f "$metadata_file" ] || continue
    RUN_ID=$(basename $(dirname "$metadata_file"))
    FILE_NAME=$(basename "$metadata_file" .txt)
    python parse_sample_metadata.py \
        --input-file "$metadata_file" \
        --output-file "$OUTPUT_DIR/${RUN_ID}-${FILE_NAME}-parsed.csv" \
        --log-file "/Users/amontalban/HCB-Work/Doctorat/IlluQC/Logs_Folder/${RUN_ID}-${FILE_NAME}-samples-metadata.log"
done
```

## Arguments reference

| Argument | Required | Default | Description |
|---|---|---|---|
| `--input-file` | Yes | — | Path to the input tab-delimited metadata file |
| `--output-file` | Yes | — | Path to the output CSV file |
| `--log` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `--log-file` | No | *stderr* | Path to a log file (instead of console) |
