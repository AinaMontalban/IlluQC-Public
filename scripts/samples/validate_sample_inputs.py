#!/usr/bin/env python3
"""Validate run-scoped sample metadata, MultiQC, and library mappings."""

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path


FASTQ_SUFFIX = re.compile(r"_S\d+(_L\d+)?_R[12]_\d+$")


def sample_base_name(value):
    return FASTQ_SUFFIX.sub("", value.strip())


def read_metadata(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows:
        return [], {}, ["metadata file is empty"]
    if rows[0] and rows[0][0].strip().lower() == "sample_id":
        header = [value.strip().lower() for value in rows[0]]
        sample_idx = header.index("sample_id")
        sex_idx = header.index("sex") if "sex" in header else None
        data = rows[1:]
    else:
        sample_idx, sex_idx, data = 0, 1, rows
    ids, sex, errors = [], {}, []
    for number, row in enumerate(data, start=2):
        if len(row) <= sample_idx or not row[sample_idx].strip():
            errors.append(f"metadata line {number}: missing sample_id")
            continue
        sample_id = row[sample_idx].strip()
        ids.append(sample_id)
        sex[sample_id] = row[sex_idx].strip() if sex_idx is not None and len(row) > sex_idx else ""
    return ids, sex, errors


def read_multiqc(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "Sample" not in reader.fieldnames:
            return [], ["MultiQC file has no 'Sample' column"]
        ids = [sample_base_name(row.get("Sample", "")) for row in reader]
    return [value for value in ids if value and not value.upper().startswith("UNDETERMINED")], []


def read_libraries(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"sample_id", "library_id"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return {}, ["library mapping must contain sample_id and library_id headers"]
        mapping = {}
        errors = []
        for number, row in enumerate(reader, start=2):
            sample_id = (row.get("sample_id") or "").strip()
            library_id = (row.get("library_id") or "").strip()
            if not sample_id or not library_id:
                errors.append(f"library mapping line {number}: sample_id/library_id is empty")
                continue
            if sample_id in mapping and mapping[sample_id] != library_id:
                errors.append(f"sample {sample_id} maps to multiple libraries")
            mapping[sample_id] = library_id
    return mapping, errors


def known_library_ids(path):
    if not path or not path.exists():
        return None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {
            (row.get("library_id") or "").strip()
            for row in csv.DictReader(handle)
            if (row.get("library_id") or "").strip()
        }


def duplicates(values):
    return sorted(value for value, count in Counter(values).items() if count > 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--multiqc", type=Path, required=True)
    parser.add_argument("--libraries", type=Path, required=True)
    parser.add_argument("--known-libraries", type=Path)
    parser.add_argument("--sample-id")
    args = parser.parse_args()

    errors, warnings = [], []
    for label, path in (("metadata", args.metadata), ("MultiQC", args.multiqc), ("library mapping", args.libraries)):
        if not path.is_file():
            errors.append(f"{label} file not found: {path}")
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1

    metadata_ids, sex_by_sample, metadata_errors = read_metadata(args.metadata)
    multiqc_ids, multiqc_errors = read_multiqc(args.multiqc)
    library_map, library_errors = read_libraries(args.libraries)
    errors.extend(metadata_errors + multiqc_errors + library_errors)

    metadata_set, multiqc_set = set(metadata_ids), set(multiqc_ids)
    target = {args.sample_id} if args.sample_id else metadata_set | multiqc_set

    if args.sample_id:
        if args.sample_id not in metadata_set:
            errors.append(f"sample {args.sample_id} is missing from metadata")
        if args.sample_id not in multiqc_set:
            errors.append(f"sample {args.sample_id} is missing from MultiQC")
    else:
        for sample_id in sorted(metadata_set - multiqc_set):
            errors.append(f"sample {sample_id} is present in metadata but missing from MultiQC")
        for sample_id in sorted(multiqc_set - metadata_set):
            errors.append(f"sample {sample_id} is present in MultiQC but missing from metadata")

    for sample_id in sorted(target):
        if not sex_by_sample.get(sample_id):
            errors.append(f"sample {sample_id} has no sex value")
        if sample_id not in library_map:
            errors.append(f"sample {sample_id} has no library mapping")

    for sample_id in duplicates(metadata_ids):
        errors.append(f"duplicate metadata sample: {sample_id}")

    known = known_library_ids(args.known_libraries)
    if known is None:
        warnings.append("known library CSV not found; library IDs were not cross-checked")
    else:
        for library_id in sorted({library_map[s] for s in target if s in library_map} - known):
            errors.append(f"unknown library_id: {library_id}")

    print(f"Run: {args.run_id}")
    print(f"Metadata samples: {len(metadata_set)}")
    print(f"MultiQC samples: {len(multiqc_set)}")
    print(f"Library mappings: {len(library_map)}")
    print(f"Requested scope: {args.sample_id or 'all samples'}")
    for message in warnings:
        print(f"WARNING: {message}")
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    if errors:
        print(f"Validation failed: {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Validation passed: {len(target)} sample(s) ready for preparation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
