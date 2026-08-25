from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BEGINNER_PAGES = (
    ("index.md", "초급: Gazebo Sim으로 `tutorial_bot` 시작하기", None),
    (
        "01-gazebo-overview.md",
        "Gazebo Sim 개요와 GUI",
        "gz sim examples/gazebo/worlds/first-world.sdf",
    ),
    (
        "02-gui-basics.md",
        "Gazebo GUI 기초",
        "gz sim examples/gazebo/worlds/first-world.sdf",
    ),
    (
        "03-sdf-basics.md",
        "SDF 기초",
        "gz sdf -k examples/gazebo/worlds/first-world.sdf",
    ),
    (
        "04-first-world.md",
        "첫 World 실행하기",
        "gz sim examples/gazebo/worlds/first-world.sdf",
    ),
)


def test_beginner_foundation_routes_h1s_and_commands_are_stable() -> None:
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    beginner_nav = next(item["초급"] for item in config["nav"] if "초급" in item)
    nav_paths = {next(iter(item.values())) for item in beginner_nav}

    for filename, heading, command in BEGINNER_PAGES:
        relative = f"beginner/{filename}"
        page = (ROOT / "docs" / relative).read_text(encoding="utf-8")
        assert relative in nav_paths
        assert page.splitlines()[0] == f"# {heading}"
        if command is not None:
            assert f"```bash\n{command}\n```" in page


def test_beginner_foundations_have_route_specific_learning_evidence() -> None:
    fragment = ROOT / "docs" / "assets" / "manifests" / "task-5.yaml"
    assert fragment.is_file()
    assets = yaml.safe_load(fragment.read_text(encoding="utf-8"))["assets"]
    assert {
        "beginner-01",
        "beginner-02",
        "beginner-03",
        "beginner-04",
    }.issubset({asset["id"] for asset in assets})

    for filename, _heading, command in BEGINNER_PAGES[1:]:
        page = (ROOT / "docs" / "beginner" / filename).read_text(encoding="utf-8")
        assert command is not None and command in page
        assert '<figure class="course-figure">' in page
        assert "alt=\"" in page
        assert "<figcaption>그림" in page
        assert "## 예상 관찰" in page
        assert "## 문제 해결" in page

    sdf_page = (ROOT / "docs" / "beginner" / "03-sdf-basics.md").read_text(encoding="utf-8")
    overview_page = (ROOT / "docs" / "beginner" / "01-gazebo-overview.md").read_text(encoding="utf-8")
    assert "x y z roll pitch yaw" in sdf_page
    assert "\\[" in sdf_page and "\\tag{" in sdf_page
    assert "RTF" in overview_page and "\\[" in overview_page
