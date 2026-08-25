#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml
from jsonschema import Draft202012Validator


ROOT: Final = Path(__file__).resolve().parents[1]
VIEWPORTS: Final = {"desktop": (1280, 900), "mobile": (375, 812)}
type JsonValue = None | bool | int | float | str | Sequence[JsonValue] | Mapping[str, JsonValue]


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


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--records")
    result.add_argument("--site-dir")
    result.add_argument("--asset-manifest", default="docs/assets/manifest.yaml")
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
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(records)]
    routes = records.get("routes")
    if isinstance(routes, list):
        names = [record.get("route") for record in routes if isinstance(record, dict)]
        duplicates = sorted({str(name) for name in names if names.count(name) > 1})
        errors.extend(f"duplicate route: {route}" for route in duplicates)
    return errors


def required_text(item: dict[str, object], field: str, index: int) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RouteInputError(f"asset {index}: {field} must be nonempty text")
    return value


def load_assets(path: Path) -> list[RouteAsset]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise RouteInputError(f"{path}: {error}") from error
    if not isinstance(loaded, dict) or not isinstance(loaded.get("assets"), list):
        raise RouteInputError(f"{path}: assets must be a list")
    assets: list[RouteAsset] = []
    for index, item in enumerate(loaded["assets"]):
        if not isinstance(item, dict):
            raise RouteInputError(f"asset {index}: expected mapping")
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


def selected_assets(assets: list[RouteAsset], courses: set[str]) -> list[RouteAsset]:
    if not courses:
        return assets
    return [
        asset
        for asset in assets
        if asset.route.split("/", 1)[0] in courses or (asset.asset_id == "fixture" and "fixture" in courses)
    ]


def browser_records(
    site_dir: Path,
    assets: list[RouteAsset],
    viewports: list[str],
    themes: list[str],
    screenshot_dir: Path,
) -> tuple[list[dict[str, JsonValue]], list[str]]:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise FileNotFoundError("Playwright Chromium is not installed") from error
    records: list[dict[str, JsonValue]] = []
    browser_errors: list[str] = []
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for asset in assets:
                    console_errors: list[str] = []
                    network_errors: list[str] = []
                    state_passes: dict[str, bool] = {}
                    semantics: set[str] = {asset.semantic}
                    for viewport_name in viewports:
                        width, height = VIEWPORTS[viewport_name]
                        for theme in themes:
                            page = browser.new_page(
                                viewport={"width": width, "height": height},
                                color_scheme="dark" if theme == "dark" else "light",
                            )
                            page.on(
                                "console",
                                lambda message, errors=console_errors: errors.append(message.text)
                                if message.type == "error"
                                else None,
                            )
                            page.on(
                                "requestfailed",
                                lambda request, errors=network_errors: errors.append(
                                    f"{request.method} {request.url}: {request.failure}"
                                ),
                            )
                            html = site_dir / asset.route / "index.html"
                            response = page.goto(html.as_uri(), wait_until="networkidle", timeout=30_000)
                            page.evaluate("window.scrollTo(0, 0)")
                            page.wait_for_timeout(500)
                            image = page.locator(f'img[alt="{asset.alt_text}"]')
                            caption = page.get_by_text(asset.caption, exact=True)
                            fixture = asset.asset_id == "fixture"
                            semantic_content = True
                            if fixture:
                                page.locator(".MathJax svg").first.wait_for(state="visible", timeout=30_000)
                                page.locator(".course-mermaid svg").first.wait_for(state="visible", timeout=30_000)
                                equation_glyphs = page.locator(".MathJax svg path, .MathJax svg use").count()
                                diagram_text = page.locator(".course-mermaid svg").first.text_content() or ""
                                semantic_content = equation_glyphs > 5 and all(
                                    label in diagram_text for label in ("명령 입력", "Gazebo 시뮬레이션", "관측 결과")
                                )
                                semantics.update(("mathjax-equation", "mermaid-diagram", "responsive-image"))
                            clipping = page.evaluate(
                                "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
                            )
                            visible = image.is_visible() and caption.is_visible() and bool(clipping) and semantic_content
                            state_passes[f"{theme}:{viewport_name}"] = visible
                            page.screenshot(
                                path=str(screenshot_dir / f"{asset.asset_id}-{theme}-{viewport_name}.png"),
                                full_page=True,
                            )
                            page.close()
                            if response is not None and response.status >= 400:
                                browser_errors.append(f"{asset.route}: HTTP {response.status}")
                    asset_path = ROOT / "docs" / asset.path
                    records.append(
                        {
                            "route": f"/{asset.route}",
                            "visual_ids": [asset.asset_id],
                            "semantic_assertions": sorted(semantics),
                            "alt_text": asset.alt_text,
                            "caption": asset.caption,
                            "source_sha": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
                            "light": all(state_passes.get(f"light:{name}", False) for name in viewports),
                            "dark": all(state_passes.get(f"dark:{name}", False) for name in viewports),
                            "desktop": all(state_passes.get(f"{theme}:desktop", False) for theme in themes),
                            "mobile": all(state_passes.get(f"{theme}:mobile", False) for theme in themes),
                            "console_clean": not console_errors,
                            "network_clean": not network_errors,
                            "no_clipping": all(state_passes.values()),
                        }
                    )
                    browser_errors.extend(console_errors + network_errors)
            finally:
                browser.close()
    except PlaywrightError as error:
        if "Executable doesn't exist" in str(error) or "browserType.launch" in str(error):
            raise FileNotFoundError("Playwright Chromium is not installed") from error
        raise RouteInputError(str(error)) from error
    return records, browser_errors


def write_report(path: Path, report: Mapping[str, JsonValue]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    courses = set(filter(None, (arguments.course or arguments.courses or "").split(",")))
    viewports = list(filter(None, arguments.viewports.split(",")))
    themes = list(filter(None, arguments.themes.split(",")))
    try:
        if any(name not in VIEWPORTS for name in viewports) or any(name not in {"light", "dark"} for name in themes):
            raise RouteInputError("unsupported viewport or theme")
        assets = selected_assets(load_assets(resolved(arguments.asset_manifest)), courses)
        if arguments.expect_routes is not None and len(assets) != arguments.expect_routes:
            raise RouteInputError(f"expected {arguments.expect_routes} routes, found {len(assets)}")
        records_list, runtime_errors = browser_records(
            resolved(arguments.site_dir), assets, viewports, themes, evidence.with_suffix("")
        )
        records: dict[str, JsonValue] = {"routes": records_list}
        errors = [*runtime_errors, *validate_records(records, schema)]
    except FileNotFoundError as error:
        report: dict[str, JsonValue] = {
            "schema_version": 1,
            "status": "browser_missing",
            "errors": [str(error)],
            "routes": [],
        }
        write_report(evidence, report)
        return 22
    except (OSError, RouteInputError, json.JSONDecodeError) as error:
        report = {"schema_version": 1, "status": "fail", "errors": [str(error)], "routes": []}
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
