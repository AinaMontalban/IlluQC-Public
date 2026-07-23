#!/usr/bin/env python3
"""
MultiQC General Stats Parser — Long-format per-sample QC metric extractor.

Reads a MultiQC general statistics file (multiqc_general_stats.txt) and
produces a long-format CSV compatible with the IlluQC database schema:

  {run_id}-samples-qc-metrics.csv    — one row per sample × read × metric

Each FASTQ file row in the input (R1 / R2) becomes a separate set of
metric rows, identified by ``sample_id`` + ``read`` (R1 or R2).

Usage
-----
    python multiqc_data_parser.py \\
        multiqc_general_stats.txt \\
        --run-id R25_0806 \\
        --format csv \\
        --output-dir /path/to/output

Dependencies: Python ≥ 3.9 (stdlib only — no third-party packages).
"""

import argparse
import csv
import json
import logging
import os
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: extract sample base name from FASTQ sample name
# ---------------------------------------------------------------------------

_FASTQ_SUFFIX_RE = re.compile(r"_S\d+(_L\d+)?_R([12])_\d+$")


def sample_base_name(sample) :
    """Strip Illumina FASTQ suffixes (e.g. _S1_L001_R1_001) → base sample ID."""
    return _FASTQ_SUFFIX_RE.sub("", sample)


def detect_read(sample):
    """Return 'R1' or 'R2' based on the FASTQ filename pattern, or '' if unknown."""
    m = _FASTQ_SUFFIX_RE.search(sample)
    return f"R{m.group(2)}" if m else ""


# ---------------------------------------------------------------------------
# Core: load config
# ---------------------------------------------------------------------------
def load_config(config_path):
    """Load the JSON parser configuration file."""
    with open(config_path) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Core: parse the multiqc_general_stats.txt file (per-sample)
# ---------------------------------------------------------------------------
def parse_multiqc_general_stats(
    stats_path,
    config,
    sample_filter=None,
):
    """
    Parse *multiqc_general_stats.txt* and return per-sample metrics.

    Parameters
    ----------
    stats_path : path to the tab-separated multiqc_general_stats.txt file.
    config     : parsed JSON config (must contain ``metric_id_map``).

    Returns
    -------
    dict with keys:
        ``num_samples``    – unique biological sample count (R1+R2 merged)
        ``sample_metrics`` – list of dicts, each with:
            sample_id, read, metric_id, value_number
    """
    metric_id_map: dict = config["metric_id_map"]

    sample_metrics: list[dict] = []
    sample_names: set[str] = set()

    with open(stats_path, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for row in reader:
            raw_sample = row.get("Sample", "")
            sample_id = sample_base_name(raw_sample)
            read = detect_read(raw_sample)

            if sample_filter and sample_id != sample_filter:
                continue
            
            # Skip undetermined samples (they won't have library_id)
            if sample_id.upper().startswith("UNDETERMINED"):
                continue
            
            sample_names.add(sample_id)

            for col, metric_id in metric_id_map.items():
                val = row.get(col, "")
                if val == "":
                    continue
                try:
                    # Concatenate metric_id with read (e.g., FASTQC_AVG_SEQUENCE_LENGTH_R1)
                    combined_metric_id = metric_id + "_" + read if read else metric_id
                    logging.debug(
                        "Adding metric: sample_id=%s, read=%s, metric_id=%s, value_number=%s",
                        sample_id, read, combined_metric_id, val,
                    )
                    sample_metrics.append({
                        "sample_id": sample_id,
                        "metric_id": combined_metric_id,
                        "value_number": round(float(val), 4),
                    })
                except (ValueError, TypeError):
                    logging.debug("Non-numeric value '%s' in column '%s'", val, col)

    return {
        "num_samples": len(sample_names),
        "sample_metrics": sample_metrics,
    }


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_sample_qc_metrics(
    run_id,
    sample_metrics,
    output_path,
):
    """Write the long-format sample-qc-metrics CSV (one row per sample × metric with read in metric_id)."""
    fieldnames = ["sample_id", "run_id", "metric_id", "value_number"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in sample_metrics:
            writer.writerow({
                "sample_id": row["sample_id"],
                "run_id": run_id,
                "metric_id": row["metric_id"],
                "value_number": row["value_number"],
            })


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Parse MultiQC general stats into long-format CSVs."
    )
    parser.add_argument(
        "fastqc_file",
        help="Path to the multiqc_general_stats.txt file.",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier (e.g. R25_0806).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to multiqc_parser_config.json (defaults to same directory as this script).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (json or csv).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for output CSVs (defaults to the directory of the input file).",
    )
    parser.add_argument(
        "--log",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    parser.add_argument(
        "--sample-id",
        default=None,
        help="Only parse metrics for this normalized sample ID.",
    )

    if len(os.sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    logging.basicConfig(level=args.log.upper(), format="%(levelname)s: %(message)s")

    # ── Resolve paths ──────────────────────────────────────────────
    fastqc_path = Path(args.fastqc_file)
    if not fastqc_path.exists():
        logging.error("File not found: %s", fastqc_path)
        return

    script_dir = Path(__file__).resolve().parent
    config_path = Path(args.config) if args.config else script_dir / "multiqc_parser_config.json"
    config = load_config(config_path)
    logging.debug("Loaded config from %s", config_path)

    # ── Parse ──────────────────────────────────────────────────────
    result = parse_multiqc_general_stats(
        fastqc_path,
        config,
        sample_filter=args.sample_id,
    )
    run_id = args.run_id
    num_samples = result["num_samples"]
    sample_metrics = result["sample_metrics"]

    if args.sample_id and not sample_metrics:
        logging.error("Sample ID not found in MultiQC statistics: %s", args.sample_id)
        return 2

    logging.info("Parsed %d sample-metric rows for run %s", len(sample_metrics), run_id)
    logging.info("Detected %d samples", num_samples)

    # ── Output ─────────────────────────────────────────────────────
    if args.format == "csv":
        output_dir = Path(args.output_dir) if args.output_dir else fastqc_path.resolve().parent
        suffixes = config.get("output_suffixes", {})

        output_stem = f"{run_id}-{args.sample_id}" if args.sample_id else run_id
        sample_path = output_dir / f"{output_stem}{suffixes.get('sample_qc_metrics', '-samples-qc-metrics.csv')}"

        write_sample_qc_metrics(
            run_id=run_id,
            sample_metrics=sample_metrics,
            output_path=sample_path,
        )
        logging.info("Wrote sample QC metrics     → %s", sample_path)
    else:
        # JSON output (stdout or file)
        payload = {
            "run_id": run_id,
            "num_samples": num_samples,
            "sample_metrics": sample_metrics,
        }
        print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
