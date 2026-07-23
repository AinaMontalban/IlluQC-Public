
"""Parser that extracts sample metadata from a tab-delimited file and writes CSV ready for database upload."""

import argparse
import csv
import logging
import sys


def parse_sample_metadata(input_file, output_file, logger, sample_filter=None):
    """Parse sample metadata from input file and write to CSV.
    
    Args:
        input_file: Path to input tab-delimited file
        output_file: Path to output CSV file
        logger: Logger instance
    """
    try:
        with open(input_file, 'r', newline='', encoding='utf-8-sig') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            rows = list(csv.reader(infile, delimiter='\t'))
            writer = csv.writer(outfile)

            # Write the header for the output CSV
            writer.writerow(['sample_id', 'sex'])
            
            row_count = 0
            if rows and rows[0] and rows[0][0].strip().lower() == 'sample_id':
                header = [column.strip().lower() for column in rows[0]]
                sample_idx = header.index('sample_id')
                sex_idx = header.index('sex') if 'sex' in header else None
                data_rows = rows[1:]
            else:
                sample_idx = 0
                sex_idx = 1
                data_rows = rows

            for row in data_rows:
                if len(row) >= 2:  # Ensure there are enough columns
                    sample_id = row[sample_idx].strip()
                    if sample_filter and sample_id != sample_filter:
                        continue
                    sex = row[sex_idx].strip() if sex_idx is not None and len(row) > sex_idx else ''
                    writer.writerow([sample_id, sex])
                    row_count += 1
            
            logger.info(f"Successfully parsed {row_count} samples from {input_file}")
            logger.info(f"Output written to {output_file}")
            if sample_filter and row_count == 0:
                logger.error("Sample ID not found: %s", sample_filter)
                return False
            return True
    
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {input_file}")
        return False
    except Exception as e:
        logger.error(f"Error parsing sample metadata: {e}")
        return False


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

    parser.add_argument(
        '--sample-id',
        default=None,
        help='Only write the row matching this sample ID'
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
    if not parse_sample_metadata(
        args.input_file,
        args.output_file,
        logger,
        sample_filter=args.sample_id,
    ):
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
