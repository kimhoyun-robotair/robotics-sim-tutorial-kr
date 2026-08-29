from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import copytree

import yaml

ROOT = Path(__file__).parents[1]
CHECKER = ROOT / "scripts/check_workflow.py"
WORKFLOW = ROOT / ".github/workflows/pages.yml"


def run_checker(path: Path, runner: str = "ubuntu-24.04", timeout: int = 30) -> subprocess.CompletedProcess[str]:
    # Given: a workflow path and the expected ROS runner contract.
    command = [
        sys.executable,
        str(CHECKER),
        str(path),
        "--expect-runner",
        runner,
        "--expect-timeout",
        str(timeout),
    ]

    # When: the repository-owned workflow checker runs.
    return subprocess.run(command, check=False, capture_output=True, text=True)


def test_repository_workflow_preserves_pages_and_adds_ros_gate() -> None:
    result = run_checker(WORKFLOW)

    # Then: the complete Pages and ROS/Gazebo contract passes.
    assert result.returncode == 0, result.stderr


def test_checker_rejects_ros_job_with_write_permission(tmp_path: Path) -> None:
    # Given: the real workflow with the ROS job escalated to Pages write access.
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    workflow["jobs"]["ros-gazebo"]["permissions"] = {"contents": "write"}
    fixture = tmp_path / "write-permission.yml"
    fixture.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")

    result = run_checker(fixture)

    # Then: permission escalation is rejected at the workflow boundary.
    assert result.returncode == 1


def test_checker_rejects_pages_dependency_regression(tmp_path: Path) -> None:
    # Given: the real workflow with deploy no longer depending on build.
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    workflow["jobs"]["deploy"]["needs"] = "ros-gazebo"
    fixture = tmp_path / "broken-pages.yml"
    fixture.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")

    result = run_checker(fixture)

    # Then: the Pages dependency regression is rejected.
    assert result.returncode == 1


def test_checker_rejects_pages_setup_on_jazzy(tmp_path: Path) -> None:
    fixture_root = tmp_path / "repository"
    workflow_dir = fixture_root / ".github/workflows"
    workflow_dir.mkdir(parents=True)
    workflow = yaml.load(WORKFLOW.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    configure = next(
        step
        for step in workflow["jobs"]["build"]["steps"]
        if step.get("uses") == "actions/configure-pages@v5"
    )
    configure.pop("if")
    fixture = workflow_dir / "pages.yml"
    fixture.write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8")
    copytree(ROOT / "scripts/ci", fixture_root / "scripts/ci")

    result = run_checker(fixture)

    assert result.returncode == 1
    assert "must run only on main" in result.stderr


def test_checker_rejects_parallel_selected_test_execution(tmp_path: Path) -> None:
    # Given: the real workflow helpers without the serialized CTest contract.
    fixture_root = tmp_path / "repository"
    workflow_dir = fixture_root / ".github/workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "pages.yml"
    workflow.write_text(WORKFLOW.read_text(encoding="utf-8"), encoding="utf-8")
    copytree(ROOT / "scripts/ci", fixture_root / "scripts/ci")
    runner = fixture_root / "scripts/ci/run_ros_gazebo_ci.sh"
    runner.write_text(
        runner.read_text(encoding="utf-8").replace("--executor sequential ", ""),
        encoding="utf-8",
    )

    result = run_checker(workflow)

    # Then: a future parallel test-order regression is rejected.
    assert result.returncode == 1
    assert "deterministic selected tests" in result.stderr
