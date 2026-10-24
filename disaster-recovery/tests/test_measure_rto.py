import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "measure_rto.py"
)
SPEC = importlib.util.spec_from_file_location("measure_rto", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
measure_rto = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measure_rto)


class MeasureRtoTests(unittest.TestCase):
    def run_report(
        self,
        actual_sha256: str,
        expected_sha256: str,
    ) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        str(SCRIPT_PATH),
                        "--backup",
                        "ledger-before-incident",
                        "--expected-sha256",
                        expected_sha256,
                        "--output",
                        str(report_path),
                    ],
                ),
                patch.object(measure_rto.shutil, "which", return_value="tool"),
                patch.object(
                    measure_rto,
                    "run_command",
                    side_effect=[
                        "",
                        "",
                        f"{actual_sha256}  /data/important.txt",
                    ],
                ),
            ):
                exit_code = measure_rto.main()
            return exit_code, json.loads(report_path.read_text(encoding="utf-8"))

    def test_success_report_requires_matching_restored_checksum(self) -> None:
        checksum = "a" * 64

        exit_code, report = self.run_report(checksum, checksum)

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["status"], "succeeded")
        self.assertEqual(report["backup"], "ledger-before-incident")
        self.assertEqual(report["expected_sha256"], checksum)
        self.assertEqual(report["actual_sha256"], checksum)
        self.assertGreaterEqual(report["recovery_time_seconds"], 0)
        self.assertIn("started_at_utc", report)
        self.assertIn("completed_at_utc", report)

    def test_checksum_mismatch_is_reported_as_failure(self) -> None:
        actual = "a" * 64
        expected = "b" * 64

        exit_code, report = self.run_report(actual, expected)

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertNotEqual(report["actual_sha256"], expected)
        self.assertIn("checksum does not match", report["error"])

    def test_restore_command_failure_is_reported(self) -> None:
        expected = "b" * 64

        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        str(SCRIPT_PATH),
                        "--backup",
                        "ledger-before-incident",
                        "--expected-sha256",
                        expected,
                        "--output",
                        str(report_path),
                    ],
                ),
                patch.object(measure_rto.shutil, "which", return_value="tool"),
                patch.object(
                    measure_rto,
                    "run_command",
                    side_effect=RuntimeError("restore failed"),
                ),
            ):
                exit_code = measure_rto.main()

            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["error"], "restore failed")

    def test_invalid_checksum_output_is_reported(self) -> None:
        expected = "b" * 64

        exit_code, report = self.run_report("invalid", expected)

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["status"], "failed")
        self.assertIn("Could not parse", report["error"])


if __name__ == "__main__":
    unittest.main()
