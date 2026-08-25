from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_finalizer_binds_and_seals_immutable_inputs(tmp_path: Path) -> None:
    # Given: a live plan, ledger, and task index before final integration binding.
    plan = tmp_path / "plan.md"
    ledger = tmp_path / "ledger.jsonl"
    index = tmp_path / "index.json"
    output = tmp_path / "final-input"
    final_sha = "a" * 40
    source_tree = "b" * 40
    plan.write_text("# Final plan\n", encoding="utf-8")
    ledger.write_text('{"task":15,"status":"done"}\n', encoding="utf-8")
    index.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_sha": "c" * 40,
                "tasks": [{"task": 15, "commit": "c" * 40, "attempt_dir": "/evidence/task-15"}],
            }
        ),
        encoding="utf-8",
    )

    # When: the public finalizer binds the integrated source and creates the snapshot.
    completed = subprocess.run(
        (
            sys.executable,
            "scripts/finalize_course_evidence.py",
            "--plan",
            str(plan),
            "--ledger",
            str(ledger),
            "--index",
            str(index),
            "--output-dir",
            str(output),
            "--final-sha",
            final_sha,
            "--source-tree",
            source_tree,
        ),
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    # Then: live and snapshotted bindings match, hashes verify, and the snapshot is read-only.
    live_index = json.loads(index.read_text(encoding="utf-8"))
    snapshot_index = json.loads((output / "index.json").read_text(encoding="utf-8"))
    hashes = json.loads((output / "hashes.json").read_text(encoding="utf-8"))
    assert completed.returncode == 0
    assert live_index == snapshot_index
    assert snapshot_index["final_sha"] == final_sha
    assert snapshot_index["source_sha"] == final_sha
    assert snapshot_index["source_tree"] == source_tree
    assert snapshot_index["tasks"][-1]["commit"] == final_sha
    for name in ("plan.md", "ledger.jsonl", "index.json"):
        digest = hashlib.sha256((output / name).read_bytes()).hexdigest()
        assert hashes["artifacts"][name] == digest
        assert not (stat.S_IMODE((output / name).stat().st_mode) & 0o222)
    assert not (stat.S_IMODE(output.stat().st_mode) & 0o222)
