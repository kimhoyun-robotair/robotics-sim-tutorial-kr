#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.course_evidence_cli import parser
    from scripts.course_evidence_manifest import (
        AuditInputError,
        installed_artifact_errors,
        manifest_errors,
        parse_task_range,
    )
    from scripts.course_evidence_records import (
        fixture_errors,
        load_index,
        load_json,
        task_entries,
    )
elif __package__:
    from .course_evidence_cli import parser
    from .course_evidence_manifest import (
        AuditInputError,
        installed_artifact_errors,
        manifest_errors,
        parse_task_range,
    )
    from .course_evidence_records import (
        fixture_errors,
        load_index,
        load_json,
        task_entries,
    )
else:
    from course_evidence_cli import parser
    from course_evidence_manifest import (
        AuditInputError,
        installed_artifact_errors,
        manifest_errors,
        parse_task_range,
    )
    from course_evidence_records import (
        fixture_errors,
        load_index,
        load_json,
        task_entries,
    )

__all__ = ["installed_artifact_errors"]


def write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def bind(
    index_path: Path, index: dict[str, object], task: int, commit: str, attempt: str
) -> dict[str, object]:
    if len(commit) != 40 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise AuditInputError("commit must be a full lowercase SHA")
    attempt_path = Path(attempt).resolve()
    digest = hashlib.sha256(attempt_path.as_posix().encode()).hexdigest()
    entries = [entry for entry in task_entries(index) if entry.get("task") != task]
    entries.append(
        {
            "task": task,
            "commit": commit,
            "attempt_dir": str(attempt_path),
            "binding_digest": digest,
        }
    )

    def task_number(entry: Mapping[str, object]) -> int:
        value = entry.get("task")
        if not isinstance(value, int):
            raise AuditInputError("task number must be an integer")
        return value

    index["tasks"] = sorted(entries, key=task_number)
    write(index_path, index)
    return {
        "status": "pass",
        "class": "bound",
        "task": task,
        "commit": commit,
        "binding_digest": digest,
    }


def evidence_errors(
    index: Mapping[str, object], root: Path, required: set[int]
) -> list[str]:
    entries = task_entries(index)
    numbers = [entry.get("task") for entry in entries]
    errors = []
    if len(numbers) != len(set(numbers)) or set(numbers) != required:
        errors.append("missing_task")
    for entry in entries:
        attempt_raw = entry.get("attempt_dir")
        digest = entry.get("binding_digest")
        if not isinstance(attempt_raw, str):
            errors.append("invalid_binding")
            continue
        attempt = Path(attempt_raw).resolve()
        expected = hashlib.sha256(attempt.as_posix().encode()).hexdigest()
        if digest is not None and digest != expected:
            errors.append("stale_evidence_hash")
        claim = attempt / "DoneClaim.json"
        if not claim.is_file() or claim.stat().st_size == 0:
            errors.append("missing_done_claim")
    matrix = root / "task-15/task-15-matrix/matrix.json"
    if 15 in required:
        if not matrix.is_file():
            errors.append("missing_matrix")
        else:
            report = load_json(matrix)
            dispatches = report.get("dispatches")
            if (
                report.get("status") != "pass"
                or not isinstance(dispatches, list)
                or len(dispatches) != 26
                or any(not valid_dispatch(item) for item in dispatches)
            ):
                errors.append("misleading_success")
    return errors


def valid_dispatch(raw: object) -> bool:
    if not isinstance(raw, dict):
        return False
    cleanup = raw.get("cleanup")
    if (
        raw.get("executed") is not True
        or raw.get("observable_passed") is not True
        or not isinstance(cleanup, str)
    ):
        return False
    path = Path(cleanup)
    if not path.is_file():
        return False
    receipt = load_json(path)
    return receipt.get("survivors") == []


def audit(
    index: Mapping[str, object], args: argparse.Namespace
) -> tuple[dict[str, object], int]:
    root = Path(args.evidence_root or Path(args.evidence_index).parent).resolve()
    if args.fixture:
        fixture_root = Path(args.fixture).resolve()
        errors = fixture_errors(
            load_index(fixture_root / "index.json"),
            fixture_root,
            args.source_sha
            or subprocess.check_output(("git", "rev-parse", "HEAD"), text=True).strip(),
        )
        counts: dict[str, int] = {}
    else:
        if args.require_tasks or args.manifest:
            required = parse_task_range(args.require_tasks or "1-15")
        else:
            required = set()
            for entry in task_entries(index):
                value = entry.get("task")
                if not isinstance(value, int):
                    raise AuditInputError("task number must be an integer")
                required.add(value)
        errors = evidence_errors(index, root, required)
        counts = {}
        if args.source_sha and index.get("source_sha") != args.source_sha:
            errors.insert(0, "stale_sha")
        if args.source_tree_digest:
            actual_tree = subprocess.check_output(
                ("git", "write-tree"), text=True
            ).strip()
            if args.source_tree_digest != actual_tree:
                errors.append("stale_tree")
        if args.manifest:
            manifest_failures, counts = manifest_errors(Path(args.manifest), root)
            errors.extend(manifest_failures)
    report = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "class": errors[0] if errors else "valid",
        "errors": errors,
        "source_sha": index.get("source_sha"),
        "task_count": len(task_entries(index)),
        "course_counts": counts,
    }
    return report, 0 if not errors else 1


def main() -> int:
    args = parser().parse_args()
    try:
        index_path = Path(args.evidence_index)
        index = load_index(index_path)
        if args.print_task_baseline_sha is not None:
            print(index.get("baseline_sha", ""))
            return 0
        if args.bind_task_commit is not None:
            if args.commit is None or args.attempt_dir is None:
                raise AuditInputError("binding requires --commit and --attempt-dir")
            report = bind(
                index_path, index, args.bind_task_commit, args.commit, args.attempt_dir
            )
            exit_code = 0
        else:
            report, exit_code = audit(index, args)
    except (AuditInputError, KeyError, TypeError, ValueError) as error:
        report = {
            "schema_version": 1,
            "status": "fail",
            "class": "invalid_input",
            "errors": [str(error)],
        }
        exit_code = 64
    if args.output:
        write(Path(args.output), report)
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
