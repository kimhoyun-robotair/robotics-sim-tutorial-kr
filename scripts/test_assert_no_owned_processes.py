from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "assert_no_owned_processes.py"


def run_checker(evidence: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CHECKER),
            "--evidence-root",
            str(evidence),
            "--require-sentinels-reaped",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def write_receipt(path: Path, **overrides: object) -> None:
    value: dict[str, object] = {
        "schema_version": 1,
        "survivors": [],
        "sentinel_survived_dut_teardown": False,
        "sentinel_reaped": False,
        **overrides,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def test_checker_accepts_clean_receipts_and_reaped_registered_sentinel(
    tmp_path: Path,
) -> None:
    # Given: clean wrapper receipts for both absent and registered sentinels.
    write_receipt(tmp_path / "first-cleanup.json")
    write_receipt(
        tmp_path / "nested" / "cleanup.json",
        sentinel_survived_dut_teardown=True,
        sentinel_reaped=True,
    )

    # When: the final owned-process assertion scans the evidence tree.
    result = run_checker(tmp_path)

    # Then: both receipts are accepted without starting or signaling processes.
    assert result.returncode == 0
    assert '"status": "pass"' in result.stdout
    assert '"receipts": 2' in result.stdout


def test_checker_rejects_malformed_receipt(tmp_path: Path) -> None:
    # Given: a cleanup receipt that is not valid JSON.
    (tmp_path / "cleanup.json").write_text("{", encoding="utf-8")

    # When: the final assertion scans it.
    result = run_checker(tmp_path)

    # Then: the failure names the malformed receipt and remains nonzero.
    assert result.returncode != 0
    assert "malformed cleanup receipt" in result.stdout
    assert "cleanup.json" in result.stdout


def test_checker_rejects_owned_survivor(tmp_path: Path) -> None:
    # Given: a cleanup receipt containing one owned survivor.
    write_receipt(tmp_path / "cleanup.json", survivors=[424242])

    # When: the final assertion scans it.
    result = run_checker(tmp_path)

    # Then: the survivor PID is actionable and the check fails.
    assert result.returncode != 0
    assert "owned survivors: 424242" in result.stdout


def test_checker_rejects_unreaped_registered_sentinel(tmp_path: Path) -> None:
    # Given: a registered sentinel survived DUT teardown but was not reaped.
    write_receipt(
        tmp_path / "cleanup.json",
        sentinel_survived_dut_teardown=True,
        sentinel_reaped=False,
    )

    # When: sentinel reaping is required.
    result = run_checker(tmp_path)

    # Then: the exact unreaped condition is reported and rejected.
    assert result.returncode != 0
    assert "registered sentinel was not reaped" in result.stdout


def test_checker_rejects_evidence_without_cleanup_receipts(tmp_path: Path) -> None:
    # Given: an evidence root containing no cleanup receipt.
    (tmp_path / "result.json").write_text("{}\n", encoding="utf-8")

    # When: the final assertion scans it.
    result = run_checker(tmp_path)

    # Then: missing cleanup evidence is actionable and rejected.
    assert result.returncode != 0
    assert "no cleanup receipts found" in result.stdout
