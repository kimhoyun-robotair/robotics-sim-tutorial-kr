#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[1]
INTERMEDIATE_PACKAGES: Final = (
    "tutorial_bot_description",
    "tutorial_bot_gazebo",
    "tutorial_bot_control",
    "tutorial_bot_bringup",
)
INTERMEDIATE_TIMING_BUDGET_SECONDS: Final = 270.0


@dataclass(frozen=True, slots=True)
class Scenario:
    course: str
    name: str
    command: tuple[str, ...]
    fault_arguments: tuple[str, ...] = ("--expect-failure",)
    fault_exit: int = 0
    observable_contract: str = "checker_exit_and_cleanup"


SCENARIOS: Final = (
    Scenario("beginner", "diff-drive", ("./scripts/check_diff_drive.sh",)),
    Scenario("beginner", "sensors", ("./scripts/check_sensors.sh",)),
    Scenario("beginner", "fuel", ("./scripts/check_fuel_world.sh",)),
    Scenario("beginner", "bridge", ("./scripts/check_ros_gz_bridge.sh",)),
    Scenario(
        "intermediate",
        "launch",
        ("./scripts/check_intermediate_launch.sh",),
        ("--world", "missing-world", "--expect-failure"),
        observable_contract="entity_topics_controllers_or_missing_world",
    ),
    Scenario(
        "intermediate",
        "sensors",
        ("./scripts/check_intermediate_sensors.sh",),
        ("--expected-width", "1"),
        1,
        "sensor_statistics_json",
    ),
    Scenario(
        "intermediate",
        "control_tf",
        ("./scripts/check_intermediate_control_tf.sh",),
        ("--expect-missing-frame", "missing_link"),
        1,
        "controller_displacement_or_missing_tf",
    ),
    Scenario(
        "intermediate",
        "multi_robot",
        ("./scripts/check_intermediate_multi_robot.sh",),
        ("--robot2-name", "robot1"),
        1,
        "isolated_displacements_or_identity_collision",
    ),
    Scenario(
        "intermediate",
        "nav2",
        ("./scripts/check_intermediate_nav2.sh", "--fresh-build"),
        ("--goal-name", "unreachable_goal.yaml", "--expect-status", "6"),
        observable_contract="nav2_status_tf_and_live_topics",
    ),
    Scenario(
        "advanced",
        "distance",
        ("./scripts/check_advanced_course.sh", "--scenario", "distance"),
    ),
    Scenario(
        "advanced",
        "transport",
        ("./scripts/check_advanced_course.sh", "--scenario", "transport"),
    ),
    Scenario(
        "advanced",
        "physics",
        ("./scripts/check_advanced_course.sh", "--scenario", "physics"),
    ),
    Scenario(
        "advanced",
        "headless",
        ("./scripts/check_advanced_course.sh", "--scenario", "headless"),
    ),
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


def scenario_command(scenario: Scenario, mode: str, evidence: Path) -> list[str]:
    command = [*scenario.command, "--evidence", str(evidence)]
    return [*command, *(scenario.fault_arguments if mode == "fault" else ())]


def expected_exit(scenario: Scenario, mode: str) -> int:
    return scenario.fault_exit if mode == "fault" else 0


def timing_budget(
    courses: set[str], names: set[str], modes: set[str], execute: bool
) -> float | None:
    required_names = {
        scenario.name for scenario in SCENARIOS if scenario.course == "intermediate"
    }
    if execute and courses == {"intermediate"} and names == required_names and modes == {
        "nominal",
        "fault",
    }:
        return INTERMEDIATE_TIMING_BUDGET_SECONDS
    return None


def shared_build(output: Path, execute: bool) -> tuple[dict[str, object], Path]:
    install = output / "shared-install"
    command = [
        "colcon",
        "--log-base",
        str(output / "shared-log"),
        "build",
        "--base-paths",
        str(ROOT / "examples/ros2_ws/src"),
        "--packages-select",
        *INTERMEDIATE_PACKAGES,
        "--build-base",
        str(output / "shared-build"),
        "--install-base",
        str(install),
        "--event-handlers",
        "console_direct+",
    ]
    record: dict[str, object] = {
        "count": 1,
        "command": command,
        "executed": execute,
        "exit": None,
    }
    if execute:
        shell_command = (
            "export PATH=/opt/ros/jazzy/bin:/usr/bin:/bin; "
            f"source /opt/ros/jazzy/setup.bash && exec {shlex.join(command)}"
        )
        cleanup = output / "shared-build-cleanup.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/run_owned_process.py"),
                "--timeout",
                "120",
                "--cleanup-receipt",
                str(cleanup),
                "--",
                "bash",
                "-lc",
                shell_command,
            ],
            cwd=ROOT,
            check=False,
        )
        receipt = (
            json.loads(cleanup.read_text(encoding="utf-8")) if cleanup.is_file() else {}
        )
        record["exit"] = receipt.get("dut_exit", completed.returncode)
        record["cleanup"] = str(cleanup)
    return record, install


