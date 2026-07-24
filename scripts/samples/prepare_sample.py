#!/usr/bin/env python3
"""Prepare load-ready files for one sample from CLI metadata and metric files."""

import argparse
import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "parser" / "MultiQC"))
sys.path.insert(0, str(REPO_ROOT / "parser" / "Sample_Metrics"))
from multiqc_data_parser import parse_multiqc_general_stats  # noqa: E402
from sample_metrics_parser import (  # noqa: E402
    METRIC_COLUMNS,
    parse_sample_metrics,
)


def parse_metrics_file(path, config, sample_id):
    """Parse a supported metrics file after inspecting its header."""
    with path.open(encoding="utf-8-sig") as handle:
        first_line = handle.readline().rstrip("\r\n")
    semicolon_header = {
        column.strip() for column in first_line.split(";") if column.strip()
    }
    if {"sample", *METRIC_COLUMNS}.issubset(semicolon_header):
        return parse_sample_metrics(path, sample_filter=sample_id)
    return parse_multiqc_general_stats(path, config, sample_filter=sample_id)


def known_library_ids(path):
    if not path.is_file():
        return None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {
            (row.get("library_id") or "").strip()
            for row in csv.DictReader(handle)
            if (row.get("library_id") or "").strip()
        }


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def remove_generated_directory(path, scope):
    """Remove a generated directory without following symlinks or leaving scope."""
    resolved_path = path.resolve()
    resolved_scope = scope.resolve()
    if resolved_path == resolved_scope or resolved_scope not in resolved_path.parents:
        raise ValueError(f"refusing to remove path outside sample scope: {path}")
    if path.is_symlink():
        path.unlink()
        return
    for child in path.iterdir():
        if child.is_symlink() or child.is_file():
            child.unlink()
        elif child.is_dir():
            remove_generated_directory(child, scope)
        else:
            child.unlink()
    path.rmdir()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("sample_id")
    parser.add_argument("--sex", required=True)
    parser.add_argument("--library-id", required=True)
    parser.add_argument("--clinical-method")
    parser.add_argument("--sample-type")
    parser.add_argument(
        "--metrics-file", "--metrics", dest="metric_files", action="append",
        type=Path, required=True,
        help="MultiQC TSV or semicolon sample-metrics CSV; repeat for additional files",
    )
    parser.add_argument(
        "--processed-data-dir", type=Path, required=True, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--known-libraries", type=Path, required=True, help=argparse.SUPPRESS
    )
    parser.add_argument("--config", type=Path, required=True, help=argparse.SUPPRESS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    for value, label in ((args.run_id, "RUN_ID"), (args.sample_id, "SAMPLE_ID")):
        if not value or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for char in value):
            parser.error(f"{label} may contain only letters, numbers, dot, underscore, and hyphen")
    if not args.sex.strip():
        parser.error("--sex cannot be empty")
    if not args.library_id.strip():
        parser.error("--library-id cannot be empty")
    for path in args.metric_files:
        if not path.is_file():
            parser.error(f"metrics file not found: {path}")
    if not args.config.is_file():
        parser.error(f"metric parser configuration not found: {args.config}")

    libraries = known_library_ids(args.known_libraries)
    if libraries is None:
        print(f"WARNING: library catalogue not found; library ID was not cross-checked: {args.known_libraries}")
    elif args.library_id not in libraries:
        parser.error(f"unknown library_id: {args.library_id}")

    with args.config.open(encoding="utf-8") as handle:
        config = json.load(handle)

    metrics = {}
    sources = {}
    for metric_file in args.metric_files:
        try:
            parsed = parse_metrics_file(metric_file, config, args.sample_id)
        except ValueError as error:
            parser.error(f"invalid metrics file {metric_file}: {error}")
        for row in parsed["sample_metrics"]:
            metric_id = row["metric_id"]
            value = row["value_number"]
            if metric_id in metrics and metrics[metric_id] != value:
                parser.error(
                    f"conflicting values for {metric_id} in {sources[metric_id]} and {metric_file}"
                )
            metrics[metric_id] = value
            sources[metric_id] = metric_file
    if not metrics:
        parser.error(f"sample {args.sample_id} was not found, or had no configured metrics")

    scope = args.processed_data_dir / "Samples_Data" / args.run_id / "samples" / args.sample_id
    ready = scope / "load-ready"
    staging = scope / f".load-ready-staging-{args.sample_id}"
    if (ready.exists() or ready.is_symlink()) and not args.force:
        parser.error(f"load-ready output exists: {ready}; review it and use --force to replace it")
    if staging.exists() or staging.is_symlink():
        remove_generated_directory(staging, scope)
    staging.mkdir(parents=True)

    sample_row = {
        "sample_id": args.sample_id,
        "sex": args.sex.strip(),
        "clinical_method": (args.clinical_method or "").strip(),
        "sample_type": (args.sample_type or "").strip(),
    }
    write_csv(staging / "samples.csv", list(sample_row), [sample_row])
    qc_rows = [
        {
            "sample_id": args.sample_id,
            "library_id": args.library_id,
            "run_id": args.run_id,
            "metric_id": metric_id,
            "value_number": value,
        }
        for metric_id, value in sorted(metrics.items())
    ]
    write_csv(
        staging / "sample-qc-metrics.csv",
        ["sample_id", "library_id", "run_id", "metric_id", "value_number"],
        qc_rows,
    )

    if ready.exists() or ready.is_symlink():
        remove_generated_directory(ready, scope)
    staging.rename(ready)
    summary = [
        f"Run: {args.run_id}",
        f"Sample: {args.sample_id}",
        "Metadata source: command-line parameters",
        f"Library: {args.library_id}",
        "Metric sources:",
        *(f"- {path.resolve()}" for path in args.metric_files),
        f"Metric rows: {len(qc_rows)}",
        f"Load-ready directory: {ready}",
    ]
    scope.mkdir(parents=True, exist_ok=True)
    (scope / "preparation-summary.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"Prepared sample {args.sample_id}: {len(qc_rows)} metric rows")
    print(f"Load-ready directory: {ready}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
