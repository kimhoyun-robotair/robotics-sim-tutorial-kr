from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.course_evidence_manifest import AuditInputError
elif __package__:
    from .course_evidence_manifest import AuditInputError
else:
    from course_evidence_manifest import AuditInputError


def load_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuditInputError(f"{path}: {error}") from error
    if not isinstance(value, dict):
        raise AuditInputError(f"{path}: expected mapping")
    return value


def load_index(path: Path) -> dict[str, object]:
    value = load_json(path)
    if value.get("schema_version") != 1:
        raise AuditInputError("invalid evidence index schema")
    task_entries(value)
    return value


def task_entries(index: Mapping[str, object]) -> list[dict[str, object]]:
    raw = index.get("tasks")
    if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
        raise AuditInputError("index tasks must be a list of mappings")
    return raw


def fixture_errors(
    index: Mapping[str, object], root: Path, expected_sha: str
) -> list[str]:
    errors: list[str] = []
    if index.get("source_sha") is not None and index.get("source_sha") != expected_sha:
        errors.append("stale_sha")
    referenced = index.get("artifacts", [])
    if not isinstance(referenced, list):
        raise AuditInputError("artifacts must be a list")
    referenced_paths = {(root / str(path)).resolve() for path in referenced}
    if any(path.resolve() not in referenced_paths for path in root.rglob("*.png")):
        errors.append("orphan_image")
    scenarios = index.get("process_scenarios", [])
    if not isinstance(scenarios, list):
        raise AuditInputError("process_scenarios must be a list")
    for raw in scenarios:
        if not isinstance(raw, dict):
            raise AuditInputError("process scenario must be a mapping")
        cleanup = root / str(raw.get("cleanup", ""))
        result = root / str(raw.get("result", ""))
        if not cleanup.is_file():
            errors.append("missing_cleanup")
            continue
        outcome = load_json(result)
        if outcome.get("status") == "pass" and (
            outcome.get("exit") != 0 or outcome.get("observable_passed") is not True
        ):
            errors.append("misleading_success")
    events = index.get("tdd_events", [])
    if not isinstance(events, list) or any(
        not isinstance(item, dict) for item in events
    ):
        raise AuditInputError("tdd_events must be a list of mappings")
    red_sequences = [
        item.get("sequence") for item in events if item.get("phase") == "red"
    ]
    production_sequences = [
        item.get("sequence") for item in events if item.get("phase") == "production"
    ]
    if red_sequences and production_sequences:
        if any(
            not isinstance(item, int)
            for item in [*red_sequences, *production_sequences]
        ):
            raise AuditInputError("tdd event sequences must be integers")
        if min(production_sequences) < min(red_sequences):
            errors.append("invalid_tdd_order")
    return errors
