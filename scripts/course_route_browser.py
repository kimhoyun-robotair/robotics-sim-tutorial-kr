from __future__ import annotations

import hashlib
import re
from html import unescape
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from scripts.course_route_contract import JsonValue, RouteAsset, RouteInputError
elif __package__:
    from .course_route_contract import JsonValue, RouteAsset, RouteInputError
else:
    from course_route_contract import JsonValue, RouteAsset, RouteInputError

ROOT: Final = Path(__file__).resolve().parents[1]
VIEWPORTS: Final = {"desktop": (1280, 900), "mobile": (375, 812)}


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
            browser = playwright.chromium.launch(channel="chrome", headless=True)
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
                                lambda message, errors=console_errors: (
                                    errors.append(message.text)
                                    if message.type == "error"
                                    else None
                                ),
                            )
                            page.on(
                                "requestfailed",
                                lambda request, errors=network_errors: errors.append(
                                    f"{request.method} {request.url}: {request.failure}"
                                ),
                            )
                            html = site_dir / asset.route / "index.html"
                            response = page.goto(
                                html.as_uri(),
                                wait_until="domcontentloaded",
                                timeout=30_000,
                            )
                            page.evaluate("window.scrollTo(0, 0)")
                            image = page.locator(f'img[alt="{asset.alt_text}"]')
                            image.scroll_into_view_if_needed(timeout=30_000)
                            image.wait_for(state="visible", timeout=30_000)
                            caption = image.locator(
                                "xpath=following-sibling::figcaption[1]"
                            )
                            expected_caption = re.sub(
                                r"<[^>]*>", "", unescape(asset.caption)
                            )
                            caption_visible = (
                                caption.count() == 1
                                and caption.is_visible()
                                and caption.inner_text() == expected_caption
                            )
                            semantic_content = True
                            if asset.asset_id == "fixture":
                                page.locator(".MathJax svg").first.wait_for(
                                    state="visible", timeout=30_000
                                )
                                page.locator(".course-mermaid svg").first.wait_for(
                                    state="visible", timeout=30_000
                                )
                                equation_glyphs = page.locator(
                                    ".MathJax svg path, .MathJax svg use"
                                ).count()
                                diagram_text = (
                                    page.locator(
                                        ".course-mermaid svg"
                                    ).first.text_content()
                                    or ""
                                )
                                semantic_content = equation_glyphs > 5 and all(
                                    label in diagram_text
                                    for label in (
                                        "명령 입력",
                                        "Gazebo 시뮬레이션",
                                        "관측 결과",
                                    )
                                )
                                semantics.update(
                                    (
                                        "mathjax-equation",
                                        "mermaid-diagram",
                                        "responsive-image",
                                    )
                                )
                            clipping = page.evaluate(
                                "() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"
                            )
                            if asset.route.startswith("intermediate/"):
                                worked = page.locator(
                                    f'.course-worked[data-worked-example="{asset.asset_id}"]'
                                )
                                worked_visible = (
                                    worked.count() == 1
                                    and worked.is_visible()
                                    and bool(worked.inner_text().strip())
                                )
                                semantic_content = semantic_content and worked_visible
                                semantics.add("worked-explanation-rendered")
                            visible = (
                                image.is_visible()
                                and caption_visible
                                and bool(clipping)
                                and semantic_content
                            )
                            state_passes[f"{theme}:{viewport_name}"] = visible
                            page.screenshot(
                                path=str(
                                    screenshot_dir
                                    / f"{asset.asset_id}-{theme}-{viewport_name}.png"
                                ),
                                full_page=True,
                            )
                            page.close()
                            if response is not None and response.status >= 400:
                                browser_errors.append(
                                    f"{asset.route}: HTTP {response.status}"
                                )
                    asset_path = ROOT / "docs" / asset.path
                    records.append(
                        {
                            "route": f"/{asset.route}",
                            "visual_ids": [asset.asset_id],
                            "semantic_assertions": sorted(semantics),
                            "alt_text": asset.alt_text,
                            "caption": asset.caption,
                            "source_sha": hashlib.sha256(
                                asset_path.read_bytes()
                            ).hexdigest(),
                            "light": all(
                                state_passes.get(f"light:{name}", False)
                                for name in viewports
                            ),
                            "dark": all(
                                state_passes.get(f"dark:{name}", False)
                                for name in viewports
                            ),
                            "desktop": all(
                                state_passes.get(f"{theme}:desktop", False)
                                for theme in themes
                            ),
                            "mobile": all(
                                state_passes.get(f"{theme}:mobile", False)
                                for theme in themes
                            ),
                            "console_clean": not console_errors,
                            "network_clean": not network_errors,
                            "no_clipping": all(state_passes.values()),
                        }
                    )
                    browser_errors.extend(console_errors + network_errors)
            finally:
                browser.close()
    except PlaywrightError as error:
        if "Executable doesn't exist" in str(error) or "browserType.launch" in str(
            error
        ):
            raise FileNotFoundError("Playwright Chromium is not installed") from error
        raise RouteInputError(str(error)) from error
    return records, browser_errors
