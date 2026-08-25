#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.course_evidence_manifest import AuditInputError
    from scripts.course_evidence_records import load_json
elif __package__:
    from .course_evidence_manifest import AuditInputError
    from .course_evidence_records import load_json
else:
    from course_evidence_manifest import AuditInputError
    from course_evidence_records import load_json


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--evidence-root", required=True, type=Path)
    result.add_argument("--require-sentinels-reaped", action="store_true")
    return result


def receipt_errors(path: Path, require_sentinels_reaped: bool) -> list[str]:
    try:
        receipt = load_json(path)
    except AuditInputError as error:
        return [f"{path}: malformed cleanup receipt: {error}"]
    survivors = receipt.get("survivors")
    if isinstance(survivors, list):
        if any(type(pid) is not int for pid in survivors):
            return [f"{path}: malformed cleanup receipt: survivors must be integers"]
        if survivors:
            return [
                f"{path}: owned survivors: {','.join(str(pid) for pid in survivors)}"
            ]
    elif type(survivors) is int:
        if survivors != 0:
            return [f"{path}: owned survivors: {survivors}"]
    else:
        return [f"{path}: malformed cleanup receipt: survivors must be a list or zero"]
    sentinel_survived = receipt.get("sentinel_survived_dut_teardown")
    sentinel_reaped = receipt.get("sentinel_reaped")
    if sentinel_survived is not None or sentinel_reaped is not None:
        if type(sentinel_survived) is not bool or type(sentinel_reaped) is not bool:
            return [
                f"{path}: malformed cleanup receipt: sentinel fields must be booleans"
            ]
        if require_sentinels_reaped and sentinel_survived and not sentinel_reaped:
            return [f"{path}: registered sentinel was not reaped"]
    return []


def main() -> int:
    arguments = parser().parse_args()
    evidence_root = arguments.evidence_root.resolve()
    receipts = (
        sorted(evidence_root.rglob("*cleanup.json")) if evidence_root.is_dir() else []
    )
    errors = (
        [f"{evidence_root}: no cleanup receipts found"]
        if not receipts
        else [
            error
            for receipt in receipts
            for error in receipt_errors(receipt, arguments.require_sentinels_reaped)
        ]
    )
    report = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "evidence_root": str(evidence_root),
        "receipts": len(receipts),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
