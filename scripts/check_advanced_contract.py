#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Final

import yaml


EXIT_CONTRACT: Final = 64
type YAMLValue = str | int | float | bool | list[str] | Mapping[str, "YAMLValue"] | None
type EvidenceValue = str | list[str]
EXPECTED: Final[tuple[tuple[tuple[str, ...], str | float | bool | list[str]], ...]] = (
    (("diagnostics", "plugin", "class"), "gz::sim::systems::TutorialBotDiagnostics"),
    (("diagnostics", "plugin", "library"), "libTutorialBotDiagnosticsSystem.so"),
    (("diagnostics", "plugin", "scope"), "world"),
    (("diagnostics", "plugin", "interfaces"), ["ISystemConfigure", "ISystemPostUpdate"]),
    (("diagnostics", "plugin", "ecs_read_set"), ["named_model", "world_pose"]),
    (("diagnostics", "plugin", "ros_dependencies"), False),
    (("diagnostics", "plugin", "duplicates_diff_drive"), False),
    (("diagnostics", "parameters", "model_name", "default"), "tutorial_bot"),
    (("diagnostics", "parameters", "distance_topic", "default"), "/tutorial_bot/diagnostics/distance"),
    (("diagnostics", "parameters", "distance_topic", "message_type"), "gz.msgs.Double"),
    (("diagnostics", "parameters", "distance_topic", "direction"), "publish"),
    (("diagnostics", "parameters", "status_topic", "default"), "/tutorial_bot/diagnostics/status"),
    (("diagnostics", "parameters", "status_topic", "message_type"), "gz.msgs.StringMsg"),
    (("diagnostics", "parameters", "status_topic", "direction"), "publish"),
    (("diagnostics", "parameters", "enable_topic", "default"), "/tutorial_bot/diagnostics/enable"),
    (("diagnostics", "parameters", "enable_topic", "message_type"), "gz.msgs.Boolean"),
    (("diagnostics", "parameters", "enable_topic", "direction"), "subscribe"),
    (("diagnostics", "parameters", "reset_service", "default"), "/tutorial_bot/diagnostics/reset"),
    (("diagnostics", "parameters", "reset_service", "request_type"), "gz.msgs.Empty"),
    (("diagnostics", "parameters", "reset_service", "response_type"), "gz.msgs.Boolean"),
    (("diagnostics", "parameters", "reset_service", "direction"), "request_reply"),
    (("diagnostics", "parameters", "publish_period", "default"), 0.1),
    (("diagnostics", "parameters", "publish_period", "unit"), "seconds"),
    (("diagnostics", "parameters", "publish_period", "constraint"), "finite_positive"),
    (("diagnostics", "parameters", "enabled", "default"), True),
    (("diagnostics", "states"), ["WAITING_FOR_MODEL", "READY", "DISABLED", "MODEL_REMOVED", "INVALID_CONFIG"]),
    (("diagnostics", "lifecycle", "first_valid_sample"), "baseline_distance_zero_status_READY"),
    (("diagnostics", "lifecycle", "missing_model"), "WAITING_FOR_MODEL_then_bind_by_name"),
    (("diagnostics", "lifecycle", "model_removed"), "freeze_distance_emit_MODEL_REMOVED_rebind_fresh_baseline"),
    (("diagnostics", "lifecycle", "reset_bound"), "reply_true_zero_distance_and_baseline_including_DISABLED"),
    (("diagnostics", "lifecycle", "reset_unbound"), "reply_false_state_unchanged"),
    (("diagnostics", "lifecycle", "invalid_publish_period"), "INVALID_CONFIG_no_distance_publisher_harness_exit_64"),
    (("diagnostics", "future_behavior_tests"), ["diagnostics_configure", "diagnostics_missing_model", "diagnostics_distance", "diagnostics_enable_disable", "diagnostics_reset"]),
)


def _lookup(document: Mapping[str, YAMLValue], path: tuple[str, ...]) -> YAMLValue:
    value: YAMLValue = document
    for part in path:
        if not isinstance(value, Mapping) or part not in value:
            return None
        value = value[part]
    return value


def _write_evidence(path: Path, payload: Mapping[str, EvidenceValue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        temporary = Path(stream.name)
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        loaded: Mapping[str, YAMLValue] = yaml.safe_load(
            arguments.contract.read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError) as error:
        message = f"contract parse error: {error}"
        _write_evidence(arguments.evidence, {"status": "fail", "errors": [message]})
        print(message, file=sys.stderr)
        return EXIT_CONTRACT

    errors = [
        f"{'.'.join(path)}: expected {expected!r}, got {_lookup(loaded, path)!r}"
        for path, expected in EXPECTED
        if _lookup(loaded, path) != expected
    ]

    if errors:
        _write_evidence(arguments.evidence, {"status": "fail", "errors": errors})
        print("\n".join(errors), file=sys.stderr)
        return EXIT_CONTRACT

    surface: Sequence[str] = (
        "plugin.class=gz::sim::systems::TutorialBotDiagnostics",
        "plugin.library=libTutorialBotDiagnosticsSystem.so",
        "plugin.interfaces=ISystemConfigure,ISystemPostUpdate",
        "model_name=tutorial_bot",
        "distance_topic=/tutorial_bot/diagnostics/distance type=gz.msgs.Double direction=publish",
        "status_topic=/tutorial_bot/diagnostics/status type=gz.msgs.StringMsg direction=publish",
        "enable_topic=/tutorial_bot/diagnostics/enable type=gz.msgs.Boolean direction=subscribe",
        "reset_service=/tutorial_bot/diagnostics/reset request=gz.msgs.Empty response=gz.msgs.Boolean",
        "publish_period=0.1 seconds constraint=finite_positive",
        "enabled=true",
        "states=WAITING_FOR_MODEL,READY,DISABLED,MODEL_REMOVED,INVALID_CONFIG",
    )
    output = "\n".join(surface)
    print(output)
    _write_evidence(arguments.evidence, {"status": "pass", "surface": list(surface)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
