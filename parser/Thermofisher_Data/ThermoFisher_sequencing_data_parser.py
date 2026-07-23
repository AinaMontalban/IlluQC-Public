"""ThermoFisher / Ion Torrent sequencing data parser.

Reads Ion Torrent JSON exports and writes two CSV files compatible
with the IlluQC database ``upload_CSV.py`` loader:

  - ``<run_id>-sequencing-info.csv``  — one-row run metadata
  - ``<run_id>-sequencing-metrics.csv`` — long-format QC metrics

Supported input formats
-----------------------
1. **Serialized JSON** (``serialized_*.json``):  Django fixture format
   from Ion Torrent S5 — array of ``{model, pk, fields}`` objects.
2. **Experiment-graph JSON** ):  Genexus export — flat
   JSON with ``chipMetrics``, ``experimentChips``, ``experimentKits``,
   ``resultsQcs``, etc.
"""

import argparse
import csv
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).with_name("thermofisher_parser_config.json")
CONFIG = {}


def load_config(path=CONFIG_PATH):
    """Load the parser configuration from a JSON file.

    Args:
        path: Path to the JSON config file.

    Returns:
        dict with configuration keys.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def normalize_day_id(date_text):
    """Normalize a date string to ISO 8601 format (YYYY-MM-DD).

    Accepts:
      - ISO datetime with timezone: ``2026-01-09T07:08:22Z``
      - ISO datetime without tz:   ``2026-01-09T07:08:22``
      - ISO date:                   ``2026-01-09``
      - Epoch millis (int/float):   ``1772492400000``

    Returns:
        ISO date string (YYYY-MM-DD), or the original text if unparseable.
    """
    if date_text is None:
        return ""
    # Epoch millis (Genexus uses this)
    if isinstance(date_text, (int, float)):
        try:
            return datetime.utcfromtimestamp(date_text / 1000).date().isoformat()
        except (OSError, ValueError, OverflowError):
            return str(date_text)

    date_text = str(date_text).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(date_text, fmt).date().isoformat()
        except ValueError:
            continue
    return date_text


# ---------------------------------------------------------------------------
# Serialized JSON parser (S5 Django fixture format)
# ---------------------------------------------------------------------------

def _get_model_fields(data, model_name):
    """Return the ``fields`` dict from the first object matching *model_name*.

    Args:
        data: List of Django fixture objects (``[{model, pk, fields}, …]``).
        model_name: e.g. ``'rundb.experiment'``.

    Returns:
        dict of field values, or ``{}`` if not found.
    """
    for obj in data:
        if obj.get("model") == model_name:
            return obj.get("fields", {})
    return {}


def _count_model_objects(data, model_name):
    return sum(1 for obj in data if obj.get("model") == model_name)


def parse_serialized_json(json_path):
    """Parse a serialized (S5) Django-fixture JSON and extract run data.

    Reads the array of ``{model, pk, fields}`` objects and collects
    fields from the relevant models (experiment, plannedexperiment,
    analysismetrics, libmetrics, qualitymetrics, and sample).

    Args:
        json_path: Path to the ``serialized_*.json`` file.

    Returns:
        dict with all extracted run metadata and QC values.
    """
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array, got {type(data).__name__}")

    exp = _get_model_fields(data, "rundb.experiment")
    plan = _get_model_fields(data, "rundb.plannedexperiment")
    am = _get_model_fields(data, "rundb.analysismetrics")
    lm = _get_model_fields(data, "rundb.libmetrics")
    qm = _get_model_fields(data, "rundb.qualitymetrics")
    num_samples = _count_model_objects(data, "rundb.sample")

    # ---- Run info fields ----
    run_id = plan.get("planDisplayedName") or plan.get("planName") or ""
    run_folder = exp.get("expName", "")
    day_id = normalize_day_id(exp.get("date"))
    instrument_id = exp.get("pgmName", "")
    chip_type = exp.get("chipType", "")
    flows = exp.get("flows", 0)

    # Build chemistry ID from chip type + flows (e.g. "ION_530_200" for chipType "ION_530" and 200 flows)
    chemistry_id = (
        f"{chip_type}_{flows}" if chip_type and flows else chip_type
    )

    # ---- QC metrics ----
    loading = am.get("loading")
    addressavailable = am.get("adjusted_addressable")
    total_bases = qm.get("q0_bases")
    total_num_reads = lm.get("totalNumReads")
    total_mapped_reads = lm.get("total_mapped_reads")
    q20_mean_read_length = qm.get("q20_mean_read_length")

    result = {
        # Run info fields
        "run_id": run_id,
        "run_folder": run_folder,
        "day_id": day_id,
        "instrument_id": instrument_id,
        "platform_id": CONFIG.get("platform_id", "THERMOFISHER"),
        "sequencing_chemistry_id": chemistry_id,
        "num_cycles": flows,
        "num_samples": num_samples,
        # Raw extracted fields (for logging / extra context)
        "chipType": chip_type,
        "pgmName": instrument_id,
        "expName": run_folder,
        # Metric values (keyed for metric_id_map lookup)
        "loading": loading,
        "total_bases": total_bases,
        "totalNumReads": total_num_reads,
        "q20_mean_read_length": q20_mean_read_length,
        # Additional QC values (not in metric_id_map but useful)
        "total_mapped_reads": total_mapped_reads,
        "addressavailable": addressavailable
    }
    return result


# ---------------------------------------------------------------------------
# Experiment-graph JSON parser (Genexus Plan format)
# ---------------------------------------------------------------------------

def parse_plan_json(json_path):
    """Parse a Genexus experiment-graph (Plan) JSON and extract run data.

    The Plan JSON is a flat object with top-level run metadata and nested
    ``chipMetrics``, ``experimentChips``, ``experimentKits``, and
    per-result ``resultsQcs`` arrays.

    Args:
        json_path: Path to the ``Plan_*.json`` file.

    Returns:
        dict with all extracted run metadata and QC values.
    """
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object (Plan format), got {type(data).__name__}")

    # ---- Run info ----
    run_id = data.get("planName") or data.get("displayName") or ""
    run_folder = data.get("expName", "")
    day_id = normalize_day_id(data.get("executionDate") or data.get("resultDate"))
    instrument_id = data.get("pgmName", "")
    flows = data.get("flows", 0)

    # Chemistry ID from chipType (Genexus Plan files have no flowcell/reagent)
    chip_type = data.get("chipType", "")
    chemistry_id = chip_type or None

    # ---- chipMetrics (run-level QC) ----
    cm = {}
    chip_metrics_list = data.get("chipMetrics", [])
    if chip_metrics_list:
        cm = chip_metrics_list[0]

    loading = None
    total_num_reads = cm.get("filteredLibraryReads")
    total_bases = cm.get("totalBases")
    total_addressable = cm.get("totalAddressableWells")
    wells_with_isp = cm.get("wellsWithISP")
    if total_addressable and wells_with_isp:
        loading = round((wells_with_isp / total_addressable) * 100, 4)

    # Genexus chipMetrics does not provide per-read Q20 data
    q20_mean_read_length = None

    # Count planned samples from chipMetrics barcode data
    num_samples = 0
    barcode_data_str = cm.get("plannedBarcodesReadData", "")
    if barcode_data_str:
        try:
            barcode_data = json.loads(barcode_data_str) if isinstance(barcode_data_str, str) else barcode_data_str
            num_samples = len(barcode_data)
        except (json.JSONDecodeError, TypeError):
            pass

    result = {
        # Run info fields
        "run_id": run_id,
        "run_folder": run_folder,
        "day_id": day_id,
        "instrument_id": instrument_id,
        "platform_id": CONFIG.get("platform_id", "THERMOFISHER"),
        "sequencing_chemistry_id": chemistry_id,
        "num_cycles": flows,
        "num_samples": num_samples,
        # Raw fields
        "chipType": chip_type,
        "pgmName": instrument_id,
        "expName": run_folder,
        # Metric values
        "loading": loading,
        "totalNumReads": total_num_reads,
        "q20_mean_read_length": q20_mean_read_length,
        "addressavailable": total_addressable,
        # Additional QC
        "total_mapped_reads": None,
        "total_bases": total_bases,
    }
    return result


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def detect_format(json_path):
    """Detect the JSON export format (serialized vs Plan).

    A serialized file is a JSON array whose first element has a ``model``
    key.  A Plan file is a JSON object with a top-level ``chipMetrics``
    or ``experimentChips`` key.

    Args:
        json_path: Path to the JSON file.

    Returns:
        ``'serialized'`` or ``'plan'``.

    Raises:
        ValueError: If the format cannot be determined.
    """
    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list) and data and "model" in data[0]:
        return "serialized"
    if isinstance(data, dict) and ("chipMetrics" in data or "experimentChips" in data):
        return "plan"
    raise ValueError(f"Unrecognised JSON format in {json_path}")


def parse_json_file(json_path, instrument_model=None):
    """Auto-detect format and parse a ThermoFisher JSON export.

    When *instrument_model* is provided it forces the parser choice:
      - ``S5``      → serialized Django-fixture parser
      - ``GENEXUS`` → experiment-graph (Plan) parser

    Otherwise the format is auto-detected from the JSON structure.

    Args:
        json_path: Path to a serialized or Plan JSON file.
        instrument_model: Optional hint (``'S5'`` or ``'GENEXUS'``).

    Returns:
        dict with extracted run data and QC metrics.
    """
    if instrument_model:
        model_upper = instrument_model.upper()
        if model_upper == "S5":
            logging.info("Instrument model '%s' → serialized parser", instrument_model)
            return parse_serialized_json(json_path)
        elif model_upper == "GENEXUS":
            logging.info("Instrument model '%s' → plan parser", instrument_model)
            return parse_plan_json(json_path)
        else:
            logging.warning(
                "Unknown instrument model '%s'; falling back to auto-detection.",
                instrument_model,
            )

    fmt = detect_format(json_path)
    logging.info("Auto-detected format '%s' for %s", fmt, json_path)
    if fmt == "serialized":
        return parse_serialized_json(json_path)
    return parse_plan_json(json_path)


# ---------------------------------------------------------------------------
# CSV writers (match Illumina parser output format)
# ---------------------------------------------------------------------------

def _round_metrics(metrics):
    """Round all numeric values to 4 decimal places.

    Args:
        metrics: dict of extracted run data.

    Returns:
        New dict with rounded numeric values.
    """
    rounded = {}
    for key, value in metrics.items():
        if isinstance(value, float):
            rounded[key] = round(value, 4)
        else:
            rounded[key] = value
    return rounded


def write_sequencing_info(metrics, output_path):
    """Write run-level sequencing information to a single-row CSV.

    Columns are defined by CONFIG ``fields.sequencing_info``.

    Args:
        metrics: Flat dict with run metadata.
        output_path: pathlib.Path where the CSV will be written.
    """
    fieldnames = CONFIG["fields"]["sequencing_info"]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = _round_metrics(metrics)
    row = {key: payload.get(key) for key in fieldnames}
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def write_metrics_csv(metrics, output_path):
    """Write per-metric rows to a sequencing-metrics CSV.

    Each numeric metric in the metrics dict that matches a key in
    CONFIG ``metric_id_map`` is written as a row with columns:
    run_id, day_id, metric_id, value_number.

    Args:
        metrics: Flat dict with QC values.
        output_path: pathlib.Path where the CSV will be written.
    """
    payload = _round_metrics(metrics)
    run_id = payload.get("run_id")
    day_id = payload.get("day_id")
    fieldnames = CONFIG["fields"]["sequencing_metrics"]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        metric_map = CONFIG.get("metric_id_map", {})
        known_ids = set(metric_map.values())
        for key, value in payload.items():
            metric_id = metric_map.get(key) or (key if key in known_ids else None)
            if not metric_id:
                continue
            if not isinstance(value, (int, float)):
                continue
            writer.writerow({
                "run_id": run_id,
                "day_id": day_id,
                "metric_id": metric_id,
                "value_number": value,
            })


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """CLI entry point: parse a ThermoFisher JSON export and write CSVs.

    Usage::

        python ThermoFisher_sequencing_data_parser.py \\
            --json-file <path_to_json> \\
            --output-dir <output_directory> \\
            [--run-description "..."] \\
            [--log DEBUG|INFO|WARNING|ERROR] \\
            [--log-file parser.log]
    """
    parser = argparse.ArgumentParser(
        description="Parse ThermoFisher / Ion Torrent JSON exports into IlluQC-compatible CSVs."
    )
    parser.add_argument(
        "--json-file",
        required=True,
        help="Path to the Ion Torrent JSON file (serialized_*.json or Plan_*.json).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where sequencing-info and sequencing-metrics CSVs are written.",
    )
    parser.add_argument(
        "--run-description",
        default="",
        help="Run description to include in the sequencing-info CSV.",
    )
    parser.add_argument(
        "--instrument-model",
        default=None,
        choices=["S5", "GENEXUS"],
        help="Force a specific parser: S5 (serialized) or GENEXUS (Plan). Auto-detected if omitted.",
    )
    parser.add_argument(
        "--log",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Optional log file path.",
    )

    if len(os.sys.argv) == 1:
        parser.print_help()
        return
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log.upper(),
        format="%(levelname)s:%(message)s",
        filename=args.log_file,
    )

    global CONFIG
    CONFIG = load_config()

    # Parse
    json_path = args.json_file
    if not os.path.isfile(json_path):
        logging.error("File not found: %s", json_path)
        return

    metrics = parse_json_file(json_path, instrument_model=args.instrument_model)
    metrics["run_description"] = args.run_description or ""

    run_id = metrics.get("run_id", "unknown")
    logging.info("Parsed metrics for run %s", run_id)
    logging.info(
        "Run metadata: day_id=%s, instrument=%s, chip=%s, platform=%s",
        metrics.get("day_id"),
        metrics.get("instrument_id"),
        metrics.get("chipType"),
        metrics.get("platform"),
    )

    # Write output CSVs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    info_path = output_dir / f"{run_id}{CONFIG['output_suffixes']['sequencing_info']}"
    metrics_path = output_dir / f"{run_id}{CONFIG['output_suffixes']['sequencing_metrics']}"

    write_sequencing_info(metrics, info_path)
    write_metrics_csv(metrics, metrics_path)

    logging.info("Wrote sequencing info to %s", info_path)
    logging.info("Wrote sequencing metrics to %s", metrics_path)


if __name__ == "__main__":
    main()
