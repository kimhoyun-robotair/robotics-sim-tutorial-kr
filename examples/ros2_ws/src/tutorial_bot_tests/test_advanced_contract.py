from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml


WORKSPACE_ROOT = Path(__file__).parents[4]
CONTRACT = (
    WORKSPACE_ROOT
    / "examples/ros2_ws/src/tutorial_bot_plugins/config/diagnostics-contract.yaml"
)
CHECKER = WORKSPACE_ROOT / "scripts/check_advanced_contract.py"


def test_contract_freezes_diagnostics_surface() -> None:
    # Given: the canonical advanced diagnostics contract.
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    # When: its machine-consumed surface is inspected.
    surface = contract["diagnostics"]

    # Then: every plugin identity, endpoint, default, state, and lifecycle rule is fixed.
    assert surface == {
        "plugin": {
            "class": "gz::sim::systems::TutorialBotDiagnostics",
            "library": "libTutorialBotDiagnosticsSystem.so",
            "scope": "world",
            "interfaces": ["ISystemConfigure", "ISystemPostUpdate"],
            "ecs_read_set": ["named_model", "world_pose"],
            "ros_dependencies": False,
            "duplicates_diff_drive": False,
        },
        "parameters": {
            "model_name": {"default": "tutorial_bot"},
            "distance_topic": {
                "default": "/tutorial_bot/diagnostics/distance",
                "message_type": "gz.msgs.Double",
                "direction": "publish",
            },
            "status_topic": {
                "default": "/tutorial_bot/diagnostics/status",
                "message_type": "gz.msgs.StringMsg",
                "direction": "publish",
            },
            "enable_topic": {
                "default": "/tutorial_bot/diagnostics/enable",
                "message_type": "gz.msgs.Boolean",
                "direction": "subscribe",
            },
            "reset_service": {
                "default": "/tutorial_bot/diagnostics/reset",
                "request_type": "gz.msgs.Empty",
                "response_type": "gz.msgs.Boolean",
                "direction": "request_reply",
            },
            "publish_period": {
                "default": 0.1,
                "unit": "seconds",
                "constraint": "finite_positive",
            },
            "enabled": {"default": True},
        },
        "states": [
            "WAITING_FOR_MODEL",
            "READY",
            "DISABLED",
            "MODEL_REMOVED",
            "INVALID_CONFIG",
        ],
        "lifecycle": {
            "first_valid_sample": "baseline_distance_zero_status_READY",
            "missing_model": "WAITING_FOR_MODEL_then_bind_by_name",
            "model_removed": "freeze_distance_emit_MODEL_REMOVED_rebind_fresh_baseline",
            "reset_bound": "reply_true_zero_distance_and_baseline_including_DISABLED",
            "reset_unbound": "reply_false_state_unchanged",
            "invalid_publish_period": (
                "INVALID_CONFIG_no_distance_publisher_harness_exit_64"
            ),
        },
        "future_behavior_tests": [
            "diagnostics_configure",
            "diagnostics_missing_model",
            "diagnostics_distance",
            "diagnostics_enable_disable",
            "diagnostics_reset",
        ],
    }


def test_checker_rejects_wrong_reset_response_type(tmp_path: Path) -> None:
    # Given: a fixture whose reset reply type violates the frozen contract.
    evidence = tmp_path / "fault.json"
    fixture = WORKSPACE_ROOT / "scripts/fixtures/advanced/wrong-reset-type.yaml"

    # When: the contract checker parses the fixture.
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--contract", str(fixture), "--evidence", str(evidence)],
        capture_output=True,
        check=False,
        text=True,
    )

    # Then: it reports a usage/contract failure and names the expected Boolean reply.
    assert result.returncode == 64
    assert "gz.msgs.Boolean" in result.stderr
    assert evidence.is_file()


@pytest.mark.parametrize(
    "relative_path",
    [
        "share/tutorial_bot_plugins/config/diagnostics-contract.yaml",
        "share/tutorial_bot_plugins/schema/diagnostics-contract.schema.json",
        "include/tutorial_bot_plugins/diagnostics_contract.hpp",
    ],
)
def test_plugin_install_layout_is_declared(relative_path: str) -> None:
    # Given: the plugin package build declaration.
    cmake = (
        WORKSPACE_ROOT / "examples/ros2_ws/src/tutorial_bot_plugins/CMakeLists.txt"
    ).read_text(encoding="utf-8")

    # When: install destinations are inspected.
    normalized = " ".join(cmake.split())

    # Then: the canonical contract, schema, and public header are installed.
    assert relative_path.split("/", maxsplit=3)[-1] in normalized
