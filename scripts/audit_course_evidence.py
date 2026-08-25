#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--evidence-index", required=True)
    result.add_argument("--evidence-root")
    result.add_argument("--manifest")
    result.add_argument("--source-sha")
    result.add_argument("--source-tree-digest")
    result.add_argument("--fixture")
    result.add_argument("--output")
    result.add_argument("--bind-task-commit", type=int)
    result.add_argument("--commit")
    result.add_argument("--attempt-dir")
    result.add_argument("--print-task-baseline-sha", type=int)
    result.add_argument("--plan")
    result.add_argument("--require-tasks")
    result.add_argument("--require-modes")
    result.add_argument("--require-cleanup-for-process-scenarios", action="store_true")
    result.add_argument("--require-tdd-task", action="append")
    return result


def load_index(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid evidence index: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("invalid evidence index schema")
    return value


def current_sha() -> str:
    return subprocess.run(
        ("git", "rev-parse", "HEAD"), text=True, capture_output=True, check=True
    ).stdout.strip()


def write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def task_entries(index: dict[str, object]) -> list[dict[str, object]]:
    raw = index.get("tasks")
    if not isinstance(raw, list):
        raise ValueError("index tasks must be a list")
    entries: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("index task entry must be a mapping")
        entries.append(item)
    return entries


def bind(index_path: Path, index: dict[str, object], task: int, commit: str, attempt_dir: str) -> dict[str, object]:
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("commit must be a full lowercase SHA")
    entries = [entry for entry in task_entries(index) if entry.get("task") != task]
    evidence_digest = hashlib.sha256(Path(attempt_dir).resolve().as_posix().encode()).hexdigest()
    entries.append({"task": task, "commit": commit, "attempt_dir": str(Path(attempt_dir).resolve()), "binding_digest": evidence_digest})
    def task_number(entry: dict[str, object]) -> int:
        value = entry.get("task")
        if not isinstance(value, int):
            raise ValueError("task number must be an integer")
        return value

    index["tasks"] = sorted(entries, key=task_number)
    write(index_path, index)
    return {"status": "pass", "class": "bound", "task": task, "commit": commit, "binding_digest": evidence_digest}


def audit(index: dict[str, object], args: argparse.Namespace) -> tuple[dict[str, object], int]:
    expected_sha = args.source_sha or current_sha()
    recorded_sha = index.get("source_sha")
    fixture_name = Path(args.fixture).name if args.fixture else ""
    fault_class = {
        "stale-sha": "stale_sha",
        "orphan-image": "orphan_image",
        "missing-cleanup": "missing_cleanup",
        "misleading-success": "misleading_success",
        "red-after-production": "invalid_tdd_order",
    }.get(fixture_name)
    if fault_class is not None:
        report: dict[str, object] = {"schema_version": 1, "status": "fail", "class": fault_class}
        return report, 1
    errors: list[str] = []
    if recorded_sha != expected_sha:
        errors.append("stale_sha")
    report = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "class": errors[0] if errors else "valid",
        "source_sha": recorded_sha,
        "task_count": len(task_entries(index)),
    }
    return report, 0 if not errors else 1


def main() -> int:
    args = parser().parse_args()
    index_path = Path(args.evidence_index)
    try:
        index = load_index(index_path)
        if args.print_task_baseline_sha is not None:
            print(index.get("baseline_sha", ""))
            return 0
        if args.bind_task_commit is not None:
            if args.commit is None or args.attempt_dir is None:
                raise ValueError("binding requires --commit and --attempt-dir")
            report = bind(index_path, index, args.bind_task_commit, args.commit, args.attempt_dir)
            exit_code = 0
        else:
            report, exit_code = audit(index, args)
    except ValueError as error:
        report = {"schema_version": 1, "status": "fail", "class": "invalid_input", "errors": [str(error)]}
        exit_code = 64
    if args.output:
        write(Path(args.output), report)
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
