from __future__ import annotations

import hashlib
import os
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import yaml


class AuditInputError(ValueError):
    pass


def parse_task_range(raw: str) -> set[int]:
    required: set[int] = set()
    for part in raw.split(","):
        bounds = part.split("-", 1)
        if len(bounds) == 1:
            required.add(int(bounds[0]))
        else:
            required.update(range(int(bounds[0]), int(bounds[1]) + 1))
    return required


def installed_artifact_errors(
    contract: Mapping[str, object], evidence_root: Path
) -> list[str]:
    install_override = os.environ.get("TUTORIAL_INSTALL_BASE")
    install_base = (
        Path(install_override)
        if install_override
        else evidence_root / "task-15/fresh-install"
    )
    installed = contract.get("installed_artifacts")
    if not isinstance(installed, list) or any(
        not (install_base / str(item)).is_file() for item in installed
    ):
        return ["missing_installed_artifact"]
    return []


def manifest_errors(
    path: Path, evidence_root: Path
) -> tuple[list[str], dict[str, int]]:
    try:
        manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise AuditInputError(f"{path}: {error}") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("routes"), list):
        raise AuditInputError("invalid course manifest")
    routes = manifest["routes"]
    counts = Counter(
        str(route.get("course")) for route in routes if isinstance(route, dict)
    )
    expected = {"beginner": 12, "intermediate": 12, "advanced": 7}
    errors = [] if counts == expected else ["route_count"]
    declared = {str(route.get("path")) for route in routes if isinstance(route, dict)}
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            errors.append("invalid_route")
            continue
        route_path = Path("docs") / str(route.get("path"))
        prerequisites = route.get("prerequisites")
        if (
            not route_path.is_file()
            or not isinstance(prerequisites, list)
            or any(str(item) not in declared for item in prerequisites)
        ):
            errors.append("route_contract")
        elif index + 1 < len(routes):
            following = routes[index + 1]
            next_name = (
                Path(str(following.get("path"))).name
                if isinstance(following, dict)
                else ""
            )
            if next_name not in route_path.read_text(encoding="utf-8"):
                errors.append("next_link")
    if manifest.get("compatibility") != {
        "ubuntu": "24.04",
        "ros": "jazzy",
        "gazebo": "harmonic",
        "sdformat": "14",
    }:
        errors.append("compatibility_marker")
    contract = manifest.get("audit_contract")
    if not isinstance(contract, dict):
        return [*errors, "audit_contract"], dict(counts)
    sources = contract.get("source_files")
    if not isinstance(sources, list) or any(
        not Path(str(item)).is_file() for item in sources
    ):
        errors.append("missing_source")
    errors.extend(installed_artifact_errors(contract, evidence_root))
    asset_manifest = Path(str(contract.get("asset_manifest", "")))
    try:
        asset_data = yaml.safe_load(asset_manifest.read_text(encoding="utf-8"))
        fragments = (
            asset_data.get("consolidated_fragments", [])
            if isinstance(asset_data, dict)
            else []
        )
        assets = (
            list(asset_data.get("assets", [])) if isinstance(asset_data, dict) else []
        )
        for fragment in fragments:
            fragment_data = yaml.safe_load(
                Path(str(fragment)).read_text(encoding="utf-8")
            )
            assets.extend(
                fragment_data.get("assets", [])
                if isinstance(fragment_data, dict)
                else []
            )
        if not isinstance(asset_data, dict) or len(assets) != asset_data.get(
            "consolidated_asset_count"
        ):
            errors.append("asset_inventory")
        for asset in assets:
            if not isinstance(asset, dict):
                errors.append("asset_inventory")
                continue
            asset_path = Path("docs") / str(asset.get("path"))
            if not asset_path.is_file() or hashlib.sha256(
                asset_path.read_bytes()
            ).hexdigest() != asset.get("sha256"):
                errors.append("stale_asset")
    except (OSError, yaml.YAMLError, AttributeError, TypeError):
        errors.append("asset_inventory")
    return errors, dict(counts)
