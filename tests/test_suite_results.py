import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / "scripts/runtime_suite.py"
spec = importlib.util.spec_from_file_location("runtime_suite", path)
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


class EvidenceTests(unittest.TestCase):
    def test_missing_or_nonboolean_success_cannot_pass(self):
        for report in ({}, None, {"passed": "true"}, {"passed": 1}, {"status": "NOT_RUN"}, {"status": "PARTIAL"}):
            with self.subTest(report=report):
                self.assertFalse(suite.passed(report))

    def test_explicit_failure_takes_precedence(self):
        self.assertFalse(suite.passed({"status": "PASS", "passed": False}))
        self.assertFalse(suite.passed({"status": "FAIL", "passed": True}))
        self.assertFalse(suite.passed({"passed": True, "error": "cleanup failed"}))

    def test_supported_success_schemas(self):
        self.assertTrue(suite.passed({"passed": True}))
        self.assertTrue(suite.passed({"status": "PASS"}))


if __name__ == "__main__":
    unittest.main()
