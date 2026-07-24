#!/usr/bin/env python3
"""Convert semicolon-delimited sample metrics to IlluQC long-format CSV."""

import argparse
import csv
import logging
from pathlib import Path


SAMPLE_COLUMN = "sample"
METRIC_COLUMNS = (
    "length",
    "total_reads",
    "primary_reads",
    "prop_primary_reads",
    "secondary_reads",
    "prop_secondary_reads",
    "supplementary_reads",
    "prop_supplementary_reads",
    "duplicate_reads",
    "prop_duplicate_reads",
    "mapped_reads",
    "prop_mapped_reads",
    "mapped_good_reads",
    "prop_mapped_good_reads_of_mapped_reads",
    "prop_mapped_good_reads_of_total_reads",
    "ontarget_reads",
    "prop_ontarget_reads_of_mapped_good_reads",
    "prop_ontarget_reads_of_total_reads",
    "Cov_1X",
    "Cov_20X",
    "Cov_38X",
    "Cov_75X",
    "Cov_100X",
    "Cov_250X",
    "Cov_500X",
    "Cov_1000X",
    "Cov_2000X",
    "mean",
    "min",
    "max",
    "Coverage_Uniformity",
)
MISSING_VALUES = {"", "na", "n/a", "nan", "none", "."}


def parse_number(raw_value, row_number, column):
    """Parse a numeric cell, accepting percent signs and decimal commas."""
    value = raw_value.strip()
    if value.lower() in MISSING_VALUES:
        return None
    if value.endswith("%"):
        value = value[:-1].strip()
    if "," in value and "." not in value:
        value = value.replace(",", ".")
    try:
        return round(float(value), 4)
    except ValueError as error:
        raise ValueError(
            f"row {row_number}: non-numeric value {raw_value!r} in {column}"
        ) from error


def parse_sample_metrics(input_path, sample_filter=None):
    """Return long-format metric dictionaries from a wide metrics file."""
    metrics = []
    samples = set()
    with Path(input_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        fieldnames = reader.fieldnames or []
        missing_columns = [
            column for column in (SAMPLE_COLUMN, *METRIC_COLUMNS)
            if column not in fieldnames
        ]
        if missing_columns:
            raise ValueError(
                "missing required columns: " + ", ".join(missing_columns)
            )

        for row_number, row in enumerate(reader, start=2):
            sample_id = (row.get(SAMPLE_COLUMN) or "").strip()
            if not sample_id:
                raise ValueError(f"row {row_number}: sample cannot be empty")
            if sample_filter and sample_id != sample_filter:
                continue
            samples.add(sample_id)
            for column in METRIC_COLUMNS:
                number = parse_number(row.get(column) or "", row_number, column)
                if number is not None:
                    metrics.append(
                        {
                            "sample_id": sample_id,
                            "metric_id": column,
                            "value_number": number,
                        }
                    )
    return {"num_samples": len(samples), "sample_metrics": metrics}


def write_sample_metrics(output_path, run_id, metrics):
    """Write database-compatible long-format sample metric rows."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["sample_id", "run_id", "metric_id", "value_number"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(
                {
                    "sample_id": metric["sample_id"],
                    "run_id": run_id,
                    "metric_id": metric["metric_id"],
                    "value_number": metric["value_number"],
                }
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics_file", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sample-id", help="Only parse this sample")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--log", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=args.log.upper(), format="%(levelname)s: %(message)s")

    if not args.metrics_file.is_file():
        parser.error(f"metrics file not found: {args.metrics_file}")
    if args.output and args.output_dir:
        parser.error("use either --output or --output-dir, not both")

    try:
        result = parse_sample_metrics(args.metrics_file, args.sample_id)
    except ValueError as error:
        parser.error(str(error))
    if args.sample_id and not result["sample_metrics"]:
        parser.error(f"sample not found or has no numeric metrics: {args.sample_id}")

    output_path = args.output
    if output_path is None:
        output_dir = args.output_dir or args.metrics_file.resolve().parent
        stem = f"{args.run_id}-{args.sample_id}" if args.sample_id else args.run_id
        output_path = output_dir / f"{stem}-samples-qc-metrics.csv"
    write_sample_metrics(output_path, args.run_id, result["sample_metrics"])
    logging.info(
        "Parsed %d metrics for %d samples",
        len(result["sample_metrics"]),
        result["num_samples"],
    )
    logging.info("Wrote %s", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
