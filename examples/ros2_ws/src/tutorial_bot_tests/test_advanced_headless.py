from __future__ import annotations

import os
import re
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

WORKSPACE_ROOT = Path(__file__).parents[4]


@dataclass(frozen=True, slots=True)
class HeadlessCase:
    scenario: str
    expected_exit: int
    cleanup_status: str
    readiness_timeout: int


FAULT_CASES: Final = (
    HeadlessCase("missing-model", 20, "clean", 5),
    HeadlessCase("plugin-missing", 21, "clean", 1),
    HeadlessCase("misleading-output", 1, "clean", 1),
    HeadlessCase("cleanup-reuse", 70, "failed", 1),
    HeadlessCase("timeout", 124, "clean", 1),
)


def _case_id(case: HeadlessCase) -> str:
    return case.scenario


def _number(receipt: str, field: str) -> float:
    matched = re.search(rf'"{re.escape(field)}":(-?[0-9]+(?:\.[0-9]+)?)', receipt)
    assert matched is not None
    return float(matched.group(1))


def test_nominal_scenario_uses_runnable_checker_seam(tmp_path: Path) -> None:
    # Given: the installed prerequisite packages and the repository checker seam.
    install_base = Path(os.environ["AMENT_PREFIX_PATH"].split(os.pathsep)[0]).parent
    checker = WORKSPACE_ROOT / "scripts" / "check_advanced_course.sh"

    # When: the Task 12 nominal scenario is requested from that seam.
    result = subprocess.run(
        [
            str(checker),
            "--scenario",
            "nominal",
            "--install-base",
            str(install_base),
            "--evidence",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )

    # Then: live ROS, plugin, reset, and ownership observables pass together.
    assert result.returncode == 0, (
        f"checker exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    scenario = (tmp_path / "scenario.json").read_text(encoding="utf-8")
    cleanup = (tmp_path / "cleanup.json").read_text(encoding="utf-8")
    assert _number(scenario, "ros_planar_displacement") >= 0.10
    assert _number(scenario, "plugin_distance") >= 0.10
    assert _number(scenario, "post_reset_distance") <= 1e-6
    assert '"status":"clean"' in cleanup
    assert '"survivors":[]' in cleanup


def test_nominal_early_exit_surfaces_checker_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: a nonexistent install base that makes the checker exit before writing receipts.
    monkeypatch.setenv("AMENT_PREFIX_PATH", str(tmp_path / "missing-install/package"))

    # When: the nominal integration harness executes the early-failing checker.
    with pytest.raises(AssertionError) as captured:
        test_nominal_scenario_uses_runnable_checker_seam(tmp_path / "evidence")

    # Then: the harness exposes the checker status and captured diagnostics.
    message = captured.value.args[0]
    assert isinstance(message, str)
    assert "checker exited 64" in message
    assert "stdout:\n" in message
    assert "stderr:" in message
    assert "installed headless assets not found" in message


@pytest.mark.parametrize("case", FAULT_CASES, ids=_case_id)
def test_fault_scenario_preserves_exit_and_cleanup_taxonomy(
    tmp_path: Path, case: HeadlessCase
) -> None:
    # Given: an installed stack and an isolated evidence directory for one fault.
    install_base = Path(os.environ["AMENT_PREFIX_PATH"].split(os.pathsep)[0]).parent

    # When: the runnable checker executes the fault through its real process seam.
    result = subprocess.run(
        [
            str(WORKSPACE_ROOT / "scripts" / "check_advanced_course.sh"),
            "--scenario",
            case.scenario,
            "--internal-readiness-timeout",
            str(case.readiness_timeout),
            "--install-base",
            str(install_base),
            "--evidence",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Then: the exact exit is retained and cleanup reports no owned survivors.
    cleanup = (tmp_path / "cleanup.json").read_text(encoding="utf-8")
    assert result.returncode == case.expected_exit
    assert f'"status":"{case.cleanup_status}"' in cleanup
    assert '"survivors":[]' in cleanup


def test_cleanup_escalates_only_the_owned_term_resistant_group(tmp_path: Path) -> None:
    # Given: the checker owns a fake Gazebo group that ignores INT and TERM,
    # while an unrelated sentinel runs in a different process group.
    install_base = tmp_path / "install"
    (install_base / "tutorial_bot_plugins/lib").mkdir(parents=True)
    (install_base / "tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds").mkdir(
        parents=True
    )
    (install_base / "tutorial_bot_bringup/share/tutorial_bot_bringup/config").mkdir(
        parents=True
    )
    (
        install_base / "tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
    ).touch()
    (
        install_base
        / "tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
    ).write_text(
        "<sdf version='1.10'><world name='advanced_diagnostics'/></sdf>\n",
        encoding="utf-8",
    )
    (
        install_base
        / "tutorial_bot_bringup/share/tutorial_bot_bringup/config/bridge.yaml"
    ).write_text("[]\n", encoding="utf-8")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gz = fake_bin / "gz"
    fake_gz.write_text(
        "#!/usr/bin/env bash\n"
        'printf \'%s\\n\' "$$" > "$FAKE_GZ_PID_FILE"\n'
        "trap '' INT TERM\n"
        "while true; do sleep 1; done\n",
        encoding="utf-8",
    )
    fake_gz.chmod(0o755)
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    fake_pid_file = tmp_path / "fake-gz.pid"
    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "FAKE_GZ_PID_FILE": str(fake_pid_file),
    }
    sentinel = subprocess.Popen(["sleep", "60"], start_new_session=True)
    checker = subprocess.Popen(
        [
            str(WORKSPACE_ROOT / "scripts" / "check_advanced_headless.sh"),
            "--scenario",
            "timeout",
            "--internal-readiness-timeout",
            "1",
            "--install-base",
            str(install_base),
            "--evidence",
            str(evidence),
        ],
        env=environment,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        # When: checker cleanup must stop its resistant process group.
        stdout, stderr = checker.communicate(timeout=12)

        # Then: escalation is bounded, the public exit and receipt are retained,
        # and the unrelated sentinel is untouched.
        assert checker.returncode == 124, (stdout, stderr)
        assert '"status":"clean"' in (evidence / "cleanup.json").read_text(
            encoding="utf-8"
        )
        assert '"survivors":[]' in (evidence / "cleanup.json").read_text(
            encoding="utf-8"
        )
        assert sentinel.poll() is None
    finally:
        if checker.poll() is None:
            os.killpg(checker.pid, signal.SIGKILL)
            checker.wait()
        if fake_pid_file.exists():
            fake_pid = int(fake_pid_file.read_text(encoding="utf-8"))
            try:
                os.killpg(fake_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if sentinel.poll() is None:
            os.killpg(sentinel.pid, signal.SIGKILL)
            sentinel.wait()
