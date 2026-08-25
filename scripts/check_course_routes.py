#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Final

from jsonschema import Draft202012Validator

if TYPE_CHECKING:
    from scripts.course_route_browser import VIEWPORTS, browser_records
    from scripts.course_route_contract import (
        JsonValue,
        RouteInputError,
        load_assets,
        selected_assets,
    )
elif __package__:
    from .course_route_browser import VIEWPORTS, browser_records
    from .course_route_contract import (
        JsonValue,
        RouteInputError,
        load_assets,
        selected_assets,
    )
else:
    from course_route_browser import VIEWPORTS, browser_records
    from course_route_contract import (
        JsonValue,
        RouteInputError,
        load_assets,
        selected_assets,
    )

ROOT: Final = Path(__file__).resolve().parents[1]


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--records")
    result.add_argument("--site-dir")
    result.add_argument("--asset-manifest", default="docs/assets/manifest.yaml")
    result.add_argument("--fragments")
    result.add_argument("--routes")
    result.add_argument("--course")
    result.add_argument("--courses")
    result.add_argument("--expect-routes", type=int)
    result.add_argument("--viewports", default="desktop,mobile")
    result.add_argument("--themes", default="light,dark")
    result.add_argument("--schema", default="scripts/schemas/route-qa.schema.json")
    result.add_argument("--evidence", required=True)
    return result


def resolved(raw: str) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else ROOT / candidate


def validate_records(records: Mapping[str, JsonValue], schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = [
        error.message for error in Draft202012Validator(schema).iter_errors(records)
    ]
    routes = records.get("routes")
    if isinstance(routes, list):
        names = [record.get("route") for record in routes if isinstance(record, dict)]
        duplicates = sorted({str(name) for name in names if names.count(name) > 1})
        errors.extend(f"duplicate route: {route}" for route in duplicates)
    return errors


def write_report(path: Path, report: Mapping[str, JsonValue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


def main() -> int:
    arguments = parser().parse_args()
    evidence = Path(arguments.evidence)
    schema = resolved(arguments.schema)
    if arguments.records:
        records = json.loads(resolved(arguments.records).read_text(encoding="utf-8"))
        errors = validate_records(records, schema)
        report: dict[str, JsonValue] = {
            "schema_version": 1,
            "status": "pass" if not errors else "fail",
            "errors": errors,
            **records,
        }
        write_report(evidence, report)
        return 0 if not errors else 64
    if not arguments.site_dir:
        parser().error("--site-dir is required unless --records is used")
    courses = set(
        filter(None, (arguments.course or arguments.courses or "").split(","))
    )
    routes = {
        route.strip("/") for route in (arguments.routes or "").split(",") if route
    }
    viewports = list(filter(None, arguments.viewports.split(",")))
    themes = list(filter(None, arguments.themes.split(",")))
    try:
        if any(name not in VIEWPORTS for name in viewports) or any(
            name not in {"light", "dark"} for name in themes
        ):
            raise RouteInputError("unsupported viewport or theme")
        assets = load_assets(resolved(arguments.asset_manifest))
        if arguments.fragments:
            for fragment in arguments.fragments.split(","):
                assets.extend(load_assets(resolved(fragment)))
        assets = selected_assets(assets, courses, routes)
        ids = [asset.asset_id for asset in assets]
        if len(ids) != len(set(ids)):
            raise RouteInputError("duplicate asset id")
        if (
            arguments.expect_routes is not None
            and len(assets) != arguments.expect_routes
        ):
            raise RouteInputError(
                f"expected {arguments.expect_routes} routes, found {len(assets)}"
            )
        records_list, runtime_errors = browser_records(
            resolved(arguments.site_dir),
            assets,
            viewports,
            themes,
            evidence.with_suffix(""),
        )
        records = {"routes": records_list}
        errors = [*runtime_errors, *validate_records(records, schema)]
    except FileNotFoundError as error:
        report = {
            "schema_version": 1,
            "status": "browser_missing",
            "errors": [str(error)],
            "routes": [],
        }
        write_report(evidence, report)
        return 22
    except (OSError, RouteInputError, json.JSONDecodeError) as error:
        report = {
            "schema_version": 1,
            "status": "fail",
            "errors": [str(error)],
            "routes": [],
        }
        write_report(evidence, report)
        return 64
    report = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "errors": errors,
        **records,
    }
    write_report(evidence, report)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
