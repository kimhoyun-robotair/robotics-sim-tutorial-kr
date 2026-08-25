#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

ROOT: Final = Path(__file__).resolve().parents[1]
RENDERER: Final = "scripts/render_fixture_visual.py"


@dataclass(frozen=True, slots=True)
class VisualAsset:
    asset_id: str
    path: str
    source_command: str


class ManifestError(ValueError):
    pass


def required_text(item: dict[str, object], field: str, index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str):
        raise ManifestError(f"asset {index}: {field} must be text")
    return value


def load_visual_assets(path: Path) -> list[VisualAsset]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ManifestError(f"{path}: {error}") from error
    if not isinstance(loaded, dict) or loaded.get("schema_version") != 1:
        raise ManifestError(f"{path}: schema_version must be 1")
    raw_assets = loaded.get("assets")
    if not isinstance(raw_assets, list):
        raise ManifestError(f"{path}: assets must be a list")
    assets: list[VisualAsset] = []
    for index, item in enumerate(raw_assets):
        if not isinstance(item, dict):
            raise ManifestError(f"asset {index}: expected mapping")
        assets.append(
            VisualAsset(
                asset_id=required_text(item, "id", index),
                path=required_text(item, "path", index),
                source_command=required_text(item, "source_command", index),
            )
        )
    return assets


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--manifest", required=True)
    result.add_argument("--fragments")
    result.add_argument("--only")
    result.add_argument("--evidence", required=True)
    return result


def manifest_path(raw: str) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else ROOT / candidate


def approved_command(asset: VisualAsset) -> list[str]:
    try:
        parts = shlex.split(asset.source_command)
    except ValueError as error:
        raise ManifestError(f"{asset.asset_id}: invalid source_command: {error}") from error
    expected = ["python3", RENDERER, "--output", f"docs/{asset.path}"]
    rendered = [*expected, "--scene", asset.asset_id]
    forced = [*expected, "--force-failure"]
    cleanup_failure = [*expected, "--cleanup-failure"]
    if parts not in (expected, rendered, forced, cleanup_failure):
        raise ManifestError(f"{asset.asset_id}: source_command is not approved")
    return [sys.executable, str(ROOT / RENDERER), *parts[2:]]


def write_summary(path: Path, status: str, survivors: list[int], errors: list[str]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "status": status, "survivors": survivors, "errors": errors}
    (path / "cleanup.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_invalid_cleanup(path: Path, error: ManifestError) -> None:
    path.mkdir(parents=True, exist_ok=True)
    receipt = path / "cleanup.json"
    _ = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_owned_process.py"),
            "--timeout",
            "30",
            "--cleanup-receipt",
            str(receipt),
            "--",
            sys.executable,
            str(ROOT / "scripts" / "fixtures" / "processes" / "success.py"),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(receipt.read_text(encoding="utf-8"))
    report.update({"status": "invalid", "errors": [str(error)]})
    receipt.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def capture(asset: VisualAsset, evidence: Path) -> tuple[int, list[int]]:
    command = approved_command(asset)
    asset_evidence = evidence / asset.asset_id
    receipt = asset_evidence / "cleanup.json"
    asset_evidence.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_owned_process.py"),
            "--timeout",
            "60",
            "--cleanup-receipt",
            str(receipt),
            "--",
            *command,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    (asset_evidence / "stdout.log").write_text(completed.stdout, encoding="utf-8")
    (asset_evidence / "stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0 or not receipt.is_file():
        return 70, []
    data = json.loads(receipt.read_text(encoding="utf-8"))
    return int(data["dut_exit"]), [int(pid) for pid in data["survivors"]]


def main() -> int:
    arguments = parser().parse_args()
    evidence = Path(arguments.evidence)
    try:
        assets = load_visual_assets(manifest_path(arguments.manifest))
        if arguments.fragments:
            for fragment in arguments.fragments.split(","):
                assets.extend(load_visual_assets(manifest_path(fragment)))
        selected_ids = set(arguments.only.split(",")) if arguments.only else None
        selected = [asset for asset in assets if selected_ids is None or asset.asset_id in selected_ids]
        if not selected or (selected_ids is not None and {asset.asset_id for asset in selected} != selected_ids):
            raise ManifestError(f"unknown --only asset: {arguments.only}")
        for asset in selected:
            approved_command(asset)
    except ManifestError as error:
        write_invalid_cleanup(evidence, error)
        print(str(error))
        return 64
    failures: list[str] = []
    survivors: list[int] = []
    for asset in selected:
        dut_exit, remaining = capture(asset, evidence)
        survivors.extend(remaining)
        if dut_exit != 0:
            failures.append(f"{asset.asset_id}: capture exited {dut_exit}")
    status = "pass" if not failures and not survivors else "fail"
    write_summary(evidence, status, survivors, failures)
    print(json.dumps({"status": status, "errors": failures, "survivors": survivors}, ensure_ascii=False))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
