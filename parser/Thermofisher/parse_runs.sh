
#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Parse all ThermoFisher JSON files in RUNS_THERMOFISHER and write CSVs
# to RUNS_5.  Serialized (S5) files use "AP-AMPLISEQ"; the Genexus Plan
# file uses "CBM-MYE-DNA".
# ---------------------------------------------------------------------------

set -euo pipefail

INPUT_DIR="/Users/amontalban/HCB-Work/Doctorat/P005-multiplatform/real_data/RUNS_THERMOFISHER"
OUTPUT_DIR="/Users/amontalban/HCB-Work/Doctorat/P005-multiplatform/real_data/RUNS_5"
PARSER="$(dirname "$0")/ThermoFisher_sequencing_data_parser.py"

mkdir -p "$OUTPUT_DIR"

count=0
errors=0

for json_file in "$INPUT_DIR"/s*.json; do
    basename=$(basename "$json_file")

    # Skip copy/backup files
    if echo "$basename" | grep -qi 'copy'; then
        echo "SKIP  $basename (copy file)"
        continue
    fi


    run_description="AP-AMPLISEQ"

    echo "--- Processing: $basename  (description: $run_description)"

    if python3 "$PARSER" \
        --json-file "$json_file" \
        --output-dir "$OUTPUT_DIR" \
        --instrument-model "S5" \
        --run-description "$run_description"; then
        count=$((count + 1))
    else
        echo "ERROR processing $basename"
        errors=$((errors + 1))
    fi
done

echo ""
echo "Done. Processed: $count   Errors: $errors"