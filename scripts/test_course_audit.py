from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import audit_course_evidence

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "scripts/fixtures/evidence"


def test_installed_artifacts_use_retained_fresh_install_when_env_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: final verification has retained the installed artifact but exports no install env.
    artifact = "package/share/package/contract.json"
    retained_install = tmp_path / "task-15/fresh-install"
    installed_artifact = retained_install / artifact
    installed_artifact.parent.mkdir(parents=True)
    installed_artifact.write_text("{}\n", encoding="utf-8")
    monkeypatch.delenv("TUTORIAL_INSTALL_BASE", raising=False)

    # When: the installed-artifact contract is checked from the final evidence root.
    errors = audit_course_evidence.installed_artifact_errors(
        {"installed_artifacts": [artifact]}, tmp_path
    )

    # Then: the real retained artifact satisfies the contract.
    assert errors == []


@pytest.mark.parametrize(
    ("fixture", "expected_class"),
    (
        ("stale-sha", "stale_sha"),
        ("orphan-image", "orphan_image"),
        ("missing-cleanup", "missing_cleanup"),
        ("misleading-success", "misleading_success"),
        ("red-after-production", "invalid_tdd_order"),
    ),
)
def test_audit_rejects_fault_from_fixture_contents(
    fixture: str, expected_class: str, tmp_path: Path
) -> None:
    # Given: a copied evidence tree whose directory name carries no fault hint.
    copied = tmp_path / "evidence-under-test"
    source = FIXTURES / fixture
    subprocess.run(("cp", "-a", str(source), str(copied)), check=True)
    index = copied / "index.json"

    # When: the public CLI audits the copied tree.
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/audit_course_evidence.py",
            "--evidence-index",
            str(index),
            "--evidence-root",
            str(copied),
            "--fixture",
            str(copied),
            "--source-sha",
            "1111111111111111111111111111111111111111",
        ),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: the evidence inconsistency, not the fixture name, determines the class.
    report = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert report["class"] == expected_class


def test_audit_rejects_missing_task_15_entry(tmp_path: Path) -> None:
    # Given: otherwise well-formed bindings for only Tasks 1 through 14.
    tasks = []
    for number in range(1, 15):
        attempt = tmp_path / f"task-{number}"
        attempt.mkdir()
        (attempt / "DoneClaim.json").write_text("{}\n", encoding="utf-8")
        tasks.append(
            {
                "task": number,
                "commit": f"{number:040x}",
                "attempt_dir": str(attempt),
            }
        )
    index = tmp_path / "index.json"
    index.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_sha": "1" * 40,
                "tasks": tasks,
            }
        ),
        encoding="utf-8",
    )

    # When: full curriculum task coverage is required.
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/audit_course_evidence.py",
            "--evidence-index",
            str(index),
            "--evidence-root",
            str(tmp_path),
            "--source-sha",
            "1" * 40,
            "--require-tasks",
            "1-15",
        ),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: the missing binding is an audit failure.
    report = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert report["class"] == "missing_task"


def test_matrix_dispatches_real_course_faults_and_headless_checker(
    tmp_path: Path,
) -> None:
    # Given: the complete three-course matrix selected in dry-run mode.
    output = tmp_path / "matrix"

    # When: the public CLI expands all required nominal and fault dispatches.
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/run_course_matrix.py",
            "--course",
            "beginner,intermediate,advanced",
            "--scenarios",
            "all-required",
            "--modes",
            "nominal,fault",
            "--dry-run",
            "--evidence",
            str(output),
        ),
        cwd=ROOT,
        check=False,
    )

    # Then: every fault uses a supported adverse input and headless uses its real checker.
    report = json.loads((output / "matrix.json").read_text(encoding="utf-8"))
    commands = {
        (item["course"], item["scenario"], item["mode"]): item["command"]
        for item in report["dispatches"]
    }
    assert completed.returncode == 0
    assert "--expect-failure" not in commands[("beginner", "diff-drive", "fault")]
    assert "missing-wheel-parent.urdf.xacro" in " ".join(
        commands[("beginner", "diff-drive", "fault")]
    )
    assert "first-world.sdf" in " ".join(commands[("beginner", "fuel", "fault")])
    assert commands[("advanced", "headless", "nominal")][0].endswith(
        "check_advanced_headless.sh"
    )
    assert "plugin-missing" in commands[("advanced", "headless", "fault")]
    assert "missing-model" in commands[("advanced", "distance", "fault")]
    assert "transport-wrong-types" in commands[("advanced", "transport", "fault")]
    assert "invalid-period" in commands[("advanced", "physics", "fault")]


def test_matrix_resolves_relative_evidence_before_exporting_shared_paths(
    tmp_path: Path,
) -> None:
    # Given: a relative evidence argument from outside the repository.

    # When: the matrix prepares its shared build without executing scenarios.
    completed = subprocess.run(
        (
            sys.executable,
            str(ROOT / "scripts/run_course_matrix.py"),
            "--course",
            "intermediate",
            "--scenarios",
            "launch",
            "--modes",
            "nominal",
            "--dry-run",
            "--evidence",
            "relative-matrix",
        ),
        cwd=tmp_path,
        check=False,
    )

    # Then: every exported path is absolute and checker-safe.
    report = json.loads(
        (tmp_path / "relative-matrix/matrix.json").read_text(encoding="utf-8")
    )
    command = report["shared_build"]["command"]
    assert completed.returncode == 0
    assert Path(command[command.index("--install-base") + 1]).is_absolute()


def test_advanced_distance_probe_moves_the_model_through_world_transport(
    tmp_path: Path,
) -> None:
    # Given: installed asset fixtures and a bounded Gazebo transport double.
    install = tmp_path / "install"
    library = install / "tutorial_bot_plugins/lib/libTutorialBotDiagnosticsSystem.so"
    world = (
        install
        / "tutorial_bot_gazebo/share/tutorial_bot_gazebo/worlds/advanced-diagnostics.sdf"
    )
    library.parent.mkdir(parents=True)
    world.parent.mkdir(parents=True)
    library.touch()
    world.touch()
    binary_dir = tmp_path / "bin"
    binary_dir.mkdir()
    fake_gz = ROOT / "scripts/fixtures/advanced/fake_gz.sh"
    (binary_dir / "gz").symlink_to(fake_gz)
    calls = tmp_path / "gz-calls.log"
    environment = {
        **os.environ,
        "PATH": f"{binary_dir}:{os.environ['PATH']}",
        "TUTORIAL_INSTALL_BASE": str(install),
        "FAKE_GZ_CALLS": str(calls),
    }

    # When: the public distance CLI executes its nominal scenario.
    completed = subprocess.run(
        (
            "bash",
            str(ROOT / "scripts/check_advanced_course.sh"),
            "--scenario",
            "distance",
            "--evidence",
            str(tmp_path / "evidence"),
        ),
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    # Then: it observes zero and positive distance through the world pose service.
    result = json.loads(
        (tmp_path / "evidence/scenario.json").read_text(encoding="utf-8")
    )
    assert completed.returncode == 0, completed.stderr
    assert result == {
        "scenario": "distance",
        "status": "PASS",
        "observed_zero": True,
        "observed_positive": True,
    }
    assert "service -s /world/advanced_diagnostics/set_pose" in calls.read_text(
        encoding="utf-8"
    )
