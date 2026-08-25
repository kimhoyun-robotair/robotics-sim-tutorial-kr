from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_real_31_route_pedagogical_artifact_validates_all_approvals(tmp_path: Path) -> None:
    # Given: one complete approval record for every route in the real course manifest.
    manifest = yaml.safe_load((ROOT / "docs/course-manifest.yaml").read_text(encoding="utf-8"))
    routes = manifest["routes"]
    review = {
        "verdict": "APPROVE",
        "final_sha": "a" * 40,
        "route_reviews": [
            {
                "route": route["path"],
                "progression_clear": True,
                "korean_readable": True,
                "advanced_scope_safe": True,
                "copyright_safe_assets": True,
                "verdict": "APPROVE",
            }
            for route in routes
        ],
    }
    artifact = tmp_path / "pedagogy.json"
    artifact.write_text(json.dumps(review), encoding="utf-8")

    # When: the literal F4 validator command checks all route verdicts.
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/validate_structured_review.py",
            "--schema",
            "scripts/schemas/pedagogical-review.schema.json",
            "--input",
            str(artifact),
            "--expect-routes",
            "31",
            "--expect-all-verdicts",
            "APPROVE",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: the exact 31-route artifact is conclusively accepted.
    assert len(routes) == 31
    assert completed.returncode == 0, completed.stdout
    assert "structured review accepted" in completed.stdout
