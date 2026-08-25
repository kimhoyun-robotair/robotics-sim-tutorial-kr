from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_owned_process.py"
FIXTURES = ROOT / "scripts" / "fixtures" / "processes"


class OwnedProcessTests(unittest.TestCase):
    def run_owned(
        self, fixture: str, *fixture_args: str, timeout: int = 5, signal_after: str | None = None
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "cleanup.json"
            command = [
                sys.executable,
                str(WRAPPER),
                "--timeout",
                str(timeout),
            ]
            if signal_after is not None:
                command.extend(("--signal-after", signal_after))
            command.extend(
                (
                    "--cleanup-receipt",
                    str(receipt),
                    "--",
                    sys.executable,
                    str(FIXTURES / fixture),
                    *fixture_args,
                )
            )
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            data = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else {}
            return completed, data

    def test_success_reaps_only_registered_sentinel(self) -> None:
        completed, receipt = self.run_owned("success.py")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(receipt["dut_exit"], 0)
        self.assertTrue(receipt["sentinel_survived_dut_teardown"])
        self.assertTrue(receipt["sentinel_reaped"])
        self.assertEqual(receipt["survivors"], [])

    def test_partial_launch_preserves_dut_exit_and_cleans_descendants(self) -> None:
        completed, receipt = self.run_owned("partial-launch.py", "--fail-after-spawn")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(receipt["dut_exit"], 1)
        self.assertTrue(receipt["sentinel_reaped"])
        self.assertEqual(receipt["survivors"], [])

    def test_timeout_is_distinct_from_wrapper_failure(self) -> None:
        completed, receipt = self.run_owned("long_running_owned_fixture.py", timeout=1)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(receipt["dut_exit"], 124)
        self.assertEqual(receipt["termination_reason"], "timeout")
        self.assertEqual(receipt["survivors"], [])

    def test_pid_reuse_is_reported_as_stale_identity(self) -> None:
        completed, receipt = self.run_owned("pid-reuse.py")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(receipt["dut_exit"], 70)
        self.assertTrue(receipt["stale_identity"])
        self.assertEqual(receipt["survivors"], [])

    def test_sigint_reports_shell_compatible_exit_and_reaps_sentinel(self) -> None:
        completed, receipt = self.run_owned(
            "long_running_owned_fixture.py", timeout=5, signal_after="0.2:INT"
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(receipt["dut_exit"], 130)
        self.assertEqual(receipt["signal_sent"], "SIGINT")
        self.assertTrue(receipt["sentinel_reaped"])
        self.assertEqual(receipt["survivors"], [])


if __name__ == "__main__":
    unittest.main()
