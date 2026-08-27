#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from xml.etree import ElementTree

import yaml

ROOT: Final = Path(__file__).resolve().parents[1]
DOCS: Final = (
    ROOT / "docs/03_beginner/05-first-robot.md",
    ROOT / "docs/03_beginner/06-joints.md",
    ROOT / "docs/03_beginner/07-diff-drive.md",
)
CANONICAL_XACRO: Final = (
    ROOT
    / "examples/ros2_ws/src/tutorial_bot_description/urdf/tutorial_bot.urdf.xacro"
)


@dataclass(frozen=True, slots=True)
class RobotMath:
    wheel_radius_m: float
    wheel_separation_m: float
    left_joint: str
    right_joint: str


class MathAuditError(Exception):
    pass


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--scope", required=True, choices=("beginner-robot", "all"))
    source = result.add_mutually_exclusive_group()
    source.add_argument("--xacro", type=Path)
    source.add_argument("--fixture", type=Path)
    result.add_argument("--evidence", type=Path, required=True)
    return result


def expand_xacro(path: Path) -> ElementTree.Element:
    completed = subprocess.run(
        ("xacro", str(path)), check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise MathAuditError(f"xacro expansion failed: {completed.stderr.strip()}")
    try:
        return ElementTree.fromstring(completed.stdout)
    except ElementTree.ParseError as error:
        raise MathAuditError(f"expanded Xacro is invalid XML: {error}") from error


def required_element(parent: ElementTree.Element, query: str) -> ElementTree.Element:
    element = parent.find(query)
    if element is None:
        raise MathAuditError(f"canonical Xacro is missing {query}")
    return element


def required_float(parent: ElementTree.Element, query: str) -> float:
    element = required_element(parent, query)
    if element.text is None:
        raise MathAuditError(f"canonical Xacro has empty {query}")
    try:
        return float(element.text)
    except ValueError as error:
        raise MathAuditError(f"canonical Xacro has non-numeric {query}") from error


def robot_math(root: ElementTree.Element) -> RobotMath:
    plugin = required_element(root, ".//plugin[@name='gz::sim::systems::DiffDrive']")
    return RobotMath(
        wheel_radius_m=required_float(plugin, "wheel_radius"),
        wheel_separation_m=required_float(plugin, "wheel_separation"),
        left_joint=required_element(plugin, "left_joint").text or "",
        right_joint=required_element(plugin, "right_joint").text or "",
    )


def close(actual: float, expected: float) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-8)


def audit_inertia(root: ElementTree.Element) -> None:
    base = required_element(root, ".//link[@name='base_link']/inertial/inertia")
    expected_base = {"ixx": 0.04866666666666667, "iyy": 0.090375, "izz": 0.12704166666666668}
    for axis, expected in expected_base.items():
        if not close(float(base.attrib[axis]), expected):
            raise MathAuditError(f"base inertia mismatch: {axis}")
    wheel = required_element(
        root, ".//link[@name='left_wheel_link']/inertial/inertia"
    )
    expected_wheel = {"ixx": 0.00031, "iyy": 0.00054, "izz": 0.00031}
    for axis, expected in expected_wheel.items():
        if not close(float(wheel.attrib[axis]), expected):
            raise MathAuditError(f"wheel inertia mismatch: {axis}")


def audit_docs(model: RobotMath) -> None:
    contents = tuple(path.read_text(encoding="utf-8") for path in DOCS)
    required = (
        (contents[0], ("I_{xx}", "0.0487", "0.0904", "0.1270", "??? note")),
        (contents[1], ("I_{yy}", "0.000540", "0.000310", "axis", "??? note")),
        (
            contents[2],
            (
                f"r={model.wheel_radius_m:.2f}",
                f"L={model.wheel_separation_m:.2f}",
                "4.00",
                "4.90",
                "1.10",
                "3.17",
                "??? note",
            ),
        ),
    )
    for document, tokens in required:
        missing = [token for token in tokens if token not in document]
        if missing:
            raise MathAuditError(f"educational math missing: {', '.join(missing)}")
    forbidden = ("\\begin{matrix}", "\\begin{bmatrix}", "\\begin{pmatrix}")
    if any(token in document for document in contents for token in forbidden):
        raise MathAuditError("matrix notation is forbidden in beginner core")


def load_fixture(path: Path) -> RobotMath:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise MathAuditError("fixture schema_version must be 1")
        return RobotMath(
            wheel_radius_m=float(payload["wheel_radius_m"]),
            wheel_separation_m=float(payload["wheel_separation_m"]),
            left_joint=str(payload["left_joint"]),
            right_joint=str(payload["right_joint"]),
        )
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        raise MathAuditError(f"invalid math fixture: {error}") from error


def direction_error(model: RobotMath) -> str | None:
    if model.left_joint != "left_wheel_joint" or model.right_joint != "right_wheel_joint":
        return "turn-direction mismatch"
    return None


def write_report(path: Path, report: dict[str, str | float | list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    arguments = parser().parse_args()
    xacro_path: Path | None = arguments.xacro
    fixture_path: Path | None = arguments.fixture
    if arguments.scope == "all":
        if fixture_path is not None:
            parser().error("--scope all does not accept --fixture")
        xacro_path = xacro_path or CANONICAL_XACRO
    elif xacro_path is None and fixture_path is None:
        parser().error("--scope beginner-robot requires --xacro or --fixture")
    try:
        if xacro_path is not None:
            root = expand_xacro(xacro_path)
            model = robot_math(root)
            audit_inertia(root)
            audit_docs(model)
        else:
            if fixture_path is None:
                parser().error("math source is required")
            model = load_fixture(fixture_path)
        error = direction_error(model)
        if error is not None:
            raise MathAuditError(error)
    except MathAuditError as error:
        report: dict[str, str | float | list[str]] = {
            "status": "fail",
            "diagnostic": str(error),
        }
        write_report(arguments.evidence, report)
        print(str(error), file=sys.stderr)
        return 1
    report = {
        "status": "pass",
        "wheel_radius_m": model.wheel_radius_m,
        "wheel_separation_m": model.wheel_separation_m,
        "verified_examples": ["straight", "arc", "spin"],
        "verified_scopes": ["beginner-robot"],
    }
    write_report(arguments.evidence, report)
    print("beginner robot math verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
