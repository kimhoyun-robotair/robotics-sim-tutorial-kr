from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from scripts.course_matrix_contract import Scenario, expected_exit, scenario_command
elif __package__:
    from .course_matrix_contract import Scenario, expected_exit, scenario_command
else:
    from course_matrix_contract import Scenario, expected_exit, scenario_command

ROOT: Final = Path(__file__).resolve().parents[1]


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
    if required:
        return all(value == "true" for value in required)
    cleanup = path / "cleanup.json"
    if not cleanup.is_file():
        return False
    receipt = json.loads(cleanup.read_text(encoding="utf-8"))
    return (
        receipt.get("survivors") in ([], 0)
        and receipt.get("identity_mismatch") is not True
    )


def observable_passed(
    scenario: Scenario, mode: str, path: Path
) -> tuple[bool, Mapping[str, object]]:
    if scenario.course == "intermediate" and scenario.name == "launch":
        values = key_values(
            path / ("fault-observable.log" if mode == "fault" else "controllers.log")
        )
        passed = (
            int(values.get("launch_exit", "0")) != 0
            if mode == "fault"
            else (path / "entities.log").is_file() and (path / "topics.log").is_file()
        )
    elif scenario.course == "intermediate" and scenario.name == "sensors":
        result_path = path / "collection.json"
        values = (
            json.loads(result_path.read_text(encoding="utf-8"))
            if result_path.is_file()
            else {}
        )
        passed = values.get("passed") is (mode == "nominal") and bool(
            values.get("counts")
        )
    elif scenario.course == "intermediate" and scenario.name == "control_tf":
        values = key_values(
            path / ("missing-frame.log" if mode == "fault" else "displacement.log")
        )
        passed = (
            int(values.get("lookup_exit", "0")) != 0
            if mode == "fault"
            else float(values.get("displacement_m", "0")) >= 0.30
        )
    elif scenario.course == "intermediate" and scenario.name == "multi_robot":
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
    elif scenario.course == "intermediate" and scenario.name == "nav2":
        values = key_values(path / "run-1/status.log")
        expected = "6" if mode == "fault" else "4"
        passed = (
            values.get("status") == expected
            and (path / "run-1/observable.log").is_file()
        )
    else:
        artifact = path / (
            "scenario.json" if scenario.course == "advanced" else "result.json"
        )
        if artifact.is_file():
            values = json.loads(artifact.read_text(encoding="utf-8"))
        elif mode == "fault" and (path / "cleanup.json").is_file():
            values = json.loads((path / "cleanup.json").read_text(encoding="utf-8"))
        else:
            values = {}
        passed = bool(values) or scenario.name == "diff-drive"
    return passed and cleanup_passed(path), values


def run_scenario(
    scenario: Scenario, mode: str, evidence: Path, install: Path, overlay: Path
) -> tuple[int, bool, Mapping[str, object], Path]:
    effective_install = (
        str(install)
        if scenario.course == "intermediate"
        else os.environ.get("TUTORIAL_INSTALL_BASE", str(install))
    )
    command = [
        effective_install if value == "__INSTALL_BASE__" else value
        for value in scenario_command(scenario, mode, evidence)
    ]
    cleanup = evidence / "matrix-wrapper-cleanup.json"
    environment = {
        **os.environ,
        "TUTORIAL_INSTALL_BASE": effective_install,
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
