from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_course_math.py"
CANONICAL_XACRO = (
    ROOT
    / "examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro"
)


def test_beginner_robot_math_matches_canonical_xacro(tmp_path: Path) -> None:
    # Given: the canonical robot and beginner mechanics chapters.
    evidence = tmp_path / "math.json"

    # When: the public course-math checker audits the beginner robot scope.
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--scope",
            "beginner-robot",
            "--xacro",
            str(CANONICAL_XACRO),
            "--evidence",
            str(evidence),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: dimensions, inertia, and all three motion examples agree.
    assert result.returncode == 0, result.stderr
    report = json.loads(evidence.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["wheel_radius_m"] == 0.06
    assert report["wheel_separation_m"] == 0.38
    assert report["verified_examples"] == ["straight", "arc", "spin"]


def test_swapped_wheels_reject_turn_direction(tmp_path: Path) -> None:
    # Given: a fixture that swaps the left and right DiffDrive joints.
    evidence = tmp_path / "fault.json"

    # When: the fixture is checked through the same public CLI.
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--scope",
            "beginner-robot",
            "--fixture",
            "scripts/fixtures/math/swapped-wheels.yaml",
            "--evidence",
            str(evidence),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    # Then: a false positive turn is impossible and the diagnostic is exact.
    assert result.returncode == 1
    assert "turn-direction mismatch" in f"{result.stdout}{result.stderr}"
    assert json.loads(evidence.read_text(encoding="utf-8"))["status"] == "fail"


def test_all_scope_runs_every_current_math_audit(tmp_path: Path) -> None:
    # Given: the aggregate course-math scope and its evidence path.
    evidence = tmp_path / "all.json"

    # When: the public checker runs every current course math audit.
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--scope",
            "all",
            "--evidence",
            str(evidence),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: the aggregate succeeds and records the audited scope explicitly.
    assert result.returncode == 0, result.stderr
    report = json.loads(evidence.read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["verified_scopes"] == ["beginner-robot"]
