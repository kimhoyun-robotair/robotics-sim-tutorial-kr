from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).parents[4]
RUNNER = WORKSPACE_ROOT / "scripts/run_tdd_phase.py"
DEPENDENCY_CLOSURE = (
    "tutorial_bot_plugins",
    "tutorial_bot_tests",
    "tutorial_bot_gazebo",
    "tutorial_bot_description",
    "tutorial_bot_bringup",
)


def _write_fake_colcon(bin_dir: Path, test_exit: int, build_exit: int = 0) -> None:
    script = bin_dir / "colcon"
    script.write_text(
        "#!/usr/bin/env bash\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_COLCON_CALLS\"\n"
        "case \" $* \" in\n"
        "  *' build '*) exit \"$FAKE_BUILD_EXIT\" ;;\n"
        "  *' test-result '*) exit \"$FAKE_TEST_EXIT\" ;;\n"
        "  *' test '*) exit \"$FAKE_TEST_EXIT\" ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    os.environ["FAKE_TEST_EXIT"] = str(test_exit)
    os.environ["FAKE_BUILD_EXIT"] = str(build_exit)


def _run_phase(tmp_path: Path, phase: str, test_exit: int, build_exit: int = 0) -> subprocess.CompletedProcess[str]:
    # Given: a deterministic colcon fixture and a real test source blob.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.log"
    test_source = tmp_path / "test_contract.py"
    test_source.write_text("def test_contract():\n    assert True\n", encoding="utf-8")
    _write_fake_colcon(bin_dir, test_exit=test_exit, build_exit=build_exit)
    environment = os.environ | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "FAKE_COLCON_CALLS": str(calls),
    }

    # When: the TDD phase runner executes through its real CLI.
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--task",
            "9",
            "--phase",
            phase,
            "--packages",
            "tutorial_bot_plugins,tutorial_bot_tests",
            "--selector",
            "^diagnostics_distance$",
            "--test-path",
            str(test_source),
            "--attempt-dir",
            str(tmp_path / "attempt"),
        ],
        capture_output=True,
        check=False,
        cwd=WORKSPACE_ROOT,
        env=environment,
        text=True,
    )
    return result


@pytest.mark.parametrize(
    ("phase", "test_exit", "expected_exit"),
    [("red", 1, 1), ("green", 0, 0)],
)
def test_runner_classifies_intended_red_and_green(
    tmp_path: Path, phase: str, test_exit: int, expected_exit: int
) -> None:
    result = _run_phase(tmp_path, phase=phase, test_exit=test_exit)

    # Then: the exit class and metadata match the observed test result.
    assert result.returncode == expected_exit
    metadata = json.loads(
        (tmp_path / "attempt" / f"{phase}-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["classification"] == phase
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8")
    assert "--packages-select " + " ".join(DEPENDENCY_CLOSURE) in calls


def test_runner_classifies_build_failure_as_69(tmp_path: Path) -> None:
    result = _run_phase(tmp_path, phase="green", test_exit=0, build_exit=2)

    # Then: build/configuration failures cannot be mistaken for behavioral RED.
    assert result.returncode == 69
    metadata = json.loads(
        (tmp_path / "attempt" / "green-metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["classification"] == "build_failure"
