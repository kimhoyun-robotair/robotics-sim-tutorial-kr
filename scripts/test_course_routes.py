from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from scripts.check_course_routes import load_assets

ROOT = Path(__file__).resolve().parents[1]


def validate_fixture(name: str, evidence: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "check_course_routes.py"),
            "--records",
            str(ROOT / "scripts" / "fixtures" / "routes" / name),
            "--schema",
            str(ROOT / "scripts" / "schemas" / "route-qa.schema.json"),
            "--evidence",
            str(evidence),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_route_schema_accepts_complete_true_record() -> None:
    # Given: one complete route record with every required boolean true.
    with tempfile.TemporaryDirectory() as temporary:
        # When: the record is validated.
        result = validate_fixture("valid.json", Path(temporary) / "valid.json")

        # Then: schema and uniqueness checks pass.
        assert result.returncode == 0


def test_route_schema_rejects_missing_route_record() -> None:
    # Given: an empty route-record collection.
    with tempfile.TemporaryDirectory() as temporary:
        # When: the collection is validated.
        result = validate_fixture("missing.json", Path(temporary) / "missing.json")

        # Then: the required record is rejected.
        assert result.returncode == 64


def test_route_schema_rejects_duplicate_route_record() -> None:
    # Given: two records for the same route with different visual IDs.
    with tempfile.TemporaryDirectory() as temporary:
        # When: the collection is validated.
        result = validate_fixture("duplicate.json", Path(temporary) / "duplicate.json")

        # Then: semantic route uniqueness is enforced.
        assert result.returncode == 64
        assert "duplicate route" in result.stdout


def test_route_schema_rejects_false_required_boolean() -> None:
    # Given: a structurally complete record whose network result is false.
    with tempfile.TemporaryDirectory() as temporary:
        # When: the record is validated.
        result = validate_fixture("false-boolean.json", Path(temporary) / "false.json")

        # Then: false cannot masquerade as a schema-valid pass.
        assert result.returncode == 64


def test_asset_loader_includes_task_manifest_fragments() -> None:
    # Given: a base manifest and an independently owned task fragment.
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        fragments = root / "manifests"
        fragments.mkdir()
        record = {
            "id": "route-visual",
            "path": "assets/intermediate/route.svg",
            "route": "intermediate/route/",
            "source_command": "repository-authored SVG",
            "semantic_observable": "고유 구조가 보인다.",
            "alt_text": "고유 구조도",
            "caption": "그림 1. 고유 구조도",
            "sha256": "0" * 64,
        }
        (root / "manifest.yaml").write_text(
            yaml.safe_dump({"schema_version": 1, "assets": []}, allow_unicode=True),
            encoding="utf-8",
        )
        (fragments / "task-8.yaml").write_text(
            yaml.safe_dump(
                {"schema_version": 1, "assets": [record]}, allow_unicode=True
            ),
            encoding="utf-8",
        )

        # When: the default manifest is loaded.
        assets = load_assets(root / "manifest.yaml")

        # Then: the task-owned route record participates in browser QA.
        assert [asset.asset_id for asset in assets] == ["route-visual"]


def test_missing_browser_has_dedicated_exit_code() -> None:
    # Given: a built fixture route and an explicitly empty browser path.
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        site = root / "site" / "reference" / "visual-fixture"
        site.mkdir(parents=True)
        (site / "index.html").write_text("<h1>fixture</h1>", encoding="utf-8")
        environment = {
            "PATH": str(Path(sys.executable).parent),
            "PLAYWRIGHT_BROWSERS_PATH": str(root / "missing"),
        }

        # When: a real-browser route audit is requested without Chromium.
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "check_course_routes.py"),
                "--site-dir",
                str(root / "site"),
                "--asset-manifest",
                str(ROOT / "docs" / "assets" / "manifest.yaml"),
                "--course",
                "fixture",
                "--expect-routes",
                "1",
                "--evidence",
                str(root / "report.json"),
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

        # Then: missing browser is not conflated with a route assertion.
        assert result.returncode == 22
        report = json.loads((root / "report.json").read_text(encoding="utf-8"))
        assert report["status"] == "browser_missing"
