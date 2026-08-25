#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypeAlias

import yaml

ROOT: Final = Path(__file__).resolve().parents[1]
VISUAL_SUFFIXES: Final = frozenset({".png", ".webp", ".svg"})
PRIVATE_PATH: Final = re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\\\Users\\\\)")
JsonValue: TypeAlias = (
    str | int | float | bool | None | Sequence["JsonValue"] | Mapping[str, "JsonValue"]
)


@dataclass(frozen=True, slots=True)
class VisualAsset:
    asset_id: str
    path: str
    route: str
    source_command: str
    semantic_observable: str
    alt_text: str
    caption: str
    sha256: str


class ManifestError(ValueError):
    pass


def required_text(item: Mapping[str, JsonValue], field: str, index: int) -> str:
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
                route=required_text(item, "route", index),
                source_command=required_text(item, "source_command", index),
                semantic_observable=required_text(item, "semantic_observable", index),
                alt_text=required_text(item, "alt_text", index),
                caption=required_text(item, "caption", index),
                sha256=required_text(item, "sha256", index),
            )
        )
    return assets


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--manifest", required=True)
    result.add_argument("--fragments", nargs="+")
    result.add_argument("--assets-root")
    result.add_argument("--site-dir")
    result.add_argument("--evidence", required=True)
    return result


def resolved(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def asset_errors(asset: VisualAsset, assets_root: Path) -> list[str]:
    errors: list[str] = []
    relative = Path(asset.path)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("assets",):
        return [f"{asset.asset_id}: unsafe asset path"]
    asset_path = assets_root / Path(*relative.parts[1:])
    fields = (asset.source_command, asset.semantic_observable, asset.alt_text, asset.caption)
    if not asset.alt_text.strip():
        errors.append(f"{asset.asset_id}: alt_text is required")
    if not asset.caption.strip():
        errors.append(f"{asset.asset_id}: caption is required")
    if not asset.semantic_observable.strip():
        errors.append(f"{asset.asset_id}: semantic_observable is required")
    if any(PRIVATE_PATH.search(field) for field in fields):
        errors.append(f"{asset.asset_id}: absolute home path leaked")
    if not asset_path.is_file():
        errors.append(f"{asset.asset_id}: missing file {asset.path}")
    else:
        if PRIVATE_PATH.search(asset_path.read_text(encoding="utf-8", errors="replace")):
            errors.append(f"{asset.asset_id}: absolute home path leaked in asset")
        if hashlib.sha256(asset_path.read_bytes()).hexdigest() != asset.sha256:
            errors.append(f"{asset.asset_id}: stale generated asset sha256 mismatch")
    return errors


def site_errors(asset: VisualAsset, site_dir: Path) -> list[str]:
    route_html = site_dir / asset.route / "index.html"
    if not route_html.is_file():
        return [f"{asset.asset_id}: rendered route missing"]
    html = route_html.read_text(encoding="utf-8")
    errors: list[str] = []
    if asset.path not in html and Path(asset.path).name not in html:
        errors.append(f"{asset.asset_id}: rendered asset link missing")
    if asset.alt_text not in html:
        errors.append(f"{asset.asset_id}: rendered alt text missing")
    if asset.caption not in html:
        errors.append(f"{asset.asset_id}: rendered caption missing")
    return errors


def audit(
    manifests: tuple[Path, ...], assets_root: Path, site_dir: Path | None
) -> tuple[dict[str, JsonValue], int]:
    assets = [asset for manifest in manifests for asset in load_visual_assets(manifest)]
    errors: list[str] = []
    ids = [asset.asset_id for asset in assets]
    paths = [asset.path for asset in assets]
    if len(ids) != len(set(ids)):
        errors.append("duplicate asset id")
    if len(paths) != len(set(paths)):
        errors.append("duplicate asset path")
    for asset in assets:
        errors.extend(asset_errors(asset, assets_root))
        if site_dir is not None:
            errors.extend(site_errors(asset, site_dir))
    registered = {Path(path).relative_to("assets").as_posix() for path in paths if path.startswith("assets/")}
    actual = {
        path.relative_to(assets_root).as_posix()
        for path in assets_root.rglob("*")
        if path.is_file() and path.suffix.lower() in VISUAL_SUFFIXES
    }
    errors.extend(f"unregistered asset: {path}" for path in sorted(actual - registered))
    records: list[JsonValue] = []
    for asset in assets:
        record: dict[str, JsonValue] = {
            "id": asset.asset_id,
            "path": asset.path,
            "sha256": hashlib.sha256((assets_root / Path(asset.path).relative_to("assets")).read_bytes()).hexdigest()
            if (assets_root / Path(asset.path).relative_to("assets")).is_file()
            else None,
        }
        records.append(record)
    report: dict[str, JsonValue] = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "assets": records,
        "errors": errors,
        "quality_gate": "semantic",
    }
    if not errors:
        return report, 0
    return report, 64 if any("missing file" in error for error in errors) else 1


def main() -> int:
    arguments = parser().parse_args()
    manifest = resolved(arguments.manifest)
    fragments = tuple(
        resolved(fragment)
        for raw_fragment in arguments.fragments or ()
        for fragment in raw_fragment.split(",")
    )
    assets_root = resolved(arguments.assets_root) if arguments.assets_root else ROOT / "docs" / "assets"
    site_dir = resolved(arguments.site_dir) if arguments.site_dir else None
    try:
        report, exit_code = audit((manifest, *fragments), assets_root, site_dir)
    except ManifestError as error:
        report, exit_code = {"schema_version": 1, "status": "fail", "errors": [str(error)]}, 64
    evidence = Path(arguments.evidence)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
