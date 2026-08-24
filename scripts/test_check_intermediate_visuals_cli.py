from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_help_is_available_without_playwright() -> None:
    script = Path(__file__).with_name("check_intermediate_visuals.py")

    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--gazebo-title" in result.stdout
    assert result.stderr == ""
