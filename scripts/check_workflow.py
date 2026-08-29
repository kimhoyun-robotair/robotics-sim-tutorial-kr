#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ALLOWED_ROS_ACTIONS = {
    "actions/cache@v4",
    "actions/checkout@v4",
    "actions/upload-artifact@v4",
}
SELECTED_TEST_PATTERN = (
    "^(advanced_contract|advanced_framework_cli|advanced_headless_integration|"
    "rover_examples|diagnostics_distance|diagnostics_enable_reset|"
    "diagnostics_enable_reset_concurrency|diagnostics_model_lifecycle|"
    "diagnostics_physics_cadence)$"
)
type Step = dict[str, str]
type JobValue = str | list[Step] | dict[str, str]
type Job = dict[str, JobValue]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("workflow", type=Path)
    result.add_argument("--expect-runner", required=True)
    result.add_argument("--expect-timeout", required=True, type=int)
    return result


def action_names(steps: list[dict[str, str]]) -> set[str]:
    return {step["uses"] for step in steps if "uses" in step}


def steps(job: Job) -> list[Step]:
    value = job.get("steps", [])
    match value:
        case list():
            return value
        case str() | dict():
            return []


def string_mapping(job: Job, key: str) -> dict[str, str]:
    value = job.get(key, {})
    match value:
        case dict():
            return value
        case str() | list():
            return {}


def validate_pages(jobs: dict[str, Job]) -> list[str]:
    errors: list[str] = []
    build = jobs.get("build", {})
    deploy = jobs.get("deploy", {})
    build_actions = action_names(steps(build))
    deploy_actions = action_names(steps(deploy))
    required_build = {
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v3",
    }
    if build.get("runs-on") != "ubuntu-latest":
        errors.append("Pages build runner changed")
    if not required_build.issubset(build_actions):
        errors.append("Pages build actions changed")
    main_only_actions = {
        "actions/configure-pages@v5",
        "actions/upload-pages-artifact@v3",
    }
    for step in steps(build):
        if (
            step.get("uses") in main_only_actions
            and step.get("if") != "github.ref == 'refs/heads/main'"
        ):
            errors.append("Pages setup and artifact upload must run only on main")
    if deploy.get("needs") != "build":
        errors.append("Pages deploy must depend only on build")
    if "actions/deploy-pages@v4" not in deploy_actions:
        errors.append("Pages deploy action changed")
    return errors


def validate_ros(job: Job, runner: str, timeout: int) -> list[str]:
    errors: list[str] = []
    job_steps = steps(job)
    actions = action_names(job_steps)
    run_text = "\n".join(step.get("run", "") for step in job_steps)
    if job.get("runs-on") != runner:
        errors.append(f"ROS job runner must be {runner}")
    if job.get("timeout-minutes") != str(timeout):
        errors.append(f"ROS job timeout must be {timeout}")
    if job.get("permissions") != {"contents": "read"}:
        errors.append("ROS job must have contents: read as its only permission")
    if not actions.issubset(ALLOWED_ROS_ACTIONS):
        errors.append("ROS job uses an unapproved or unpinned action")
    if "actions/upload-artifact@v4" not in actions:
        errors.append("ROS job must upload failure artifacts")
    required_tokens = (
        "run_ros_gazebo_container.sh",
        "--scenario nominal",
    )
    if not all(token in run_text for token in required_tokens):
        errors.append("ROS job must use the repository container reproduction")
    environment = string_mapping(job, "env")
    if environment.get("TUTORIAL_CI_CCACHE") != "/tmp/tutorial-bot-ccache":
        errors.append("ROS job must expose only the safe compiler cache")
    forbidden = ("nvidia", "rviz", "fuel", "nav2", "secrets.", "--gpus")
    if any(token in run_text.lower() for token in forbidden):
        errors.append("ROS job contains a forbidden runtime dependency")
    return errors


def validate_helpers(root: Path) -> list[str]:
    runner = (root / "scripts/ci/run_ros_gazebo_ci.sh").read_text(encoding="utf-8")
    container = (root / "scripts/ci/run_ros_gazebo_container.sh").read_text(
        encoding="utf-8"
    )
    image = (root / "scripts/ci/Dockerfile.ubuntu24.04").read_text(encoding="utf-8")
    required_runner = (
        "rosdep update",
        "rosdep install",
        "resolved-versions.txt",
        "gz sim --versions",
        "gcc --version",
        "colcon --log-base /work/log build",
        "colcon --log-base /work/test-log test",
        "colcon test-result",
        "check_advanced_course.sh",
        "LIBGL_ALWAYS_SOFTWARE=1",
    )
    errors: list[str] = []
    if not all(token in runner for token in required_runner):
        errors.append("container runner is missing a required CI stage")
    deterministic_test_tokens = (
        "export CTEST_PARALLEL_LEVEL=1",
        "--executor sequential",
        SELECTED_TEST_PATTERN,
    )
    if not all(token in runner for token in deterministic_test_tokens):
        errors.append("container runner must pin deterministic selected tests")
    repositories = ("FROM ubuntu:24.04", "packages.ros.org", "packages.osrfoundation.org")
    if not all(token in image for token in repositories):
        errors.append("container image must use supported Ubuntu, ROS, and Gazebo repositories")
    forbidden = ("nvidia", "rviz", "fuel", "nav2", "--gpus", "secrets.")
    if any(token in f"{runner}\n{container}\n{image}".lower() for token in forbidden):
        errors.append("container reproduction contains a forbidden dependency")
    return errors


def main() -> int:
    args = parser().parse_args()
    try:
        workflow = yaml.load(args.workflow.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        jobs = workflow["jobs"]
        permissions = workflow["permissions"]
    except (FileNotFoundError, KeyError, TypeError, yaml.YAMLError) as error:
        print(f"invalid workflow: {error}", file=sys.stderr)
        return 2
    errors = validate_pages(jobs)
    if permissions != {"contents": "read", "pages": "write", "id-token": "write"}:
        errors.append("top-level Pages permissions changed")
    ros_job = jobs.get("ros-gazebo")
    if ros_job is None:
        errors.append("missing ros-gazebo job")
    else:
        errors.extend(validate_ros(ros_job, args.expect_runner, args.expect_timeout))
    try:
        errors.extend(validate_helpers(args.workflow.parents[2]))
    except FileNotFoundError as error:
        errors.append(f"missing container helper: {error.filename}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("workflow contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
