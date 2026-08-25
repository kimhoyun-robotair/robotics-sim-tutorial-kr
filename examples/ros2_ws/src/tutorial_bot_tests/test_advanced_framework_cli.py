from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).parents[4]


def test_distance_scenario_rejects_missing_installed_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given: the checker is bound to an install root without Task 9 artifacts.
    evidence = tmp_path / "distance"
    monkeypatch.setenv("TUTORIAL_INSTALL_BASE", str(tmp_path / "missing-install"))

    # When: the distance scenario is invoked through its command-line surface.
    result = subprocess.run(
        [
            "bash",
            str(WORKSPACE_ROOT / "scripts/check_advanced_course.sh"),
            "--scenario",
            "distance",
            "--evidence",
            str(evidence),
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )

    # Then: stale or absent installs cannot be mistaken for live success.
    assert result.returncode == 64
    assert "installed diagnostics assets not found" in result.stderr
    assert "PASS" not in result.stdout
