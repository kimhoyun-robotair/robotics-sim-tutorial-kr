#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Final, Literal


DEPENDENCY_CLOSURE: Final = (
    "tutorial_bot_plugins",
    "tutorial_bot_tests",
    "tutorial_bot_gazebo",
    "tutorial_bot_description",
    "tutorial_bot_bringup",
)
WORKSPACE_PREREQUISITES: Final = ("tutorial_bot_control",)
BUILD_FAILURE: Final = 69
Phase = Literal["red", "green"]


@dataclass(frozen=True, slots=True)
class PhaseRequest:
    task: int
    phase: Phase
    packages: tuple[str, ...]
    selector: str
    test_paths: tuple[Path, ...]
    attempt_dir: Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, required=True)
    parser.add_argument("--phase", choices=("red", "green"), required=True)
    parser.add_argument("--packages", required=True)
    parser.add_argument("--selector", required=True)
    parser.add_argument("--test-path", action="append", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    return parser


def _request() -> PhaseRequest:
    arguments = _parser().parse_args()
    packages = tuple(item for item in arguments.packages.split(",") if item)
    return PhaseRequest(
        task=arguments.task,
        phase=arguments.phase,
        packages=packages,
        selector=arguments.selector,
        test_paths=tuple(arguments.test_path),
        attempt_dir=arguments.attempt_dir.resolve(),
    )


def _run(command: list[str], log_path: Path, cwd: Path) -> int:
    with log_path.open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                check=False,
                stdout=stream,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            stream.write("command timed out after 180 seconds\n")
            return 124
    return result.returncode


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, str | int | list[dict[str, str]]]) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def _write_phase_metadata(
    request: PhaseRequest, classification: str, test_exit: int
) -> None:
    parent_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _write_json(
        request.attempt_dir / f"{request.phase}-metadata.json",
        {
            "task": request.task,
            "phase": request.phase,
            "classification": classification,
            "parent_sha": parent_sha,
            "selector": request.selector,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "test_exit": test_exit,
            "test_sources": [
                {"path": str(path), "sha256": _sha256(path)}
                for path in request.test_paths
            ],
        },
    )


def main() -> int:
    request = _request()
    request.attempt_dir.mkdir(parents=True, exist_ok=True)
    workspace = Path(__file__).resolve().parents[1] / "examples/ros2_ws"
    phase = request.phase
    build_log = request.attempt_dir / f"{phase}-build.log"
    test_log = request.attempt_dir / f"{phase}-test.log"
    result_log = request.attempt_dir / f"{phase}-test-result.log"
    prerequisite_command = [
        "colcon", "--log-base", str(request.attempt_dir / f"{phase}-prerequisite-log"),
        "build",
        "--build-base", str(request.attempt_dir / f"{phase}-build"),
        "--install-base", str(request.attempt_dir / f"{phase}-install"),
        "--packages-select", *WORKSPACE_PREREQUISITES,
        "--cmake-args", "-DPython3_EXECUTABLE=/usr/bin/python3",
    ]
    prerequisite_exit = _run(
        prerequisite_command,
        request.attempt_dir / f"{phase}-prerequisite-build.log",
        workspace,
    )
    if prerequisite_exit != 0:
        _write_phase_metadata(request, "build_failure", prerequisite_exit)
        return BUILD_FAILURE
    build_command = [
        "colcon", "--log-base", str(request.attempt_dir / f"{phase}-log"),
        "build",
        "--build-base", str(request.attempt_dir / f"{phase}-build"),
        "--install-base", str(request.attempt_dir / f"{phase}-install"),
        "--packages-select", *DEPENDENCY_CLOSURE,
        "--cmake-args", "-DBUILD_TESTING=ON", "-DPython3_EXECUTABLE=/usr/bin/python3",
    ]
    build_exit = _run(build_command, build_log, workspace)
    if build_exit != 0:
        _write_phase_metadata(request, "build_failure", build_exit)
        return BUILD_FAILURE

    test_command = [
        "colcon", "--log-base", str(request.attempt_dir / f"{phase}-test-log"),
        "test",
        "--build-base", str(request.attempt_dir / f"{phase}-build"),
        "--install-base", str(request.attempt_dir / f"{phase}-install"),
        "--packages-select", *request.packages,
        "--ctest-args", "-R", request.selector,
        "--event-handlers", "console_direct+",
        "--return-code-on-test-failure",
    ]
    test_exit = _run(test_command, test_log, workspace)
    result_command = [
        "colcon", "test-result", "--verbose",
        "--test-result-base", str(request.attempt_dir / f"{phase}-build"),
    ]
    result_exit = _run(result_command, result_log, workspace)
    observed_exit = test_exit if test_exit != 0 else result_exit
    expected = (phase == "red" and observed_exit != 0) or (phase == "green" and observed_exit == 0)
    classification = phase if expected else "phase_mismatch"
    _write_phase_metadata(request, classification, observed_exit)
    if phase == "red" and expected:
        return 1
    if phase == "green" and expected:
        return 0
    return BUILD_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
