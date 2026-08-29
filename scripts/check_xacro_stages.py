from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence
import argparse
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ElementTree


PACKAGE_NAME = "tutorial_bot_description"


@dataclass(frozen=True, slots=True)
class Inventory:
    links: frozenset[str]
    joints: frozenset[str]
    plugins: frozenset[str]
    sensors: frozenset[str]


@dataclass(frozen=True, slots=True)
class StageExpectation:
    name: str
    inventory: Inventory


class StageFailure(Exception):
    pass


BASE = Inventory(frozenset({"base_link"}), frozenset(), frozenset(), frozenset())
WHEELS = Inventory(
    frozenset(
        {"base_link", "left_wheel_link", "right_wheel_link", "caster_link"}
    ),
    frozenset({"left_wheel_joint", "right_wheel_joint", "caster_joint"}),
    frozenset(),
    frozenset(),
)
DIFF_DRIVE = Inventory(
    WHEELS.links,
    WHEELS.joints,
    frozenset(
        {
            "gz::sim::systems::DiffDrive",
            "gz::sim::systems::JointStatePublisher",
        }
    ),
    frozenset(),
)
FINAL = Inventory(
    frozenset(
        {
            "base_link",
            "left_wheel_link",
            "right_wheel_link",
            "caster_link",
            "lidar_link",
            "camera_link",
            "camera_optical_frame",
            "imu_link",
        }
    ),
    frozenset(
        {
            "left_wheel_joint",
            "right_wheel_joint",
            "caster_joint",
            "lidar_joint",
            "camera_joint",
            "camera_optical_joint",
            "imu_joint",
        }
    ),
    DIFF_DRIVE.plugins,
    frozenset({"lidar", "camera", "imu"}),
)
EXPECTATIONS = (
    StageExpectation("01-base.xacro", BASE),
    StageExpectation("02-wheels-and-joints.xacro", WHEELS),
    StageExpectation("03-diff-drive.xacro", DIFF_DRIVE),
    StageExpectation("04-sensors-final.xacro", FINAL),
)


def command_output(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(arguments, check=False, capture_output=True, text=True)


def expand_and_check(xacro_path: Path, output_path: Path) -> Inventory:
    expansion = command_output(("xacro", str(xacro_path)))
    if expansion.returncode != 0:
        raise StageFailure(f"xacro failed for {xacro_path}: {expansion.stderr.strip()}")
    output_path.write_text(expansion.stdout, encoding="utf-8")
    urdf_check = command_output(("check_urdf", str(output_path)))
    if urdf_check.returncode != 0:
        raise StageFailure(
            f"check_urdf failed for {xacro_path}: {urdf_check.stderr.strip()}"
        )
    try:
        root = ElementTree.fromstring(expansion.stdout)
    except ElementTree.ParseError as error:
        raise StageFailure(
            f"expanded XML is invalid for {xacro_path}: {error}"
        ) from error
    return Inventory(
        frozenset(element.attrib["name"] for element in root.findall("link")),
        frozenset(element.attrib["name"] for element in root.findall("joint")),
        frozenset(element.attrib["name"] for element in root.findall(".//plugin")),
        frozenset(element.attrib["name"] for element in root.findall(".//sensor")),
    )


def assert_inventory(stage_name: str, actual: Inventory, expected: Inventory) -> None:
    if actual != expected:
        raise StageFailure(
            f"{stage_name} inventory mismatch: expected={expected}, actual={actual}"
        )


def check_stages(install_base: Path, work_dir: Path) -> None:
    candidates = (
        install_base / "share" / PACKAGE_NAME / "urdf",
        install_base / PACKAGE_NAME / "share" / PACKAGE_NAME / "urdf",
    )
    urdf_dir = next(
        (
            candidate
            for candidate in candidates
            if (candidate / "tutorial_bot.urdf.xacro").is_file()
        ),
        None,
    )
    if urdf_dir is None:
        raise StageFailure(f"installed canonical Xacro is missing under: {candidates}")
    canonical = urdf_dir / "tutorial_bot.urdf.xacro"
    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"PASS installed stages: {urdf_dir / 'stages'}")
    inventories: dict[str, Inventory] = {}
    for expectation in EXPECTATIONS:
        stage = urdf_dir / "stages" / expectation.name
        if not stage.is_file():
            raise StageFailure(f"installed stage is missing: {stage}")
        inventory = expand_and_check(stage, work_dir / f"{expectation.name}.urdf")
        assert_inventory(expectation.name, inventory, expectation.inventory)
        inventories[expectation.name] = inventory
        print(
            f"PASS {expectation.name}: links={len(inventory.links)} "
            f"joints={len(inventory.joints)} plugins={len(inventory.plugins)} "
            f"sensors={len(inventory.sensors)}"
        )
    canonical_inventory = expand_and_check(
        canonical, work_dir / "tutorial_bot.canonical.urdf"
    )
    assert_inventory("tutorial_bot.urdf.xacro", canonical_inventory, FINAL)
    if inventories["04-sensors-final.xacro"] != canonical_inventory:
        raise StageFailure(
            "final stage inventory differs from the installed canonical Xacro"
        )
    print("PASS 04-sensors-final.xacro matches tutorial_bot.urdf.xacro")


def check_fault_fixture(fixture: Path, work_dir: Path) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    expanded = command_output(("xacro", str(fixture)))
    if expanded.returncode != 0:
        raise StageFailure(f"fault fixture did not expand: {expanded.stderr.strip()}")
    output = work_dir / "missing-wheel-parent.urdf"
    output.write_text(expanded.stdout, encoding="utf-8")
    urdf_check = command_output(("check_urdf", str(output)))
    diagnostic = f"{urdf_check.stdout}{urdf_check.stderr}"
    if urdf_check.returncode == 0:
        raise StageFailure("fault fixture unexpectedly passed check_urdf")
    if "parent link [base_link]" not in diagnostic:
        raise StageFailure(
            f"fault fixture missed parent diagnostic: {diagnostic.strip()}"
        )
    print(diagnostic.strip())
    print("PASS missing-wheel-parent fixture rejected")


def write_evidence(
    evidence: Path | None, valid: bool, subject: Path, diagnostic: str
) -> None:
    if evidence is None:
        return
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        json.dumps(
            {
                "valid": valid,
                "subject": str(subject),
                "diagnostic": diagnostic,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-base", type=Path)
    parser.add_argument("--fault-fixture", type=Path)
    parser.add_argument("--xacro", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--work-dir", type=Path)
    options = parser.parse_args(arguments)
    subjects = tuple(
        subject
        for subject in (options.install_base, options.fault_fixture, options.xacro)
        if subject is not None
    )
    if len(subjects) != 1:
        parser.error(
            "provide exactly one of --install-base, --fault-fixture, or --xacro"
        )
    subject = subjects[0]
    with tempfile.TemporaryDirectory(prefix="check-xacro-stages-") as temporary_dir:
        work_dir = options.work_dir or Path(temporary_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        try:
            if options.install_base is not None:
                check_stages(options.install_base, work_dir)
            elif options.fault_fixture is not None:
                check_fault_fixture(options.fault_fixture, work_dir)
            else:
                expand_and_check(options.xacro, work_dir / f"{options.xacro.name}.urdf")
                print(f"PASS {options.xacro}")
        except StageFailure as error:
            print(f"FAIL: {error}", file=sys.stderr)
            write_evidence(options.evidence, False, subject, str(error))
            return 1
    write_evidence(options.evidence, True, subject, "validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
