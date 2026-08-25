from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

type JsonValue = (
    None | bool | int | float | str | Sequence[JsonValue] | Mapping[str, JsonValue]
)


@dataclass(frozen=True, slots=True)
class RouteAsset:
    asset_id: str
    path: str
    route: str
    semantic: str
    alt_text: str
    caption: str


class RouteInputError(ValueError):
    pass


def required_text(item: dict[str, object], field: str, index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RouteInputError(f"asset {index}: {field} must be nonempty text")
    return value


def load_assets(path: Path) -> list[RouteAsset]:
    assets: list[RouteAsset] = []
    manifests = (path, *sorted((path.parent / "manifests").glob("*.yaml")))
    for manifest in manifests:
        try:
            loaded = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise RouteInputError(f"{manifest}: {error}") from error
        if not isinstance(loaded, dict) or not isinstance(loaded.get("assets"), list):
            raise RouteInputError(f"{manifest}: assets must be a list")
        for index, item in enumerate(loaded["assets"]):
            if not isinstance(item, dict):
                raise RouteInputError(f"{manifest}: asset {index}: expected mapping")
            assets.append(
                RouteAsset(
                    asset_id=required_text(item, "id", index),
                    path=required_text(item, "path", index),
                    route=required_text(item, "route", index),
                    semantic=required_text(item, "semantic_observable", index),
                    alt_text=required_text(item, "alt_text", index),
                    caption=required_text(item, "caption", index),
                )
            )
    return assets


def selected_assets(
    assets: list[RouteAsset], courses: set[str], routes: set[str]
) -> list[RouteAsset]:
    if routes:
        return [asset for asset in assets if asset.route.strip("/") in routes]
    if not courses:
        return assets
    return [
        asset
        for asset in assets
        if asset.route.split("/", 1)[0] in courses
        or (asset.asset_id == "fixture" and "fixture" in courses)
    ]
