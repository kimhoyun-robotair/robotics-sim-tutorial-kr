#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


OWNED_CHECKERS = (
    "check_diff_drive.sh",
    "check_sensors.sh",
    "check_fuel_world.sh",
    "check_ros_gz_bridge.sh",
    "check_intermediate_launch.sh",
    "check_intermediate_sensors.sh",
    "check_intermediate_control_tf.sh",
    "check_intermediate_multi_robot.sh",
    "check_intermediate_nav2.sh",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="scripts")
    parser.add_argument("--forbid", default="pkill,killall")
    parser.add_argument("--require-owned-process-api", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.path)
    forbidden = [token.strip() for token in args.forbid.split(",") if token.strip()]
    errors: list[str] = []
    for path in sorted(root.rglob("*.sh")):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if re.search(rf"(?:^|[;&|\s]){re.escape(token)}(?=\s|$)", text, re.MULTILINE):
                errors.append(f"{path}: forbidden command {token}")
    if args.require_owned_process_api:
        if not (root / "run_owned_process.py").is_file() or not (root / "lib/owned_process.sh").is_file():
            errors.append("shared owned-process APIs are missing")
        for name in OWNED_CHECKERS:
            text = (root / name).read_text(encoding="utf-8")
            if "lib/owned_process.sh" not in text or "owned_validate_isolation" not in text:
                errors.append(f"{name}: checker is not migrated to owned process isolation")
    report = {"schema_version": 1, "status": "pass" if not errors else "fail", "errors": errors}
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
