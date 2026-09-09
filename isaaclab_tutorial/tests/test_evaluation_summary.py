"""Pure tests with SYNTHETIC values; these are not trained-policy measurements."""

import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "examples" / "summarize_evaluations.py"
SPEC = importlib.util.spec_from_file_location("summarize_evaluations", SCRIPT)
SUMMARY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUMMARY)


def synthetic_report(label):
    """Build two deliberately unequal episode lengths to test episode weighting."""
    return {
        "schema": SUMMARY.SCHEMA, "status": "complete", "label": label,
        "requested_episodes": 2,
        "protocol": {"fixture": "SYNTHETIC: not simulator output"},
        "episodes": [
            {
                "seed": 1000, "steps": 2, "duration_s": 0.2,
                "terminated": True, "truncated": False,
                "initial_state": {"cart_position_m": 0.1, "pole_angle_rad": 0.2},
                "pole_angle_rms_rad": 0.1, "cart_position_rms_m": 0.2,
                "cart_travel_m": 0.3, "command_force_rms_n": 2.0, "action_change_rms": 0.4,
            },
            {
                "seed": 1001, "steps": 10, "duration_s": 1.0,
                "terminated": False, "truncated": True,
                "initial_state": {"cart_position_m": -0.1, "pole_angle_rad": -0.2},
                "pole_angle_rms_rad": 0.5, "cart_position_rms_m": 0.6,
                "cart_travel_m": 0.7, "command_force_rms_n": 6.0, "action_change_rms": 0.8,
            },
        ],
    }


class EvaluationSummaryTests(unittest.TestCase):
    def test_pair_by_seed_and_retain_early_failure(self):
        left = synthetic_report("SYNTHETIC baseline")
        right = synthetic_report("SYNTHETIC candidate")
        right["episodes"].reverse()
        right["episodes"][0]["command_force_rms_n"] = 4.0
        right["episodes"][1]["command_force_rms_n"] = 1.0
        result = SUMMARY.compare_reports(left, right)
        metric = result["metrics"]["command_force_rms_n"]
        self.assertEqual(metric["reference"]["mean"], 4.0)
        self.assertEqual(metric["candidate"]["mean"], 2.5)
        self.assertEqual(metric["paired_delta"]["mean"], -1.5)
        self.assertAlmostEqual(metric["paired_delta"]["sample_std"], math.sqrt(0.5))
        self.assertEqual(result["outcomes"]["reference"]["terminated"], 1)

    def test_timeout_with_failure_is_not_timeout_only(self):
        report = synthetic_report("SYNTHETIC")
        report["episodes"][0]["truncated"] = True
        result = SUMMARY.compare_reports(report, copy.deepcopy(report))
        self.assertEqual(result["outcomes"]["reference"], {
            "terminated": 1, "truncated_without_termination": 1, "both_flags": 1,
        })

    def test_reject_incomplete_nonfinite_and_unpaired_data(self):
        baseline = synthetic_report("SYNTHETIC")
        mutations = [
            lambda item: item.update(status="failed"),
            lambda item: item.update(requested_episodes=3),
            lambda item: item["protocol"].update(physics="different"),
            lambda item: item["episodes"][0].update(seed=1001),
            lambda item: item["episodes"][0].update(seed=999),
            lambda item: item["episodes"][0].update(pole_angle_rms_rad=float("nan")),
            lambda item: item["episodes"][0].update(command_force_rms_n=float("inf")),
            lambda item: item["episodes"][0].update(terminated=False),
            lambda item: item["episodes"][0]["initial_state"].update(cart_position_m=0.7),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                candidate = copy.deepcopy(baseline)
                mutation(candidate)
                with self.assertRaises(ValueError):
                    SUMMARY.compare_reports(baseline, candidate)

    def test_atomic_json_rejects_nan_and_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            SUMMARY.write_json_atomic(path, {"status": "original"})
            with self.assertRaises(ValueError):
                SUMMARY.write_json_atomic(path, {"bad": float("nan")})
            self.assertEqual(json.loads(path.read_text()), {"status": "original"})
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_cli_writes_json_and_csv_from_synthetic_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            left, right = folder / "left.json", folder / "right.json"
            output, csv_output = folder / "comparison.json", folder / "comparison.csv"
            left.write_text(json.dumps(synthetic_report("SYNTHETIC baseline")))
            right.write_text(json.dumps(synthetic_report("SYNTHETIC candidate")))
            subprocess.run(
                [sys.executable, str(SCRIPT), str(left), str(right), "--output", str(output),
                 "--csv-output", str(csv_output)],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(json.loads(output.read_text())["episode_count"], 2)
            self.assertIn("command_force_rms_n,4.0,4.0,0.0,0.0", csv_output.read_text())


if __name__ == "__main__":
    unittest.main()
