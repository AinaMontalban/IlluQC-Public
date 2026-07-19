# coreBM-ThermoFisher_Parser

Parser for **ThermoFisher / Ion Torrent** sequencing JSON exports.

Reads Ion Torrent JSON files (S5 serialized exports or Genexus experiment-graph exports) and writes two CSV files compatible with the [IlluQC Database](../coreBM-IlluQC_DB_Streamlit/) `upload_CSV.py` loader.

## Supported input formats

| Format | Filename pattern | Source | Structure |
|---|---|---|---|
| **Serialized JSON** | `serialized_*.json` | Ion Torrent S5 | Django fixture — JSON array of `{model, pk, fields}` objects |
| **Experiment-graph JSON** | `Plan_*.json` | Genexus | Flat JSON object with `chipMetrics`, `experimentChips`, `resultsQcs`, etc. |

The parser **auto-detects** the format.

## Output files

For each input JSON, two CSVs are produced (matching the Illumina parser output format):

### `<run_id>-sequencing-info.csv`

| Column | Description |
|---|---|
| `run_id` | Run identifier (from `planDisplayedName` / `planName`) |
| `run_folder` | Internal experiment name |
| `run_description` | User-supplied description |
| `day_id` | Run date (YYYY-MM-DD) |
| `instrument_id` | Instrument name (`pgmName`) |
| `platform_id` | `THERMOFISHER` |
| `sequencing_chemistry_id` | Derived from reagent part + chip type |
| `flowcell_part_number` | Chip barcode |
| `reagent_kit_part_number` | Chef reagents part number |
| `num_cycles` | Number of flows |
| `num_samples` | Number of samples |

### `<run_id>-sequencing-metrics.csv`

Long-format metrics compatible with `sequencing_qc_metrics` table:

| Column | Description |
|---|---|
| `run_id` | Run identifier |
| `day_id` | Run date (YYYY-MM-DD) |
| `metric_id` | Metric identifier (see table below) |
| `value_number` | Numeric value |

#### Metric mapping

| Source field | `metric_id` | Description |
|---|---|---|
| `totalNumReads` | `ION_READS_TOTAL` | Total reads |
| `q20_mean_read_length` | `ION_READ_LENGTH_MEAN` | Mean Q20 read length (bp) |
| `q20_bases_pct` (derived) | `ION_Q20_BASES_PCT` | % bases ≥ Q20 |
| `loading` | `ION_LOADING_PCT` | Chip loading % |
| `throughput_mb` (derived) | `ION_THROUGHPUT_MB` | Throughput (Mb) |

## Extracted fields (from serialized JSON)

| Requested field | Model |
|---|---|
| `chipType` | `rundb.experiment` |
| `chipBarcode` | `rundb.experiment` |
| `chefReagentsPart` | `rundb.experiment` |
| `pgmName` | `rundb.experiment` |
| `chefChipType1` | `rundb.experiment` |
| `chefChipType2` | `rundb.experiment` |
| `expName` | `rundb.experiment` |
| `planDisplayedName` | `rundb.plannedexperiment` |
| `templatingKitName` | `rundb.plannedexperiment` |
| `libraryKitName` | `rundb.experimentanalysissettings` |
| `loading` | `rundb.analysismetrics` |
| `totalNumReads` | `rundb.libmetrics` |
| `total_mapped_reads` | `rundb.libmetrics` |
| `total_mapped_target_bases` | `rundb.libmetrics` |
| `q20_alignments` | `rundb.libmetrics` |
| `q20_mean_read_length` | `rundb.qualitymetrics` |
| `q0_reads` | `rundb.qualitymetrics` |
| `q20_bases` | `rundb.qualitymetrics` |

## Usage

```bash
# Parse a serialized JSON file (S5)
python ThermoFisher_sequencing_data_parser.py \
    --json-file serialized_Auto_user_GSS5PL-0146-1364-2026_01_08_R26_0010_1654.json \
    --output-dir ./output \
    --run-description "CBM-LYMPHOMA"

# Parse a Genexus Plan JSON file
python ThermoFisher_sequencing_data_parser.py \
    --json-file Plan_2026_03_03_R26_0176_GX2_FOA39_experiment-graph.json \
    --output-dir ./output \
    --run-description "CBM-MYE-DNA"

# Override run_id if the plan name differs from your naming convention
python ThermoFisher_sequencing_data_parser.py \
    --json-file serialized_*.json \
    --output-dir ./output \
    --run-id-override "R26_0010"

# Enable debug logging
python ThermoFisher_sequencing_data_parser.py \
    --json-file input.json \
    --output-dir ./output \
    --log DEBUG \
    --log-file parser.log
```

## Requirements

Python ≥ 3.8. No external dependencies (uses only standard library).

## Configuration

External configuration is in [`thermofisher_parser_config.json`](thermofisher_parser_config.json). Editable keys:

- `platform_id` — platform identifier written to CSVs
- `metric_id_map` — source field → DB `metric_id` mapping
- `fields` — column lists for each output CSV
- `serialized_model_fields` — documents which fields are read from which Django model
