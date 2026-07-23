#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create <RUN>_sample_libraries.txt from run_samples_servolab.txt.

Takes a run_samples_servolab.txt file, extracts sample IDs, and creates
a sample-to-library mapping file with the given library ID assigned to all samples.

Usage
-----
    python create_sample_library_mapping.py \\
        /path/to/run_samples_servolab.txt \\
        --run-id R25_0552 \\
        --library-id LIB_A \\
        --output /path/to/output/R25_0552_sample_libraries.txt

Or with auto-detection of run_id from folder path:
    python create_sample_library_mapping.py \\
        /path/to/Illumina_Runs_Data/R25_0552/run_samples_servolab.txt \\
        --library-id LIB_A
"""

import argparse
import csv
import re
import os


def extract_run_id_from_path(file_path):
    """Extract run ID from folder path."""
    parts = file_path.split(os.sep)
    run_pattern = re.compile(r'^(RUN_\d+|R\d+_\d+)$')
    for part in reversed(parts):
        if run_pattern.match(part):
            return part
    return None


def extract_sample_ids(servolab_file):
    """Read run_samples_servolab.txt and extract sample IDs from first column."""
    sample_ids = []
    with open(servolab_file, 'r') as fh:
        reader = csv.reader(fh, delimiter='\t')
        for row in reader:
            if row:
                sample_id = row[0].strip()
                if sample_id:
                    sample_ids.append(sample_id)
    return sample_ids


def create_sample_libraries_file(sample_ids, run_id, library_id, output_path):
    """Create <RUN>_sample_libraries.txt with sample-to-library mapping."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=['sample_id', 'library_id', 'run_id'],
            delimiter='\t'
        )
        writer.writeheader()
        for sample_id in sample_ids:
            writer.writerow({
                'sample_id': sample_id,
                'library_id': library_id,
                'run_id': run_id,
            })
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Create sample-to-library mapping file from run_samples_servolab.txt"
    )
    parser.add_argument(
        'servolab_file',
        help='Path to run_samples_servolab.txt file'
    )
    parser.add_argument(
        '--run-id',
        default=None,
        help='Run ID (e.g. R25_0552). If not provided, auto-detect from folder path.'
    )
    parser.add_argument(
        '--library-id',
        required=True,
        help='Library ID to assign to all samples (e.g. LIB_A)'
    )
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path. If not provided, use <run_id>_sample_libraries.txt in same directory as input.'
    )
    
    args = parser.parse_args()
    
    # Auto-detect run_id from path if not provided
    run_id = args.run_id or extract_run_id_from_path(args.servolab_file)
    if not run_id:
        parser.error("Could not auto-detect run_id. Please provide --run-id explicitly.")
    
    # Check if input file exists
    servolab_path = args.servolab_file
    if not os.path.exists(servolab_path):
        parser.error("Input file not found: " + str(servolab_path))
    
    # Extract sample IDs
    print("Reading samples from " + os.path.abspath(servolab_path))
    try:
        sample_ids = extract_sample_ids(servolab_path)
    except Exception as e:
        parser.error("Error reading samples: " + str(e))
    
    print("Found {} samples".format(len(sample_ids)))
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_dir = os.path.dirname(servolab_path)
        output_path = os.path.join(output_dir, "{}_sample_libraries.txt".format(run_id))
    
    # Create output file
    print("Creating {}...".format(output_path))
    output_file = create_sample_libraries_file(sample_ids, run_id, args.library_id, output_path)
    print("✓ Created {}".format(output_file))


if __name__ == "__main__":
    main()
