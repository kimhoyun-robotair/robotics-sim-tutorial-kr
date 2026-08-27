#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "playwright==1.55.0",
#   "pydantic>=2.11,<3",
#   "typer>=0.16,<1",
# ]
# ///

# ─── How to run ───
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run scripts/check_intermediate_docs.py --site URL --routes-file FILE --json REPORT
# 3. Or make executable and run:
#      chmod +x scripts/check_intermediate_docs.py && ./scripts/check_intermediate_docs.py --help
# ──────────────────

"""Audit the frozen Intermediate documentation through a real Chromium DOM."""

from __future__ import annotations

import os
import re
import shutil
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, ClassVar, Final
from urllib.parse import urldefrag, urljoin, urlparse

import typer
from playwright.sync_api import (
    ConsoleMessage,
    Error,
    Page,
    Request,
    Response,
    sync_playwright,
)
from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True, slots=True)
class RouteSpec:
    """One frozen route, rendered H1, and Markdown source mapping."""

    route: str
    h1: str
    source: str


FROZEN_ROUTES: tuple[RouteSpec, ...] = (
    RouteSpec("/04_intermediate/", "중급 과정: ROS 2 통합", "docs/04_intermediate/index.md"),
    RouteSpec(
        "/04_intermediate/01-advanced-sdf/",
        "고급 SDF와 물리 속성",
        "docs/04_intermediate/01-advanced-sdf.md",
    ),
    RouteSpec(
        "/04_intermediate/02-urdf-xacro-sdf/",
        "URDF·Xacro·SDF 구분",
        "docs/04_intermediate/02-urdf-xacro-sdf.md",
    ),
    RouteSpec(
        "/04_intermediate/03-ros2-launch/",
        "ROS 2 Launch 실행",
        "docs/04_intermediate/03-ros2-launch.md",
    ),
    RouteSpec(
        "/04_intermediate/04-spawn-model/",
        "Robot Spawn과 위치",
        "docs/04_intermediate/04-spawn-model.md",
    ),
    RouteSpec(
        "/04_intermediate/05-bridge-yaml/",
        "ros_gz_bridge YAML 심화",
        "docs/04_intermediate/05-bridge-yaml.md",
    ),
    RouteSpec(
        "/04_intermediate/06-tf-rviz/",
        "TF·Joint State·RViz 검증",
        "docs/04_intermediate/06-tf-rviz.md",
    ),
    RouteSpec(
        "/04_intermediate/07-gz-ros2-control/",
        "gz_ros2_control과 controller",
        "docs/04_intermediate/07-gz-ros2-control.md",
    ),
    RouteSpec(
        "/04_intermediate/08-advanced-sensors/",
        "센서 심화: 노이즈와 주기",
        "docs/04_intermediate/08-advanced-sensors.md",
    ),
    RouteSpec(
        "/04_intermediate/09-multi-robot/",
        "다중 로봇 namespace와 TF",
        "docs/04_intermediate/09-multi-robot.md",
    ),
    RouteSpec(
        "/04_intermediate/10-nav2/", "Gazebo와 Nav2 연동", "docs/04_intermediate/10-nav2.md"
    ),
    RouteSpec(
        "/04_intermediate/11_project-autonomous-bot/",
        "자율주행 tutorial_bot 프로젝트",
        "docs/04_intermediate/11_project-autonomous-bot.md",
    ),
)
ROUTE_LOOKUP = {item.route: item for item in FROZEN_ROUTES}
SOURCE_REFERENCE = re.compile(r"(?<![\w/])((?:examples|scripts)/[A-Za-z0-9_.\-/]+)")
NAV_TARGET = re.compile(
    r"^\s{6}- [^:]+:\s+(04_intermediate/[A-Za-z0-9_.\-]+\.md)\s*$", re.MULTILINE
)
HTTP_OK: Final = 200
HTTP_ERROR_MIN: Final = 400
GENERATED_REFERENCE_PREFIXES: Final = ("examples/ros2_ws/install/",)


class DomMetrics(BaseModel):
    """Browser-computed CJK and horizontal-layout measurements."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    document_overflow: int
    code_overflow: int
    tofu: bool
    orphan_lines: tuple[str, ...]


class RouteResult(BaseModel):
    """Machine-readable audit outcome for one rendered route."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    route: str
    expected_h1: str | None
    http_status: int | None
    h1: str
    active_nav: bool
    broken_links: tuple[str, ...]
    console_errors: tuple[str, ...]
    network_errors: tuple[str, ...]
    document_overflow: int
    code_overflow: int
    tofu: bool
    orphan_lines: tuple[str, ...]
    source_references_missing: tuple[str, ...]
    errors: tuple[str, ...]
    passed: bool


