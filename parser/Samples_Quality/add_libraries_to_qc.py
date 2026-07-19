#!/usr/bin/env python3
"""Enriches sample QC metrics CSV with library_id from sample_libraries.txt mapping file."""

import argparse
import csv
import logging
import os
import sys


def load_library_mapping(library_file):
    """Load sample_id -> library_id mapping from sample_libraries.txt file.
    
    Args:
        library_file: Path to sample_libraries.txt (tab-delimited: sample_id\\tlibrary_id\\trun_id)
    
    Returns:
        dict mapping sample_id -> library_id
    """
    mapping = {}
    try:
        with open(library_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                if row.get('sample_id') and row.get('library_id'):
                    sample_id = row['sample_id'].strip()
                    library_id = row['library_id'].strip()
                    mapping[sample_id] = library_id
        return mapping
    except FileNotFoundError:
        logging.warning("Library mapping file not found: {}".format(library_file))
        return {}
    except Exception as e:
        logging.error("Error loading library mapping from {}: {}".format(library_file, e))
        return {}


def enrich_qc_metrics(input_csv, output_csv, library_file, logger):
    """Enrich sample QC metrics CSV with library_id from mapping file.
    
    Args:
        input_csv: Path to input QC metrics CSV (sample_id, run_id, read, metric_id, value_number)
        output_csv: Path to output enriched CSV (adds library_id column)
        library_file: Path to sample_libraries.txt mapping file
        logger: Logger instance
    """
    library_mapping = load_library_mapping(library_file)
    
    if not library_mapping:
        logger.error("No library mappings loaded from {}".format(library_file))
        return False
    
    logger.info("Loaded {} sample->library mappings".format(len(library_mapping)))
    
    try:
        with open(input_csv, 'r') as infile, \
             open(output_csv, 'w') as outfile:
            
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames or []
            
            # Ensure library_id is in the output
            if 'library_id' not in fieldnames:
                fieldnames = list(fieldnames)
                # Insert library_id after sample_id for logical grouping
                if 'sample_id' in fieldnames:
                    idx = fieldnames.index('sample_id')
                    fieldnames.insert(idx + 1, 'library_id')
                else:
                    fieldnames.append('library_id')
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            missing_library = 0
            enriched = 0
            
            for row in reader:
                sample_id = row.get('sample_id', '').strip()
                
                # Look up library_id from mapping
                if sample_id in library_mapping:
                    row['library_id'] = library_mapping[sample_id]
                    enriched += 1
                elif sample_id.lower() == 'undetermined':
                    # For undetermined samples, leave library_id empty
                    row['library_id'] = None
                    enriched += 1
                else:
                    logger.warning("No library mapping found for sample_id: {}".format(sample_id))
                    row['library_id'] = None
                    missing_library += 1
                
                writer.writerow(row)
        
        logger.info("Enriched {} rows with library_id".format(enriched))
        if missing_library > 0:
            logger.warning("Could not find library_id for {} samples".format(missing_library))
        
        logger.info("Output written to {}".format(output_csv))
        return True
    
    except Exception as e:
        logger.error("Error enriching QC metrics: {}".format(e))
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Enrich sample QC metrics CSV with library_id from sample_libraries.txt mapping"
    )
    
    parser.add_argument(
        '--input-csv',
        required=True,
        help='Path to input QC metrics CSV file'
    )
    
    parser.add_argument(
        '--output-csv',
        required=True,
        help='Path to output enriched CSV file'
    )
    
    parser.add_argument(
        '--library-file',
        required=True,
        help='Path to sample_libraries.txt mapping file (tab-delimited: sample_id\\tlibrary_id\\trun_id)'
    )
    
    parser.add_argument(
        '--log',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        default=None,
        help='Path to log file (default: stderr)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log.upper())
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    if args.log_file:
        logging.basicConfig(
            level=log_level,
            format=log_format,
            filename=args.log_file
        )
    else:
        logging.basicConfig(
            level=log_level,
            format=log_format
        )
    
    logger = logging.getLogger(__name__)
    
    # Validate inputs
    if not os.path.exists(args.input_csv):
        logger.error("Input CSV file not found: {}".format(args.input_csv))
        return 2
    
    if not os.path.exists(args.library_file):
        logger.error("Library mapping file not found: {}".format(args.library_file))
        return 2
    
    # Enrich the QC metrics
    if enrich_qc_metrics(args.input_csv, args.output_csv, args.library_file, logger):
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
