from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ElementTree


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPOSITORY_ROOT / "examples/ros2_ws/src/tutorial_bot_description"
CHECKER = REPOSITORY_ROOT / "scripts/check_xacro_stages.py"
STAGES = (
    "01-base.xacro",
    "02-wheels-and-joints.xacro",
    "03-diff-drive.xacro",
    "04-sensors-final.xacro",
)
DOC_STAGES = (
    ("05-first-robot.md", "01-base.xacro"),
    ("06-joints.md", "02-wheels-and-joints.xacro"),
    ("07-diff-drive.md", "03-diff-drive.xacro"),
    ("08-sensors.md", "04-sensors-final.xacro"),
)


def test_installed_stages_are_incremental_and_match_the_canonical_robot(
    tmp_path: Path,
) -> None:
    install_base = tmp_path / "install"
    environment = os.environ | {
        "AMENT_PREFIX_PATH": "",
        "COLCON_PREFIX_PATH": "",
        "PATH": "/opt/ros/jazzy/bin:/usr/bin:/bin",
    }
    stage_dir = PACKAGE_ROOT / "urdf/stages"

    for stage in STAGES:
        assert (stage_dir / stage).is_file(), f"missing stage asset: {stage}"

    subprocess.run(
        [
            "colcon",
            "--log-base",
            str(tmp_path / "log"),
            "build",
            "--base-paths",
            str(PACKAGE_ROOT.parent),
            "--packages-select",
            "tutorial_bot_description",
            "--build-base",
            str(tmp_path / "build"),
            "--install-base",
            str(install_base),
        ],
        check=True,
        cwd=REPOSITORY_ROOT,
        env=environment,
    )

    evidence = tmp_path / "installed-evidence.json"
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--install-base",
            str(install_base),
            "--evidence",
            str(evidence),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(evidence.read_text(encoding="utf-8"))["valid"] is True
    for stage in STAGES:
        assert stage in result.stdout


def test_public_xacro_fault_contract_rejects_missing_parent_without_mutation(
    tmp_path: Path,
) -> None:
    fixture = REPOSITORY_ROOT / "scripts/fixtures/xacro/missing-wheel-parent.urdf.xacro"
    evidence = tmp_path / "fault-evidence.json"
    before = subprocess.run(
        ["sha256sum", str(fixture)], check=True, capture_output=True, text=True
    ).stdout
    result = subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--xacro",
            str(fixture),
            "--evidence",
            str(evidence),
            "--work-dir",
            str(tmp_path / "new-work-dir"),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
    )
    after = subprocess.run(
        ["sha256sum", str(fixture)], check=True, capture_output=True, text=True
    ).stdout

    assert result.returncode == 1
    assert "parent link [base_link]" in f"{result.stdout}{result.stderr}"
    assert json.loads(evidence.read_text(encoding="utf-8"))["valid"] is False
    assert before == after


def test_beginner_docs_invoke_the_matching_installed_stage() -> None:
    docs_root = REPOSITORY_ROOT / "docs/03_beginner"

    for document, stage in DOC_STAGES:
        content = (docs_root / document).read_text(encoding="utf-8")
        assert f"urdf/stages/{stage}" in content
        assert (
            "xacro examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro"
            not in content
        )


def test_stage_three_freezes_dimensions_and_runtime_observables() -> None:
    # Given: the stage installed for the beginner DiffDrive chapter.
    stage = PACKAGE_ROOT / "urdf/stages/03-diff-drive.xacro"

    # When: the public Xacro command expands it to the runtime robot description.
    expansion = subprocess.run(
        ["xacro", str(stage)],
        check=True,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
    )
    robot = ElementTree.fromstring(expansion.stdout)
    plugin = robot.find(".//plugin[@name='gz::sim::systems::DiffDrive']")
    wheel = robot.find(".//link[@name='left_wheel_link']/visual/geometry/cylinder")

    # Then: the installed stage and runtime gate expose the dimensions and motion
    # signals that the worked examples must preserve.
    assert plugin is not None
    assert wheel is not None
    assert plugin.findtext("wheel_radius") == "0.06"
    assert plugin.findtext("wheel_separation") == "0.38"
    assert wheel.attrib == {"radius": "0.06", "length": "0.04"}
    runtime_gate = (REPOSITORY_ROOT / "scripts/check_diff_drive.sh").read_text(
        encoding="utf-8"
    )
    assert "/model/tutorial_bot/cmd_vel" in runtime_gate
    assert "/model/tutorial_bot/odometry" in runtime_gate
    assert "pose_x > 0.05 && linear_x > 0.15" in runtime_gate
