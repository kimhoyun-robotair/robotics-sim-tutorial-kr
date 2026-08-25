from __future__ import annotations

import subprocess
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).parents[4]


def test_unimplemented_distance_scenario_is_bounded_and_explicit(tmp_path: Path) -> None:
    # Given: Task 9 distance behavior has not been implemented.
    evidence = tmp_path / "distance"

    # When: the common advanced checker is invoked for that future scenario.
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

    # Then: it cannot be mistaken for live success.
    assert result.returncode == 64
    assert "scenario unavailable" in result.stderr
    assert "PASS" not in result.stdout