def shared_overlay(output: Path, execute: bool) -> tuple[dict[str, object], Path]:
    root = output / "shared-overlay"
    debs = root / "debs"
    extracted = root / "root"
    command = ["apt-get", "download", "ros-jazzy-ros2controlcli"]
    record: dict[str, object] = {
        "count": 1,
        "command": command,
        "executed": execute,
        "exit": None,
    }
    if execute:
        debs.mkdir(parents=True, exist_ok=True)
        extracted.mkdir(parents=True, exist_ok=True)
        cache = Path("/tmp/gazebo-course-matrix-cache")
        cache.mkdir(parents=True, exist_ok=True)
        cached_packages = sorted(cache.glob("ros-jazzy-ros2controlcli_*.deb"))
        completed = subprocess.CompletedProcess(command, 0, "", "")
        if not cached_packages:
            completed = subprocess.run(
                command, cwd=cache, check=False, capture_output=True, text=True
            )
            cached_packages = sorted(cache.glob("ros-jazzy-ros2controlcli_*.deb"))
        for package in cached_packages:
            shutil.copy2(package, debs / package.name)
        (root / "download.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        exit_code = completed.returncode if cached_packages else 1
        record["cache_hit"] = not completed.stdout and not completed.stderr
        record["cache"] = str(cache)
        for package in sorted(debs.glob("*.deb")):
            extracted_package = subprocess.run(
                ["dpkg-deb", "-x", str(package), str(extracted)], check=False
            )
            if extracted_package.returncode != 0:
                exit_code = extracted_package.returncode
        record["exit"] = exit_code
    return record, extracted


def key_values(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {
        key: value
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if "=" in line
        for key, value in (line.split("=", 1),)
    }


def cleanup_passed(path: Path) -> bool:
    values = key_values(path / "cleanup.log")
    required = [
        value for key, value in values.items() if key.endswith(("_ok", "_absent"))
    ]
    return bool(required) and all(value == "true" for value in required)


def observable_passed(
    scenario: Scenario, mode: str, path: Path
) -> tuple[bool, Mapping[str, object]]:
    if scenario.name == "launch":
        values = key_values(
            path / ("fault-observable.log" if mode == "fault" else "controllers.log")
        )
        passed = (
            int(values.get("launch_exit", "0")) != 0
            if mode == "fault"
            else (path / "entities.log").is_file() and (path / "topics.log").is_file()
        )
    elif scenario.name == "sensors":
        result_path = path / "collection.json"
        values = (
            json.loads(result_path.read_text(encoding="utf-8"))
            if result_path.is_file()
            else {}
        )
        passed = values.get("passed") is (mode == "nominal") and bool(
            values.get("counts")
        )
    elif scenario.name == "control_tf":
        values = key_values(
            path / ("missing-frame.log" if mode == "fault" else "displacement.log")
        )
        passed = (
            int(values.get("lookup_exit", "0")) != 0
            if mode == "fault"
            else float(values.get("displacement_m", "0")) >= 0.30
        )
    elif scenario.name == "multi_robot":
        values = key_values(
            path / ("name-collision.log" if mode == "fault" else "displacements.log")
        )
        passed = (
            int(values.get("launch_exit", "0")) != 0
            and values.get("readiness_reached") == "false"
            if mode == "fault"
            else float(values.get("robot1_command_robot1_displacement_m", "0")) >= 0.30
            and float(values.get("robot2_command_robot2_displacement_m", "0")) >= 0.30
        )
    elif scenario.name == "nav2":
        values = key_values(path / "run-1/status.log")
        expected = "6" if mode == "fault" else "4"
        passed = (
            values.get("status") == expected
            and (path / "run-1/observable.log").is_file()
        )
    else:
        values = {}
        passed = True
    return passed and cleanup_passed(path), values


def run_scenario(
    scenario: Scenario, mode: str, evidence: Path, install: Path, overlay: Path
) -> tuple[int, bool, Mapping[str, object], Path]:
    command = scenario_command(scenario, mode, evidence)
    cleanup = evidence / "matrix-wrapper-cleanup.json"
    environment = {
        **os.environ,
        "TUTORIAL_INSTALL_BASE": str(install),
        "TUTORIAL_BOT_DEPENDENCY_OVERLAY": str(overlay),
    }
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_owned_process.py"),
            "--timeout",
            "240",
            "--cleanup-receipt",
            str(cleanup),
            "--",
            *command,
        ],
        cwd=ROOT,
        env=environment,
        check=False,
    )
    receipt = (
        json.loads(cleanup.read_text(encoding="utf-8")) if cleanup.is_file() else {}
    )
    exit_code = int(receipt.get("dut_exit", completed.returncode))
    observable, values = observable_passed(scenario, mode, evidence)
    return exit_code, observable, values, cleanup


