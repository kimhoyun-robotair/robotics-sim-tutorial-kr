#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command-class", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--cleanup", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    log = Path(args.log)
    cleanup = Path(args.cleanup)
    if not log.is_file() or not cleanup.is_file():
        parser.error("log and cleanup receipt must exist")
    cleanup_data = json.loads(cleanup.read_text(encoding="utf-8"))
    if cleanup_data.get("survivors") != []:
        parser.error("cleanup receipt reports survivors")
    metadata = {
        "schema_version": 1,
        "command_class": args.command_class,
        "log": str(log.resolve()),
        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest(),
        "cleanup": str(cleanup.resolve()),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
