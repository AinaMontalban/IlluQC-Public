
"""Parser that extracts sample metadata from a tab-delimited file and writes CSV ready for database upload."""

import argparse
import csv
import logging
import sys


def parse_sample_metadata(input_file, output_file, logger):
    """Parse sample metadata from input file and write to CSV.
    
    Args:
        input_file: Path to input tab-delimited file
        output_file: Path to output CSV file
        logger: Logger instance
    """
    try:
        with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
            reader = csv.reader(infile, delimiter='\t')
            writer = csv.writer(outfile)

            # Write the header for the output CSV
            writer.writerow(['sample_id', 'sex'])
            
            row_count = 0
            for row in reader:
                if len(row) >= 2:  # Ensure there are enough columns
                    sample_id = row[0]  
                    sex = row[1]
                    writer.writerow([sample_id, sex])
                    row_count += 1
            
            logger.info(f"Successfully parsed {row_count} samples from {input_file}")
            logger.info(f"Output written to {output_file}")
    
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error parsing sample metadata: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Parse sample metadata from tab-delimited file and write CSV for database upload"
    )
    
    parser.add_argument(
        '--input-file',
        required=True,
        help='Path to the input tab-delimited sample metadata file'
    )
    
    parser.add_argument(
        '--output-file',
        required=True,
        help='Path to the output CSV file'
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
    
    # Parse the metadata
    parse_sample_metadata(args.input_file, args.output_file, logger)


if __name__ == '__main__':
    main()