def run_lane(
    scenario: Scenario,
    modes: set[str],
    output: Path,
    install: Path,
    overlay: Path,
    execute: bool,
) -> tuple[list[dict[str, object]], bool]:
    records: list[dict[str, object]] = []
    passed = True
    for mode in sorted(modes):
        evidence = output / f"{scenario.course}-{scenario.name}-{mode}"
        command = scenario_command(scenario, mode, evidence)
        exit_code: int | None = None
        observable = False
        values: Mapping[str, object] = {}
        cleanup: Path | None = None
        if execute:
            exit_code, observable, values, cleanup = run_scenario(
                scenario, mode, evidence, install, overlay
            )
            passed = (
                passed and exit_code == expected_exit(scenario, mode) and observable
            )
        records.append(
            {
                "course": scenario.course,
                "scenario": scenario.name,
                "mode": mode,
                "command": command,
                "executed": execute,
                "exit": exit_code,
                "expected_exit": expected_exit(scenario, mode),
                "observable_contract": scenario.observable_contract,
                "observable_passed": observable if execute else None,
                "parsed_observables": values,
                "cleanup": str(cleanup) if cleanup else None,
            }
        )
    return records, passed


def main() -> int:
    started = time.monotonic()
    args = parser().parse_args()
    courses = comma_set(args.course)
    names = comma_set(args.scenarios)
    modes = comma_set(args.modes)
    if "all-required" in names:
        names = {scenario.name for scenario in SCENARIOS if scenario.course in courses}
    selected = [
        scenario
        for scenario in SCENARIOS
        if scenario.course in courses and scenario.name in names
    ]
    if (
        courses - {"beginner", "intermediate", "advanced"}
        or modes - {"nominal", "fault"}
        or not selected
    ):
        print("invalid or empty matrix selection", file=sys.stderr)
        return 64
    output = Path(args.evidence)
    output.mkdir(parents=True, exist_ok=True)
    build_record: dict[str, object] = {"count": 0, "executed": False, "exit": None}
    overlay_record: dict[str, object] = {"count": 0, "executed": False, "exit": None}
    install = output / "shared-install"
    overlay = output / "shared-overlay/root"
    if any(scenario.course == "intermediate" for scenario in selected):
        build_record, install = shared_build(output, not args.dry_run)
        overlay_record, overlay = shared_overlay(output, not args.dry_run)
    overall_exit = (
        0
        if build_record.get("exit") in (None, 0)
        and overlay_record.get("exit") in (None, 0)
        else 1
    )
    execute = not args.dry_run and overall_exit == 0
    lane_arguments = [
        (scenario, modes, output, install, overlay, execute) for scenario in selected
    ]
    execution_schedule = "sequential"
    if (
        execute
        and "fault" in modes
        and len(selected) > 1
        and all(scenario.course == "intermediate" for scenario in selected)
        and sum(scenario.name in {"control_tf", "multi_robot"} for scenario in selected)
        == 2
    ):
        parallel_arguments = [
            values
            for values in lane_arguments
            if values[0].name in {"control_tf", "multi_robot"}
        ]
        dedicated_arguments = [
            values for values in lane_arguments if values not in parallel_arguments
        ]
        with ThreadPoolExecutor(max_workers=len(parallel_arguments)) as executor:
            parallel_results = list(
                executor.map(lambda values: run_lane(*values), parallel_arguments)
            )
        lane_results = [
            *parallel_results,
            *(run_lane(*values) for values in dedicated_arguments),
        ]
        execution_schedule = "control_tf+multi_robot parallel; remaining lanes sequential"
    else:
        lane_results = [run_lane(*values) for values in lane_arguments]
    dispatches = [record for records, _passed in lane_results for record in records]
    if any(not passed for _records, passed in lane_results):
        overall_exit = 1
    elapsed_seconds = round(time.monotonic() - started, 3)
    budget_seconds = timing_budget(courses, names, modes, execute)
    timing_passed = budget_seconds is None or elapsed_seconds <= budget_seconds
    if not timing_passed:
        overall_exit = 1
    report = {
        "schema_version": 1,
        "status": "pass" if overall_exit == 0 else "fail",
        "shared_build": build_record,
        "dependency_overlay": overlay_record,
        "execution_schedule": execution_schedule,
        "timing": {
            "elapsed_seconds": elapsed_seconds,
            "budget_seconds": budget_seconds,
            "passed": timing_passed,
        },
        "dispatches": dispatches,
    }
    (output / "matrix.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return overall_exit


if __name__ == "__main__":
    raise SystemExit(main())
