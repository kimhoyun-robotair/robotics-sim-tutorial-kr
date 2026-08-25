#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Final


SHA_LENGTH: Final = 40
SNAPSHOT_FILES: Final = ("plan.md", "ledger.jsonl", "index.json")


def full_sha(raw: str) -> str:
    if len(raw) != SHA_LENGTH or any(character not in "0123456789abcdef" for character in raw):
        raise argparse.ArgumentTypeError("expected a full lowercase SHA")
    return raw


def atomic_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def finalized_index(index_path: Path, final_sha: str, source_tree: str, task: int) -> bytes:
    raw = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("invalid evidence index schema")
    tasks = raw.get("tasks")
    if not isinstance(tasks, list) or any(not isinstance(item, dict) for item in tasks):
        raise ValueError("index tasks must be a list of mappings")
    matching = [item for item in tasks if item.get("task") == task]
    if len(matching) != 1:
        raise ValueError(f"index must contain exactly one task {task} binding")
    matching[0]["commit"] = final_sha
    raw["source_sha"] = final_sha
    raw["source_tree"] = source_tree
    raw["final_sha"] = final_sha
    return (json.dumps(raw, indent=2, sort_keys=True) + "\n").encode()


def create_snapshot(
    plan: Path,
    ledger: Path,
    index: Path,
    output: Path,
    final_sha: str,
    source_tree: str,
) -> None:
    if output.exists():
        raise FileExistsError(f"immutable snapshot already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    index_content = finalized_index(index, final_sha, source_tree, 15)
    atomic_write(index, index_content)
    temporary = Path(tempfile.mkdtemp(prefix=".final-input-", dir=output.parent))
    try:
        (temporary / "plan.md").write_bytes(plan.read_bytes())
        (temporary / "ledger.jsonl").write_bytes(ledger.read_bytes())
        (temporary / "index.json").write_bytes(index_content)
        artifacts = {
            name: hashlib.sha256((temporary / name).read_bytes()).hexdigest()
            for name in SNAPSHOT_FILES
        }
        hashes = {
            "schema_version": 1,
            "final_sha": final_sha,
            "source_tree": source_tree,
            "artifacts": artifacts,
        }
        (temporary / "hashes.json").write_text(
            json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        for path in temporary.iterdir():
            path.chmod(0o444)
        temporary.chmod(0o555)
        os.replace(temporary, output)
    except (FileNotFoundError, FileExistsError, OSError, TypeError, ValueError, json.JSONDecodeError):
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--plan", required=True, type=Path)
    result.add_argument("--ledger", required=True, type=Path)
    result.add_argument("--index", required=True, type=Path)
    result.add_argument("--output-dir", required=True, type=Path)
    result.add_argument("--final-sha", required=True, type=full_sha)
    result.add_argument("--source-tree", required=True, type=full_sha)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        create_snapshot(
            args.plan,
            args.ledger,
            args.index,
            args.output_dir,
            args.final_sha,
            args.source_tree,
        )
    except (FileNotFoundError, FileExistsError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        parser().error(str(error))
    print(json.dumps({"status": "pass", "final_sha": args.final_sha, "output_dir": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
