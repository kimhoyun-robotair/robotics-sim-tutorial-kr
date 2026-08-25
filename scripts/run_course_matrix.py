#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from scripts.course_matrix_contract import SCENARIOS, comma_set, timing_budget
    from scripts.course_matrix_execution import run_lane
elif __package__:
    from .course_matrix_contract import SCENARIOS, comma_set, timing_budget
    from .course_matrix_execution import run_lane
else:
    from course_matrix_contract import SCENARIOS, comma_set, timing_budget
    from course_matrix_execution import run_lane

ROOT: Final = Path(__file__).resolve().parents[1]
INTERMEDIATE_PACKAGES: Final = (
    "tutorial_bot_description",
    "tutorial_bot_gazebo",
    "tutorial_bot_control",
    "tutorial_bot_bringup",
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--course", required=True)
    result.add_argument("--scenarios", required=True)
    result.add_argument("--modes", default="nominal")
    result.add_argument("--evidence", required=True)
    result.add_argument("--dry-run", action="store_true")
    return result


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
    output = Path(args.evidence).resolve()
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
        execution_schedule = (
            "control_tf+multi_robot parallel; remaining lanes sequential"
        )
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
