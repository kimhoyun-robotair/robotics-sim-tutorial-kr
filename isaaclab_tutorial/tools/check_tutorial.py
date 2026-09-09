#!/usr/bin/env python3
"""Check syntax and local/pinned source links without importing Isaac Lab."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, help="Exact v3.0.0-beta2.patch1 checkout for source-link checks")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    counts = {"python_files": 0, "shell_files": 0, "markdown_files": 0, "local_links": 0, "pinned_source_links": 0}
    for path in sorted(root.rglob("*.py")):
        if "outputs" in path.parts:
            continue
        counts["python_files"] += 1
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(str(exc))
    for path in sorted(root.rglob("*.sh")):
        counts["shell_files"] += 1
        p = subprocess.run(["bash", "-n", str(path)], text=True, capture_output=True, check=False)
        if p.returncode:
            errors.append(p.stderr)
    documents = list(root.rglob("*.md"))
    if root.name == "isaaclab_tutorial":
        documents.append(root.parent / "README.md")
    steps = []
    for path in sorted(documents):
        counts["markdown_files"] += 1
        body = path.read_text(encoding="utf-8")
        if path.parent.name == "docs" and path.name.startswith(("01-", "02-", "03-")):
            steps.extend(re.findall(r'<a id="step-(\d+)"', body))
        for target in re.findall(r'\]\(([^\s)]+)\)', body):
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.exists():
                errors.append(f"Broken local link: {path.name}: {target}")
            elif parsed.fragment.startswith("step-"):
                anchor = f'id="{parsed.fragment}"'
                if anchor not in resolved.read_text(encoding="utf-8"):
                    errors.append(f"Missing step anchor: {target}")
            counts["local_links"] += 1
        if args.upstream:
            for source in re.findall(r'https://github.com/isaac-sim/IsaacLab/(?:blob|tree)/v3\.0\.0-beta2\.patch1/([^\s)#>]+)', body):
                counts["pinned_source_links"] += 1
                if not (args.upstream / unquote(source)).exists():
                    errors.append(f"Missing pinned source: {source}")
    if sorted(steps) != [f"{x:02d}" for x in range(1, 37)]:
        errors.append(f"Expected exactly steps 01–36; found {steps}")
    if args.upstream:
        p = subprocess.run(["git", "-C", str(args.upstream), "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
        if p.stdout.strip() != "ffff603eafc6b74264a5261cc0183d6a65390d78":
            errors.append("Upstream checkout does not match the pinned commit")
    result = {"status": "passed" if not errors else "failed", "counts": counts, "errors": errors,
              "runtime_simulation_tested": False, "note": "Syntax and source-link checks only; no simulator imports or GPU runs."}
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    print(encoded, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
