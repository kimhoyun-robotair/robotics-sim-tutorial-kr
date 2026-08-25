#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final


ROOT: Final = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class Scenario:
    course: str
    name: str
    command: tuple[str, ...]


SCENARIOS: Final = (
    Scenario("beginner", "diff-drive", ("./scripts/check_diff_drive.sh",)),
    Scenario("beginner", "sensors", ("./scripts/check_sensors.sh",)),
    Scenario("beginner", "fuel", ("./scripts/check_fuel_world.sh",)),
    Scenario("beginner", "bridge", ("./scripts/check_ros_gz_bridge.sh",)),
    Scenario("intermediate", "launch", ("./scripts/check_intermediate_launch.sh",)),
    Scenario("intermediate", "sensors", ("./scripts/check_intermediate_sensors.sh",)),
    Scenario("intermediate", "control_tf", ("./scripts/check_intermediate_control_tf.sh",)),
    Scenario("intermediate", "multi_robot", ("./scripts/check_intermediate_multi_robot.sh",)),
    Scenario("intermediate", "nav2", ("./scripts/check_intermediate_nav2.sh",)),
    Scenario("advanced", "distance", ("./scripts/check_advanced_course.sh", "--scenario", "distance")),
    Scenario("advanced", "transport", ("./scripts/check_advanced_course.sh", "--scenario", "transport")),
    Scenario("advanced", "physics", ("./scripts/check_advanced_course.sh", "--scenario", "physics")),
    Scenario("advanced", "headless", ("./scripts/check_advanced_course.sh", "--scenario", "headless")),
)


def comma_set(raw: str) -> set[str]:
    return {value.strip() for value in raw.split(",") if value.strip()}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--course", required=True)
    result.add_argument("--scenarios", required=True)
    result.add_argument("--modes", default="nominal")
    result.add_argument("--evidence", required=True)
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    courses = comma_set(args.course)
    names = comma_set(args.scenarios)
    modes = comma_set(args.modes)
    if "all-required" in names:
        names = {scenario.name for scenario in SCENARIOS if scenario.course in courses}
    unknown_courses = courses - {"beginner", "intermediate", "advanced"}
    unknown_modes = modes - {"nominal", "fault"}
    selected = [scenario for scenario in SCENARIOS if scenario.course in courses and scenario.name in names]
    if unknown_courses or unknown_modes or not selected:
        print("invalid or empty matrix selection", file=sys.stderr)
        return 64
    output = Path(args.evidence)
    output.mkdir(parents=True, exist_ok=True)
    dispatches: list[dict[str, object]] = []
    overall_exit = 0
    for scenario in selected:
        for mode in sorted(modes):
            scenario_evidence = output / f"{scenario.course}-{scenario.name}-{mode}"
            command = [*scenario.command, "--evidence", str(scenario_evidence)]
            if mode == "fault":
                command.append("--expect-failure")
            exit_code: int | None = None
            if not args.dry_run:
                completed = subprocess.run(command, cwd=ROOT, check=False)
                exit_code = completed.returncode
                if exit_code != 0:
                    overall_exit = 1
            dispatches.append(
                {
                    "course": scenario.course,
                    "scenario": scenario.name,
                    "mode": mode,
                    "command": command,
                    "executed": not args.dry_run,
                    "exit": exit_code,
                }
            )
    report = {"schema_version": 1, "status": "pass" if overall_exit == 0 else "fail", "dispatches": dispatches}
    (output / "matrix.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
