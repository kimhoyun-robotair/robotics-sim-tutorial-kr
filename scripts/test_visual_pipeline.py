from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def run_cli(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_rendering_config_declares_math_mermaid_and_fixture() -> None:
    # Given: the repository rendering configuration and fixture page.
    config = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
    fixture = ROOT / "docs" / "06_reference" / "03_visual-fixture.md"

    # When: rendering features are inspected.
    extensions = config["markdown_extensions"]
    serialized = json.dumps(extensions, ensure_ascii=False)
    scripts = config["extra_javascript"]

    # Then: all four reproducible visual primitives are configured.
    assert "pymdownx.arithmatex" in serialized
    assert any("mermaid" in script for script in scripts)
    assert any("mathjax" in script for script in scripts)
    text = fixture.read_text(encoding="utf-8")
    assert "\\tag{1}" in text
    assert 'class="course-mermaid"' in text
    assert 'alt="좌표계에서 로봇의 이동 방향을 보여 주는 재현 가능한 도식"' in text
    assert "그림 1." in text


def test_capture_rejects_unapproved_command_with_cleanup_receipt() -> None:
    # Given: a manifest containing a shell command outside the capture allowlist.
    with tempfile.TemporaryDirectory() as temporary:
        evidence = Path(temporary) / "evidence"

        # When: fixture capture is attempted.
        result = run_cli(
            "capture_course_visuals.py",
            "--manifest",
            "scripts/fixtures/assets/invalid-command.yaml",
            "--only",
            "fixture",
            "--evidence",
            str(evidence),
        )

        # Then: input is rejected and cleanup still proves no survivors.
        assert result.returncode == 64
        receipt = json.loads((evidence / "cleanup.json").read_text(encoding="utf-8"))
        assert receipt["survivors"] == []
        assert receipt["status"] == "invalid"


def test_capture_forced_failure_cleans_owned_processes() -> None:
    # Given: an approved capture command that fails after spawning a sentinel.
    with tempfile.TemporaryDirectory() as temporary:
        evidence = Path(temporary) / "evidence"

        # When: fixture capture is forced to fail.
        result = run_cli(
            "capture_course_visuals.py",
            "--manifest",
            "scripts/fixtures/assets/forced-failure.yaml",
            "--only",
            "fixture",
            "--evidence",
            str(evidence),
        )

        # Then: the failure is distinct and the Task-1 wrapper reaps everything.
        assert result.returncode == 1
        receipt = json.loads((evidence / "fixture" / "cleanup.json").read_text(encoding="utf-8"))
        assert receipt["dut_exit"] == 1
        assert receipt["sentinel_survived_dut_teardown"] is True
        assert receipt["sentinel_reaped"] is True
        assert receipt["survivors"] == []


def test_capture_propagates_cleanup_identity_failure() -> None:
    # Given: an approved capture whose registered sentinel identity is stale.
    with tempfile.TemporaryDirectory() as temporary:
        evidence = Path(temporary) / "evidence"

        # When: capture observes Task-1 cleanup failure exit 70.
        result = run_cli(
            "capture_course_visuals.py",
            "--manifest",
            "scripts/fixtures/assets/cleanup-failure.yaml",
            "--only",
            "fixture",
            "--evidence",
            str(evidence),
        )

        # Then: cleanup failure cannot be reported as capture success.
        assert result.returncode == 1
        receipt = json.loads((evidence / "fixture" / "cleanup.json").read_text(encoding="utf-8"))
        assert receipt["dut_exit"] == 70
        assert receipt["stale_identity"] is True
        assert receipt["survivors"] == []


def test_asset_checker_rejects_missing_alt_and_leaked_home_path() -> None:
    # Given: manifests with absent accessibility metadata and private paths.
    with tempfile.TemporaryDirectory() as temporary:
        evidence = Path(temporary)

        # When: each invalid manifest is audited.
        missing_alt = run_cli(
            "check_course_assets.py",
            "--manifest",
            "scripts/fixtures/assets/missing-alt.yaml",
            "--evidence",
            str(evidence / "missing-alt.json"),
        )
        leaked_path = run_cli(
            "check_course_assets.py",
            "--manifest",
            "scripts/fixtures/assets/leaked-home.yaml",
            "--evidence",
            str(evidence / "leaked-home.json"),
        )

        # Then: both semantic defects fail independently.
        assert missing_alt.returncode == 1
        assert leaked_path.returncode == 1
        assert "alt_text" in missing_alt.stdout
        assert "absolute home path" in leaked_path.stdout


def test_asset_checker_rejects_unregistered_asset() -> None:
    # Given: an asset tree with a visual absent from its manifest.
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        assets = root / "assets"
        assets.mkdir()
        (assets / "orphan.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
        manifest = root / "manifest.yaml"
        manifest.write_text("schema_version: 1\nassets: []\n", encoding="utf-8")

        # When: the isolated asset tree is checked.
        result = run_cli(
            "check_course_assets.py",
            "--manifest",
            str(manifest),
            "--assets-root",
            str(assets),
            "--evidence",
            str(root / "report.json"),
        )

        # Then: the orphan is rejected without a pixel-size heuristic.
        assert result.returncode == 1
        assert "unregistered asset" in result.stdout


def test_asset_checker_rejects_stale_generated_asset() -> None:
    # Given: a registered visual whose content no longer matches its capture digest.
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        assets = root / "assets"
        assets.mkdir()
        (assets / "fixture.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
        manifest = root / "manifest.yaml"
        manifest.write_text(
            "\n".join(
                (
                    "schema_version: 1",
                    "assets:",
                    "  - id: fixture",
                    "    path: assets/fixture.svg",
                    "    route: 06_reference/03_visual-fixture/",
                    "    source_command: python3 scripts/render_fixture_visual.py --output docs/assets/fixture.svg",
                    "    semantic_observable: 도식이 보인다.",
                    "    alt_text: 재현 가능한 도식",
                    "    caption: 그림 1",
                    "    captured_at: '2026-08-25'",
                    f"    sha256: '{'0' * 64}'",
                    "",
                )
            ),
            encoding="utf-8",
        )

        # When: the asset is checked after its content changed.
        result = run_cli(
            "check_course_assets.py",
            "--manifest",
            str(manifest),
            "--assets-root",
            str(assets),
            "--evidence",
            str(root / "report.json"),
        )

        # Then: stale content cannot be reported as a successful capture.
        assert result.returncode == 1
        assert "stale generated asset" in result.stdout


def test_asset_checker_merges_task_fragment_with_base_manifest(tmp_path: Path) -> None:
    # Given: the global visual manifest and the latest cumulative course fragment.
    evidence = tmp_path / "assets.json"

    # When: the latest fragment is audited against the real documentation asset tree.
    result = run_cli(
        "check_course_assets.py",
        "--manifest",
        "docs/assets/manifest.yaml",
        "--fragments",
        "docs/assets/manifests/task-13.yaml",
        "--evidence",
        str(evidence),
    )

    # Then: fragment assets participate in duplicate and orphan detection.
    assert result.returncode == 0, result.stdout
    report = json.loads(evidence.read_text(encoding="utf-8"))
    assert {asset["id"] for asset in report["assets"]} == {
        "fixture",
        "beginner-index",
        "beginner-01",
        "beginner-02",
        "beginner-03",
        "beginner-04",
        "beginner-05-format-flow",
        "beginner-06-joint-axis",
        "beginner-07-diff-drive-trajectories",
        "beginner-08-sensor-observables",
        "beginner-09-fuel-resource-flow",
        "beginner-10-bridge-dataflow",
        "beginner-project-final-observable",
        "course-dataflow",
        "inertia-contact",
        "model-conversion",
        "launch-readiness",
        "spawn-pose",
        "bridge-qos",
        "tf-composition",
        "controller-kinematics",
        "sensor-statistics",
        "namespace-isolation",
        "nav2-tolerance",
        "project-runtime",
        "advanced-course-architecture",
        "advanced-ecs-lifecycle",
        "advanced-transport-boundary",
        "advanced-sim-time",
        "advanced-headless-taxonomy",
        "advanced-ci-reproducibility",
        "advanced-production-stack",
    }
