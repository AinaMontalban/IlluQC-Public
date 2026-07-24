import csv
import tempfile
import unittest
from pathlib import Path

from sample_metrics_parser import METRIC_COLUMNS, parse_sample_metrics, write_sample_metrics


class SampleMetricsParserTests(unittest.TestCase):
    def make_input(self, directory):
        path = Path(directory) / "metrics.csv"
        values = {column: "1" for column in METRIC_COLUMNS}
        values.update({"sample": "S001", "mean": "12,5", "min": "", "max": "20"})
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["sample", *METRIC_COLUMNS], delimiter=";")
            writer.writeheader()
            writer.writerow(values)
            writer.writerow({**values, "sample": "S002", "mean": "25%"})
        return path

    def test_parses_semicolon_metrics_and_missing_values(self):
        with tempfile.TemporaryDirectory() as directory:
            result = parse_sample_metrics(self.make_input(directory), "S001")
            parsed = {row["metric_id"]: row["value_number"] for row in result["sample_metrics"]}
            self.assertEqual(result["num_samples"], 1)
            self.assertEqual(parsed["mean"], 12.5)
            self.assertNotIn("min", parsed)

    def test_writes_long_format(self):
        with tempfile.TemporaryDirectory() as directory:
            result = parse_sample_metrics(self.make_input(directory), "S002")
            output = Path(directory) / "output.csv"
            write_sample_metrics(output, "R001", result["sample_metrics"])
            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["sample_id"], "S002")
            self.assertEqual(rows[0]["run_id"], "R001")
            self.assertEqual({*rows[0]}, {"sample_id", "run_id", "metric_id", "value_number"})


if __name__ == "__main__":
    unittest.main()
