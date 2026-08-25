#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Final

import yaml


ROOT: Final = Path(__file__).resolve().parents[1]
CLASSIC_TOKENS: Final = ("gazebo classic", "ign gazebo", "gazebo_ros")
COURSES: Final = ("beginner", "intermediate", "advanced")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--manifest", required=True)
    result.add_argument("--site-config", default="mkdocs.yml")
    result.add_argument("--expect-routes", type=int)
    result.add_argument("--evidence", required=True)
    result.add_argument("--forbid-classic", action="store_true")
    result.add_argument("--forbid-advanced-scope")
    result.add_argument("--require-korean-alt", action="store_true")
    result.add_argument("--require-source-metadata", action="store_true")
    return result


def load_mapping(path: Path) -> dict[str, object]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"{path}: {error}") from error
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: expected mapping")
    return loaded


def nav_paths(value: object) -> list[str]:
    paths: list[str] = []
    if isinstance(value, list):
        for item in value:
            paths.extend(nav_paths(item))
    elif isinstance(value, dict):
        for child in value.values():
            paths.extend(nav_paths(child))
    elif isinstance(value, str) and value.endswith(".md"):
        paths.append(value)
    return paths


def route_mappings(manifest: dict[str, object]) -> list[dict[str, object]]:
    raw = manifest.get("routes")
    if not isinstance(raw, list):
        raise ValueError("manifest routes must be a list")
    routes: list[dict[str, object]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"route {index} must be a mapping")
        routes.append(item)
    return routes


def classic_errors(manifest: dict[str, object]) -> list[str]:
    allowed_raw = manifest.get("migration_warning_files", [])
    allowed = {str(item) for item in allowed_raw} if isinstance(allowed_raw, list) else set()
    errors: list[str] = []
    for path in sorted((ROOT / "docs").rglob("*.md")):
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8").lower()
        if relative not in allowed and any(token in text for token in CLASSIC_TOKENS):
            errors.append(f"forbidden Classic token outside migration warning: {relative}")
    return errors


def audit(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    manifest_path = ROOT / args.manifest
    config_path = ROOT / args.site_config
    manifest = load_mapping(manifest_path)
    config = load_mapping(config_path)
    routes = route_mappings(manifest)
    paths = [str(route.get("path", "")) for route in routes]
    counts = Counter(paths)
    duplicates = sorted(path for path, count in counts.items() if path and count > 1)
    nav_counts = Counter(nav_paths(config.get("nav")))
    unresolved = sorted(path for path in paths if not path or not (ROOT / "docs" / path).is_file())
    nav_errors = sorted(path for path in paths if nav_counts[path] != 1)
    declared = set(paths)
    prerequisite_errors: list[str] = []
    advanced_mapping_errors: list[str] = []
    course_counts = Counter(str(route.get("course", "")) for route in routes)
    for route in routes:
        route_path = str(route.get("path", ""))
        prerequisites = route.get("prerequisites", [])
        if not isinstance(prerequisites, list):
            prerequisite_errors.append(f"{route_path}: prerequisites must be a list")
        else:
            prerequisite_errors.extend(
                f"{route_path}: unresolved prerequisite {item}"
                for item in prerequisites
                if str(item) not in declared
            )
        if route.get("course") == "advanced" and route.get("implementation_todo") not in range(9, 15):
            advanced_mapping_errors.append(f"{route_path}: missing implementation todo 9-14")
    errors = [
        *(f"duplicate route: {path}" for path in duplicates),
        *(f"unresolved route: {path}" for path in unresolved),
        *(f"route must occur exactly once in nav: {path}" for path in nav_errors),
        *prerequisite_errors,
        *advanced_mapping_errors,
        *classic_errors(manifest),
    ]
    if args.expect_routes is not None and len(routes) != args.expect_routes:
        errors.append(f"expected {args.expect_routes} routes, found {len(routes)}")
    expected_counts = manifest.get("route_counts")
    if isinstance(expected_counts, dict):
        for course in COURSES:
            if course_counts[course] != expected_counts.get(course):
                errors.append(f"{course}: route count does not match manifest contract")
    if args.forbid_advanced_scope:
        advanced_text = "\n".join(path.read_text(encoding="utf-8").lower() for path in (ROOT / "docs/advanced").glob("*.md"))
        errors.extend(
            f"forbidden advanced scope: {token}"
            for token in args.forbid_advanced_scope.lower().split(",")
            if token and token in advanced_text
        )
    report: dict[str, object] = {
        "schema_version": 1,
        "status": "pass" if not errors else "fail",
        "route_count": len(routes),
        "course_counts": {course: course_counts[course] for course in COURSES},
        "duplicate_routes": duplicates,
        "unresolved_routes": unresolved,
        "nav_errors": nav_errors,
        "errors": errors,
        "compatibility": manifest.get("compatibility"),
    }
    return report, 0 if not errors else 64


def main() -> int:
    args = parser().parse_args()
    try:
        report, exit_code = audit(args)
    except ValueError as error:
        report, exit_code = {"schema_version": 1, "status": "fail", "errors": [str(error)]}, 64
    evidence = Path(args.evidence)
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
