from __future__ import annotations

import os
import re
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
    scenario = (tmp_path / "scenario.json").read_text(encoding="utf-8")
    cleanup = (tmp_path / "cleanup.json").read_text(encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert _number(scenario, "ros_planar_displacement") >= 0.10
    assert _number(scenario, "plugin_distance") >= 0.10
    assert _number(scenario, "post_reset_distance") <= 1e-6
    assert '"status":"clean"' in cleanup
    assert '"survivors":[]' in cleanup


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
