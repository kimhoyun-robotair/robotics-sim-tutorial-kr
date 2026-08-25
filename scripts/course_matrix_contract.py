from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

INTERMEDIATE_TIMING_BUDGET_SECONDS: Final = 270.0


@dataclass(frozen=True, slots=True)
class Scenario:
    course: str
    name: str
    command: tuple[str, ...]
    fault_arguments: tuple[str, ...] = ("--expect-failure",)
    fault_exit: int = 0
    observable_contract: str = "checker_exit_and_cleanup"
    fault_command: tuple[str, ...] | None = None


SCENARIOS: Final = (
    Scenario(
        "beginner",
        "diff-drive",
        ("./scripts/check_diff_drive.sh",),
        (),
        255,
        fault_command=(
            "./scripts/check_diff_drive.sh",
            "--xacro",
            "scripts/fixtures/xacro/missing-wheel-parent.urdf.xacro",
        ),
    ),
    Scenario(
        "beginner",
        "sensors",
        ("./scripts/check_sensors.sh",),
        (),
        1,
        fault_command=(
            "./scripts/check_sensors.sh",
            "--expectations",
            "scripts/fixtures/bridge/missing-scan.yaml",
        ),
    ),
    Scenario(
        "beginner",
        "fuel",
        ("./scripts/check_fuel_world.sh",),
        (),
        1,
        fault_command=(
            "./scripts/check_fuel_world.sh",
            "--world",
            "examples/gazebo/worlds/first-world.sdf",
        ),
    ),
    Scenario(
        "beginner",
        "bridge",
        ("./scripts/check_ros_gz_bridge.sh",),
        (),
        1,
        fault_command=(
            "./scripts/check_ros_gz_bridge.sh",
            "--config",
            "scripts/fixtures/bridge/missing-scan.yaml",
        ),
    ),
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
        (),
        20,
        fault_command=(
            "./scripts/check_advanced_course.sh",
            "--scenario",
            "missing-model",
        ),
    ),
    Scenario(
        "advanced",
        "transport",
        ("./scripts/check_advanced_course.sh", "--scenario", "transport"),
        (),
        0,
        fault_command=(
            "./scripts/check_advanced_course.sh",
            "--scenario",
            "transport-wrong-types",
        ),
    ),
    Scenario(
        "advanced",
        "physics",
        (
            "./scripts/check_advanced_course.sh",
            "--scenario",
            "physics",
            "--sim-seconds",
            "2.0",
            "--worlds",
            "advanced-fast.sdf,advanced-slow.sdf",
        ),
        (),
        64,
        fault_command=(
            "./scripts/check_advanced_course.sh",
            "--scenario",
            "invalid-period",
            "--publish-period",
            "0",
        ),
    ),
    Scenario(
        "advanced",
        "headless",
        (
            "./scripts/check_advanced_headless.sh",
            "--scenario",
            "nominal",
            "--install-base",
            "__INSTALL_BASE__",
        ),
        (),
        21,
        fault_command=(
            "./scripts/check_advanced_headless.sh",
            "--scenario",
            "plugin-missing",
            "--install-base",
            "__INSTALL_BASE__",
        ),
    ),
)


def comma_set(raw: str) -> set[str]:
    return {value.strip() for value in raw.split(",") if value.strip()}


def scenario_command(scenario: Scenario, mode: str, evidence: Path) -> list[str]:
    selected = (
        scenario.fault_command
        if mode == "fault" and scenario.fault_command
        else scenario.command
    )
    command = [*selected, "--evidence", str(evidence)]
    return [*command, *(scenario.fault_arguments if mode == "fault" else ())]


def expected_exit(scenario: Scenario, mode: str) -> int:
    return scenario.fault_exit if mode == "fault" else 0


def timing_budget(
    courses: set[str], names: set[str], modes: set[str], execute: bool
) -> float | None:
    required_names = {
        scenario.name for scenario in SCENARIOS if scenario.course == "intermediate"
    }
    if (
        execute
        and courses == {"intermediate"}
        and names == required_names
        and modes == {"nominal", "fault"}
    ):
        return INTERMEDIATE_TIMING_BUDGET_SECONDS
    return None
