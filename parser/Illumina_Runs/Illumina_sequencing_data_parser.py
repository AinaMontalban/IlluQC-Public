
import argparse
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import os
from interop import py_interop_run_metrics, py_interop_run, py_interop_summary

CONFIG_PATH = Path(__file__).with_name("illumina_parser_config.json")
CONFIG = {}

def load_config(path=CONFIG_PATH):
    """Load the parser configuration from a JSON file.

    Args:
        path: Path to the JSON config file. Defaults to
              ``illumina_parser_config.json`` next to this script.

    Returns:
        dict with configuration keys (platform_id, metric_id_map,
        samplesheet, output_suffixes, fields).

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

# Function to normalize date formats to ISO format (YYYY-MM-DD)
def normalize_day_id(date_text):
	"""Normalize a date string to ISO 8601 format (YYYY-MM-DD).

	Accepts common Illumina date formats: YYMMDD, YYYYMMDD, YYYY-MM-DD.
	Returns the original text unchanged if none of the formats match.

	Args:
		date_text: Raw date string from RunInfo.xml.

	Returns:
		ISO-formatted date string, or the original text if unparseable.
	"""
	if not date_text:
		return ""
	date_text = date_text.strip()
	for fmt in ("%y%m%d", "%Y%m%d", "%Y-%m-%d"):
		try:
			return datetime.strptime(date_text, fmt).date().isoformat()
		except ValueError:
			continue
	return date_text


# Function to read XML and return root element
def read_xml(path):
	"""Parse an XML file and return its root element.

	Args:
		path: File-system path to the XML file.

	Returns:
		xml.etree.ElementTree.Element: Root element of the parsed tree.
	"""
	tree = ET.parse(path)
	return tree.getroot()

# Function to parse run info XML
def parse_run_info(run_info_path):
    """Extract run-level identifiers from RunInfo.xml via the InterOp library.

    Uses ``py_interop_run.info()`` to read the binary RunInfo and exposes
    instrument name, date, run ID, and total cycle count.

    Args:
        run_info_path: Path to RunInfo.xml (or the folder containing it).

    Returns:
        dict with keys: run_id, instrument_id, day_id, num_cycles.
    """

    ### Run Info metrics
    run_info = py_interop_run.info()
    run_info.read(str(run_info_path))

    # Get IDs
    instrument_id=run_info.instrument_name() # instrument name
    date_info=run_info.date() # date
    run_id=run_info.name() # run id
    total_cycles=run_info.total_cycles() # total cycles
    seq_run_num=run_info.run_number() # run number
    run_info_version=run_info.version() # run info version
    
    return {
		"run_id": run_id,
		"instrument_id": instrument_id,
		"day_id": date_info,
		"num_cycles": total_cycles,
	}

# Function to parse run parameters XML
def parse_run_parameters(run_parameters_path):
	"""Extract consumable and read-cycle information from RunParameters.xml.

	Handles both newer instruments (ConsumableInfo sections) and older ones
	(FlowcellRFIDTag / ReagentKitRFIDTag).  Also parses read structure to
	separate sequencing read cycles from index cycles.

	Args:
		run_parameters_path: Path to RunParameters.xml.

	Returns:
		dict with keys: flowcell_part_number, reagent_kit_part_number
		(used internally to derive sequencing_chemistry_id),
		experiment_name, read_cycles, index_cycles, index_read_count.
	"""
	root = read_xml(run_parameters_path)
	consumables = root.findall(".//ConsumableInfo/ConsumableInfo")
	if consumables:
		flowcell_part_number = None
		reagent_kit_part_number = None
		for consumable in consumables:
			consumable_type = (consumable.findtext("Type", "") or "").strip().lower()
			part_number = (consumable.findtext("PartNumber", "") or "").strip()
			if consumable_type == "reagent" and part_number:
				reagent_kit_part_number = part_number
			elif consumable_type == "wetcartridge" and part_number:
				reagent_kit_part_number = part_number
			elif consumable_type == "flowcell" and part_number:
				flowcell_part_number = part_number
			elif consumable_type == "drycartridge" and part_number:
				flowcell_part_number = part_number
	else:
		flowcell_part_number = root.findtext(".//FlowcellRFIDTag/PartNumber", "").strip() or None
		reagent_kit_part_number = (
			root.findtext(".//ReagentKitRFIDTag/PartNumber", "").strip()
			or root.findtext(".//ReagentKitPartNumberEntered", "").strip()
			or None
		)
	experiment_name = root.findtext(".//ExperimentName", "").strip() or None

	read_cycles = 0
	index_cycles = 0
	index_read_count = 0
	read_nodes = root.findall(".//Reads/RunInfoRead") or root.findall(".//Reads/Read")
	for read in read_nodes:
		is_indexed = (read.attrib.get("IsIndexedRead") or "").strip().upper()
		num_cycles = int(read.attrib.get("NumCycles") or read.attrib.get("Cycles") or 0)
		if is_indexed == "Y" or read.attrib.get("ReadName", "").lower().startswith("index"):
			index_cycles += num_cycles
			index_read_count += 1
		else:
			read_cycles += num_cycles

	return {
		"flowcell_part_number": flowcell_part_number,
		"reagent_kit_part_number": reagent_kit_part_number,
		"experiment_name": experiment_name,
		"read_cycles": read_cycles,
		"index_cycles": index_cycles,
		"index_read_count": index_read_count,
	}

# Function to count number of samples in sample sheet
def get_num_samples_ss(samplesheet):
	"""Count the number of samples listed in an Illumina SampleSheet.csv.

	Detects the samplesheet version (v1 vs v2) from the config and locates
	the ``[Data]`` or ``[Cloud_Data]`` section accordingly.  The first row
	after the section header is treated as a column header and excluded
	from the count.

	Args:
		samplesheet: Path to SampleSheet.csv.

	Returns:
		int: Number of samples (0 if the file does not exist or is empty).
	"""
	if not os.path.exists(samplesheet):
		logging.warning("SampleSheet not found: %s", samplesheet)
		return 0
	# Process sample sheet
	with open(samplesheet, "r") as handle:
		all_lines = handle.readlines()
	# Check samplesheet file version
	samplesheet_version = CONFIG["samplesheet"]["version_prefix"]
	sample_count = 0
	in_data_section = False
	if any(item.startswith(samplesheet_version) for item in all_lines):
		logging.info("SampleSheet Version 2")
		str_data_exp = CONFIG["samplesheet"]["sections"]["v2"]
	else:
		logging.info("SampleSheet Version 1")
		str_data_exp = CONFIG["samplesheet"]["sections"]["v1"]

	for line in all_lines:
		line = line.strip()
		if line == str_data_exp:
			in_data_section = True
			continue
		if in_data_section and line:
			sample_count += 1
	# First line after section header is the column header, not a sample
	return max(sample_count - 1, 0)


# Function to parse interop metrics using Illumina's InterOp library
def parse_interop_metrics(run_folder, run_info_path):
    """Compute run-level QC metrics from Illumina InterOp binary files.

    Reads the InterOp directory via ``py_interop_run_metrics`` and
    summarises key quality indicators: cluster density, %PF, %≥Q30,
    yield, and %PhiX aligned.

    Args:
        run_folder: Path to the InterOp directory (currently unused;
                    the directory is derived from *run_info_path*).
        run_info_path: Path to RunInfo.xml (used to locate the run folder).

    Returns:
        dict mapping metric IDs (e.g. ``CLUSTER_DENSITY``) to float values.
    """
    
    run_info = py_interop_run.info()
    run_info.read(run_info_path)

    # Get IDs
    instrument_id=run_info.instrument_name() # instrument name
    date_info=run_info.date() # date
    run_id=run_info.name() # run id

    ## Run Metrics
    run_metrics = py_interop_run_metrics.run_metrics()
    path, file_name = os.path.split(run_info_path)
    run_folder_metrics = run_metrics.read(path) 
    valid_to_load = py_interop_run.uchar_vector(py_interop_run.MetricCount, 0)
    py_interop_run_metrics.list_summary_metrics_to_load(valid_to_load)
    summary = py_interop_summary.run_summary()
    py_interop_summary.summarize_run_metrics(run_metrics, summary)

    # Get metrics
    cluster_density_mean = (summary.at(0).at(0).density().mean()) / 1000
    cluster_pf = summary.at(0).at(0).percent_pf().mean()
    pct_gt_30 = getattr(summary.total_summary(), 'percent_gt_q30')()
    yieldg = getattr(summary.total_summary(), 'yield_g')()
    pct_aligned = getattr(summary.total_summary(), 'percent_aligned')()
    error_rate = getattr(summary.total_summary(), 'error_rate')()
    pct_occupied = getattr(summary.total_summary(), 'percent_occupied')()
    reads = getattr(summary.total_summary(), 'reads')()
    reads_pf = getattr(summary.total_summary(), 'reads_pf')()
    print(f"Cluster Density (K/mm²): {cluster_density_mean}")
    print(f"Cluster PF (%): {cluster_pf}")
    print(f"Percent ≥Q30 (%): {pct_gt_30}")
    print(f"Error Rate (%): {error_rate}")        
	# Collect per-read information
    reads_metrics_detail = []
    
    # Iterar per cada "Read" detectat (Read 1, Index 1, Index 2, Read 2, etc.)
    for i in range(summary.size()):
        read_result = {}  # Dictionary to hold metrics for this read
        read_data = summary.at(i)
        read_number = read_data.read().number()
        is_index = read_data.read().is_index()
                
        # Obtenir el resum global combinat de totes les lanes d'aquesta lectura
        total_summary = read_data.summary()
        
        # Safely extract metrics with error handling
        try:
            read_yield = total_summary.yield_g()
        except:
            read_yield = None
        
        try:
            read_q30 = total_summary.percent_gt_q30()
        except:
            read_q30 = None
        
        try:
            read_error_rate = total_summary.error_rate()
        except:
            read_error_rate = None

		# create string for the read variable <METRIC>_READ_<READ_NUMBER>_<INDEX_OR_DATA>
        metric_prefix = "READ"
        metric_suffix = f"READ_{read_number}"

		# Store per-read metrics in the result dictionary with dynamic keys
        read_result[f"YIELD_{metric_suffix}"] = round(read_yield, 4) if read_yield is not None else None
        read_result[f"Q30_PCT_{metric_suffix}"] = round(read_q30, 4) if read_q30 is not None else None
        read_result[f"ERROR_RATE_{metric_suffix}"] = round(read_error_rate, 4) if read_error_rate is not None else None

		# save the information so later we can append it to result array
        reads_metrics_detail.append(read_result)

    result = {
        "CLUSTER_DENSITY_MEAN": cluster_density_mean,
        "CLUSTER_PF_PCT_MEAN": cluster_pf,
        "Q30_PCT_MEAN": pct_gt_30,
        "YIELD_MEAN": yieldg,
        "PHIX_ALIGNED_PCT_MEAN": pct_aligned,
        "ERROR_RATE_MEAN": error_rate,
        "PCT_OCCUPIED_MEAN": pct_occupied,
        "READS_MEAN": reads,
        "READS_PF_MEAN": reads_pf
    }

	# Append per-read metrics to the result dictionary
    for read_metric in reads_metrics_detail: result.update(read_metric)

    return result


def parse_run_folder(run_folder):
	"""Orchestrate parsing of all data sources within an Illumina run folder.

	Reads RunInfo.xml, RunParameters.xml, SampleSheet.csv, and the InterOp
	directory.  Combines the results into a single flat dictionary suitable
	for CSV output.

	Args:
		run_folder: Path to the top-level Illumina run folder.

	Returns:
		dict containing run metadata (run_id, day_id, instrument_id, …)
		and InterOp QC metrics (CLUSTER_DENSITY, Q30_PCT, …).

	Raises:
		FileNotFoundError: If any required file or folder is missing.
	"""
	run_info_path = run_folder + "/RunInfo.xml"
	run_parameters_path = run_folder + "/RunParameters.xml"
	sample_sheet_path = run_folder + "/SampleSheet.csv"
	interop_folder = run_folder + "/InterOp"

	logging.debug("Run info path: %s", run_info_path)
	logging.debug("Run parameters path: %s", run_parameters_path)
	logging.debug("Sample sheet path: %s", sample_sheet_path)
	logging.debug("InterOp folder: %s", interop_folder)

	missing_paths = [
		path
		for path in [run_info_path, run_parameters_path, sample_sheet_path, interop_folder]
		if not os.path.exists(path)
	]
	if missing_paths:
		raise FileNotFoundError(
			"Missing required run files/folders: " + ", ".join(missing_paths)
		)

	run_info = parse_run_info(run_info_path)
	run_params = parse_run_parameters(run_parameters_path)
	num_samples = get_num_samples_ss(sample_sheet_path)
	interop_metrics = parse_interop_metrics(interop_folder, run_info_path)
	reagent = run_params.get("reagent_kit_part_number") or ""
	flowcell = run_params.get("flowcell_part_number") or ""
	chemistry_id = f"{reagent}_{flowcell}" if reagent and flowcell else (reagent or flowcell or None)

	final_result = {
		"run_id": run_params.get("experiment_name"),
		"run_folder": run_info.get("run_id"),
		"day_id": normalize_day_id(run_info.get("day_id")),
		"instrument_id": run_info.get("instrument_id"),
		"platform_id": CONFIG["platform_id"],
		"sequencing_chemistry_id": chemistry_id,
		"num_cycles": run_info.get("num_cycles", 0),
		"num_samples": num_samples,
	}
	# Merge InterOp metrics (keys are already metric IDs like CLUSTER_DENSITY)
	final_result.update(interop_metrics)
	return final_result


def _metrics_dict(metrics):
	"""Normalise a metrics dict by rounding all numeric values to 4 decimals.

	Non-numeric values are passed through unchanged.

	Args:
		metrics: dict (or object with ``as_output_dict()``).

	Returns:
		New dict with rounded numeric values.
	"""
	payload = metrics if isinstance(metrics, dict) else metrics.as_output_dict()
	rounded = {}
	for key, value in payload.items():
		if isinstance(value, (int, float)):
			rounded[key] = round(value, 4)
		else:
			rounded[key] = value
	return rounded


def write_metrics_csv(metrics, output_path):
	"""Write per-metric rows to a sequencing-metrics CSV.

	Each numeric metric found in the metrics dict that matches a known
	metric ID (via CONFIG ``metric_id_map``) is written as a separate row
	with columns: run_id, day_id, metric_id, value_number.

	Args:
		metrics: Flat dict returned by ``parse_run_folder`` (plus any
				 additions like run_description).
		output_path: pathlib.Path where the CSV will be written.
	"""
	payload = _metrics_dict(metrics)
	run_id = payload.get("run_id")
	day_id = payload.get("day_id")
	fieldnames = CONFIG["fields"]["sequencing_metrics"]
	print(f"Fieldnames for sequencing metrics CSV: {fieldnames}")
	with output_path.open("w", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=fieldnames)
		writer.writeheader()
		for key, value in payload.items():
			# Skip non-numeric values and metadata fields
			if not isinstance(value, (int, float)):
				continue
			if key in ["run_id", "run_folder", "day_id", "instrument_id", "platform_id", "sequencing_chemistry_id", "num_cycles", "num_samples", "run_description"]:
				continue
			# Write each metric as a row using the key as metric_id
			writer.writerow(
				{
					"run_id": run_id,
					"day_id": day_id,
					"metric_id": key,
					"value_number": value,
				}
			)


def write_sequencing_info(metrics, output_path):
	"""Write run-level sequencing information to a single-row CSV.

	The columns written are defined by CONFIG ``fields.sequencing_info``
	(e.g. run_id, run_folder, run_description, day_id, instrument_id, …).

	Args:
		metrics: Flat dict returned by ``parse_run_folder`` (plus any
				 additions like run_description).
		output_path: pathlib.Path where the CSV will be written.
	"""
	fieldnames = CONFIG["fields"]["sequencing_info"]
	output_path = Path(output_path)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	payload = _metrics_dict(metrics)
	row = {key: payload.get(key) for key in fieldnames}
	with output_path.open("w", newline="") as handle:
		writer = csv.DictWriter(handle, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerow(row)


def main():
	"""CLI entry point: parse an Illumina run folder and write output CSVs.

	Reads command-line arguments (--run-folder, --output-dir,
	--run-description, --log, --log-file), loads the external config,
	parses the run folder, and writes two CSV files:
	  - ``<run_id>-sequencing-info.csv``  (run metadata)
	  - ``<run_id>-sequencing-metrics.csv`` (QC metrics in long format)
	"""
	parser = argparse.ArgumentParser(description="Parse Illumina run folder metrics.")
	parser.add_argument(
		"--run-folder",
		nargs="?",
		help="Path to the Illumina run folder.",
	)
	parser.add_argument(
		"--output-dir",
		help="Directory where run-info, sequencing-info, and sequencing-metrics CSVs are written (defaults to run folder or --output).",
	)
	parser.add_argument(
		"--run-description",
		help="Run description to include in the sequencing-info CSV.",
	)
	parser.add_argument(
		"--log",
		default="INFO",
		help="Logging level (DEBUG, INFO, WARNING, ERROR)",
	)
	parser.add_argument(
		"--log-file",
		help="Optional log file path. When provided, logs are written to this file.",
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

	metrics = parse_run_folder(args.run_folder)
	metrics["run_description"] = args.run_description or ""
	print("Parsed metrics for run %s" % metrics.get("run_id"))
	print("Run metadata: day_id=%s, instrument_id=%s, sequencing_chemistry_id=%s"
		% (
			metrics.get("day_id"),
			metrics.get("instrument_id"),
			metrics.get("sequencing_chemistry_id"),
		)
	)
	# show metrics in log
	print("Metrics dictionary:", metrics)

	logging.info("Parsed metrics for run %s", metrics.get("run_id"))
	logging.info(
		"Run metadata: day_id=%s, instrument_id=%s, sequencing_chemistry_id=%s",
		metrics.get("day_id"),
		metrics.get("instrument_id"),
		metrics.get("sequencing_chemistry_id"),
	)

	output_dir = Path(args.output_dir)

	run_id = metrics.get("run_id")
	sequencing_info_path = output_dir / f"{run_id}{CONFIG['output_suffixes']['sequencing_info']}"
	sequencing_metrics_path = output_dir / f"{run_id}{CONFIG['output_suffixes']['sequencing_metrics']}"
	write_sequencing_info(metrics, sequencing_info_path)
	write_metrics_csv(metrics, sequencing_metrics_path)
	logging.info("Wrote sequencing info to %s", sequencing_info_path)
	logging.info("Wrote sequencing metrics to %s", sequencing_metrics_path)


if __name__ == "__main__":
	main()