class AuditReport(BaseModel):
    """Machine-readable complete documentation audit report."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    schema_version: int = 1
    site: str
    routes_file: str
    route_count: int
    contract_errors: tuple[str, ...]
    interaction_errors: tuple[str, ...]
    routes: tuple[RouteResult, ...]
    passed: bool


class InputError(ValueError):
    """A typed malformed CLI-input error."""


def parse_routes(path: Path) -> tuple[str, ...]:
    """Parse unique same-origin absolute paths from a routes file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise InputError(f"cannot read routes file {path}: {error}") from error
    routes = tuple(
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    )
    for route in routes:
        parsed = urlparse(route)
        if (
            parsed.scheme
            or parsed.netloc
            or not route.startswith("/")
            or parsed.query
            or parsed.fragment
        ):
            raise InputError(
                f"invalid route {route!r}: expected an absolute path without query or fragment"
            )
    if not routes or len(set(routes)) != len(routes):
        raise InputError("routes file must contain unique nonempty routes")
    return routes


def contract_errors(
    routes: tuple[str, ...], source_root: Path, allow_subset: bool
) -> tuple[str, ...]:
    """Compare route input and MkDocs nav with the frozen 12-route contract."""
    if allow_subset:
        return ()
    expected = tuple(item.route for item in FROZEN_ROUTES)
    errors = (
        [] if routes == expected else [f"routes differ from frozen 12: got {routes!r}"]
    )
    mkdocs = source_root / "mkdocs.yml"
    try:
        targets = tuple(NAV_TARGET.findall(mkdocs.read_text(encoding="utf-8")))
    except OSError as error:
        return (*errors, f"cannot read {mkdocs}: {error}")
    frozen_targets = tuple(item.source.removeprefix("docs/") for item in FROZEN_ROUTES)
    if targets != frozen_targets:
        errors.append(
            f"MkDocs Intermediate nav differs from frozen 12: got {targets!r}"
        )
    return tuple(errors)


def source_reference_errors(
    spec: RouteSpec | None, source_root: Path
) -> tuple[str, ...]:
    """Find missing repository paths cited by a lesson source."""
    if spec is None:
        return ()
    source = source_root / spec.source
    try:
        text = source.read_text(encoding="utf-8")
    except OSError:
        return (spec.source,)
    references = sorted({match.group(1) for match in SOURCE_REFERENCE.finditer(text)})
    return tuple(
        reference
        for reference in references
        if not reference.startswith(GENERATED_REFERENCE_PREFIXES)
        and not (source_root / reference).exists()
    )


def read_dom_metrics(page: Page) -> DomMetrics:
    """Read overflow, tofu, and short terminal CJK lines from live layout."""
    page.locator("body").evaluate("""body => {
      const orphanLines = [];
      for (const element of document.querySelectorAll('main p, main li')) {
        const node = [...element.childNodes].find(item => item.nodeType === Node.TEXT_NODE && item.textContent.trim());
        if (!node) continue;
        const lines = new Map();
        [...node.textContent].forEach((character, index) => {
          const range = document.createRange(); range.setStart(node, index); range.setEnd(node, index + 1);
          const rect = range.getBoundingClientRect();
          if (rect.width > 0) lines.set(Math.round(rect.top), (lines.get(Math.round(rect.top)) || '') + character);
        });
        const rendered = [...lines.values()].map(line => line.trim()).filter(Boolean);
        if (rendered.length > 1 && /^[가-힣]{1,2}$/.test(rendered.at(-1))) orphanLines.push(rendered.at(-1));
      }
      body.dataset.docAudit = JSON.stringify({
        document_overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
        code_overflow: [...document.querySelectorAll('pre, code')].filter(node => node.scrollWidth > node.clientWidth + 1).length,
        tofu: body.innerText.includes('\ufffd'), orphan_lines: orphanLines,
      });
    }""")
    raw = page.locator("body").get_attribute("data-doc-audit")
    if raw is None:
        raise InputError("browser DOM metrics were not produced")
    return DomMetrics.model_validate_json(raw)


