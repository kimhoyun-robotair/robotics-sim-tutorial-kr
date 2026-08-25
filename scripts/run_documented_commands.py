#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml


COMMAND_BLOCK = re.compile(r"<!--\s*course-command\s*-->\s*```(?:bash|sh|zsh)\n(.*?)```", re.DOTALL)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="docs/course-manifest.yaml")
    parser.add_argument("--course", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--fresh-build", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    manifest = yaml.safe_load(Path(args.manifest).read_text(encoding="utf-8"))
    courses = {item.strip() for item in args.course.split(",")}
    commands: list[dict[str, object]] = []
    exit_code = 0
    for route in manifest["routes"]:
        if route["course"] not in courses:
            continue
        document = Path("docs") / route["path"]
        for block in COMMAND_BLOCK.findall(document.read_text(encoding="utf-8")):
            command = "\n".join(line for line in block.splitlines() if line.strip())
            result: int | None = None
            if not args.dry_run:
                result = subprocess.run(("bash", "-euo", "pipefail", "-c", command), check=False).returncode
                if result != 0:
                    exit_code = 1
            commands.append({"route": route["path"], "command": command, "exit": result})
    output = Path(args.evidence)
    output.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "status": "pass" if exit_code == 0 else "fail", "commands": commands}
    (output / "documented-commands.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
