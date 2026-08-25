from __future__ import annotations

import json
import os
import pty
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from collections.abc import Callable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_owned_process.py"
FIXTURES = ROOT / "scripts" / "fixtures" / "processes"


class OwnedProcessTests(unittest.TestCase):
    @staticmethod
    def child_pids(parent_pid: int) -> list[int]:
        children: list[int] = []
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                fields = (entry / "stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
                if int(fields[1]) == parent_pid:
                    children.append(int(entry.name))
            except (FileNotFoundError, IndexError, PermissionError, ValueError):
                continue
        return sorted(children)

    @staticmethod
    def port_is_open(port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                return True
        except OSError:
            return False

    @staticmethod
    def wait_until(predicate: Callable[[], bool], timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            time.sleep(0.02)
        return False

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

    def test_terminal_ctrl_c_writes_receipt_and_closes_owned_http_server(self) -> None:
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]

        with tempfile.TemporaryDirectory() as temporary:
            receipt_path = Path(temporary) / "cleanup.json"
            command = [
                sys.executable,
                str(WRAPPER),
                "--timeout",
                "30",
                "--cleanup-receipt",
                str(receipt_path),
                "--",
                sys.executable,
                "-m",
                "http.server",
                str(port),
                "--bind",
                "127.0.0.1",
            ]
            wrapper_pid, master_fd = pty.fork()
            if wrapper_pid == 0:
                os.chdir(ROOT)
                os.execv(sys.executable, command)

            child_pid: int | None = None
            wrapper_reaped = False
            try:
                self.assertTrue(
                    self.wait_until(lambda: bool(self.child_pids(wrapper_pid))),
                    "wrapper did not launch its owned child",
                )
                child_pid = self.child_pids(wrapper_pid)[0]
                self.assertTrue(
                    self.wait_until(lambda: self.port_is_open(port)),
                    "owned HTTP server did not open its port",
                )

                os.write(master_fd, b"\x03")
                status: int | None = None
                deadline = time.monotonic() + 5.0
                while status is None and time.monotonic() < deadline:
                    waited_pid, candidate = os.waitpid(wrapper_pid, os.WNOHANG)
                    if waited_pid == wrapper_pid:
                        status = candidate
                        wrapper_reaped = True
                    else:
                        time.sleep(0.02)
                if status is None:
                    self.fail("wrapper did not exit after terminal Ctrl-C")
                self.assertEqual(os.waitstatus_to_exitcode(status), 0)
                self.assertTrue(receipt_path.exists(), "terminal Ctrl-C omitted cleanup receipt")
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                self.assertEqual(receipt["termination_reason"], "signal")
                self.assertEqual(receipt["signal_sent"], "SIGINT")
                self.assertEqual(receipt["dut_exit"], 0)
                self.assertEqual(receipt["survivors"], [])
                self.assertFalse(Path(f"/proc/{child_pid}").exists(), "owned child survived cleanup")
                self.assertTrue(
                    self.wait_until(lambda: not self.port_is_open(port)),
                    "owned HTTP server port survived cleanup",
                )
            finally:
                os.close(master_fd)
                if not wrapper_reaped:
                    try:
                        os.kill(wrapper_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    os.waitpid(wrapper_pid, 0)
                if child_pid is not None and Path(f"/proc/{child_pid}").exists():
                    try:
                        os.killpg(child_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
