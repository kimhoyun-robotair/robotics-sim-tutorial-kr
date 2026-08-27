from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def test_nav2_worked_example_renders_mathjax_in_chromium(tmp_path: Path) -> None:
    # Given: the production documentation is built through strict MkDocs.
    site = tmp_path / "site"
    subprocess.run(
        (sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(site)),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    # When: Chromium renders the actual Nav2 route and MathJax settles.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(
            (site / "04_intermediate/10-nav2/index.html").as_uri(),
            wait_until="domcontentloaded",
        )
        worked = page.locator('.course-worked[data-worked-example="nav2-tolerance"]')
        equations = worked.locator(".arithmatex mjx-container.MathJax")
        equations.first.wait_for(state="visible", timeout=5_000)

        # Then: all four formulas are rendered and raw TeX is not visible.
        assert equations.count() == 4
        visible_text = worked.inner_text()
        assert all(
            token not in visible_text
            for token in (r"\(", r"\)", r"\sqrt", r"\operatorname", r"\mathrm")
        )
        browser.close()