def audit_route(page: Page, route: str, site: str, source_root: Path) -> RouteResult:
    """Audit one route through real browser HTTP and DOM surfaces."""
    console_errors: list[str] = []
    network_errors: list[str] = []

    def record_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    def record_failure(request: Request) -> None:
        network_errors.append(f"failed {request.url}")

    def record_response(response: Response) -> None:
        if response.status >= HTTP_ERROR_MIN:
            network_errors.append(f"{response.status} {response.url}")

    page.on("console", record_console)
    page.on("requestfailed", record_failure)
    page.on("response", record_response)
    spec = ROUTE_LOOKUP.get(route)
    response = page.goto(urljoin(site, route), wait_until="networkidle")
    http_status = response.status if response is not None else None
    h1_locator = page.locator("main h1").first
    h1 = (
        re.sub(r"¶$", "", h1_locator.inner_text()).strip() if h1_locator.count() else ""
    )
    active = page.locator(
        "nav.md-nav--primary a.md-nav__link--active, nav a.md-nav__link--active"
    ).first
    active_href = active.get_attribute("href") if active.count() else None
    active_nav = bool(
        active_href and urljoin(page.url, urldefrag(active_href)[0]) == page.url
    )
    metrics = read_dom_metrics(page)
    links = page.locator("main a[href]")
    broken: list[str] = []
    for index in range(links.count()):
        href = links.nth(index).get_attribute("href") or ""
        target = urldefrag(urljoin(page.url, href))[0]
        if urlparse(target).netloc == urlparse(site).netloc:
            link_response = page.request.get(target)
            if not link_response.ok:
                broken.append(f"{link_response.status} {target}")
    errors: list[str] = []
    if http_status != HTTP_OK:
        errors.append(f"http_status={http_status}")
    if spec is None:
        errors.append("route_not_frozen")
    elif h1 != spec.h1:
        errors.append(f"h1={h1!r}")
    if not active_nav:
        errors.append("active_nav=false")
    missing_refs = source_reference_errors(spec, source_root)
    passed = not (
        errors
        or broken
        or console_errors
        or network_errors
        or metrics.document_overflow > 1
        or metrics.code_overflow
        or metrics.tofu
        or metrics.orphan_lines
        or missing_refs
    )
    return RouteResult(
        route=route,
        expected_h1=spec.h1 if spec else None,
        http_status=http_status,
        h1=h1,
        active_nav=active_nav,
        broken_links=tuple(sorted(set(broken))),
        console_errors=tuple(console_errors),
        network_errors=tuple(network_errors),
        document_overflow=metrics.document_overflow,
        code_overflow=metrics.code_overflow,
        tofu=metrics.tofu,
        orphan_lines=metrics.orphan_lines,
        source_references_missing=missing_refs,
        errors=tuple(errors),
        passed=passed,
    )


def navigation_errors(page: Page, site: str) -> tuple[str, ...]:
    """Drive the primary Intermediate navigation link through page.click."""
    try:
        _ = page.goto(urljoin(site, "/04_intermediate/"), wait_until="networkidle")
        drawer = page.locator('label.md-header__button[for="__drawer"]')
        if drawer.is_visible():
            drawer.click()
        page.click('a.md-nav__link[href="01-advanced-sdf/"]')
        page.wait_for_url("**/04_intermediate/01-advanced-sdf/")
    except Error as error:
        return (str(error),)
    return ()


DEFAULT_SOURCE_ROOT: Final = Path()


def main(
    site: Annotated[str, typer.Option("--site")],
    routes_file: Annotated[Path, typer.Option("--routes-file")],
    json_path: Annotated[Path, typer.Option("--json")],
    source_root: Annotated[Path, typer.Option("--source-root")] = DEFAULT_SOURCE_ROOT,
    timeout_seconds: Annotated[
        float, typer.Option("--timeout-seconds", min=1.0)
    ] = 30.0,
    viewport_width: Annotated[int, typer.Option("--viewport-width", min=320)] = 1280,
    allow_subset: Annotated[bool, typer.Option("--allow-subset")] = False,
) -> None:
    """Crawl the frozen Intermediate documentation and write a JSON report."""
    routes = parse_routes(routes_file)
    errors = contract_errors(routes, source_root, allow_subset)
    with sync_playwright() as playwright:
        browser_path = (
            None
            if os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
            else shutil.which("google-chrome")
        )
        browser = playwright.chromium.launch(
            headless=True, executable_path=browser_path
        )
        context = browser.new_context(viewport={"width": viewport_width, "height": 900})
        context.set_default_timeout(timeout_seconds * 1000)
        results = tuple(
            audit_route(context.new_page(), route, site.rstrip("/") + "/", source_root)
            for route in routes
        )
        interactions = (
            () if allow_subset else navigation_errors(context.new_page(), site)
        )
        context.close()
        browser.close()
    report = AuditReport(
        site=site,
        routes_file=str(routes_file),
        route_count=len(routes),
        contract_errors=errors,
        interaction_errors=interactions,
        routes=results,
        passed=not errors
        and not interactions
        and all(result.passed for result in results),
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    _ = json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(report.model_dump_json(indent=2))
    if not report.passed:
        raise typer.Exit(code=1)


def cli() -> None:
    """Run the CLI boundary with typed input errors."""
    try:
        typer.run(main)
    except (InputError, Error, OSError, socket.gaierror) as error:
        typer.echo(f"documentation audit error: {error}", err=True)
        raise SystemExit(2) from None


if __name__ == "__main__":
    cli()
