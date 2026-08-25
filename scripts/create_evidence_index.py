#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-sha", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    for value in (args.baseline_sha, args.source_sha):
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            parser.error("SHAs must be full lowercase hexadecimal values")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    data = {"schema_version": 1, "baseline_sha": args.baseline_sha, "source_sha": args.source_sha, "tasks": []}
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
