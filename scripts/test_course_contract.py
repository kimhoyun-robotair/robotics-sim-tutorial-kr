from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CourseContractTests(unittest.TestCase):
    def test_approve_review_rejects_high_finding(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/validate_structured_review.py",
                "--schema",
                "scripts/schemas/code-review.schema.json",
                "--input",
                "scripts/fixtures/reviews/approve-high.json",
                "--expect-verdict",
                "APPROVE",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("APPROVE requires zero findings", completed.stdout)

    def test_evidence_index_binds_task_to_full_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index = Path(temporary) / "index.json"
            output = Path(temporary) / "binding.json"
            commit = "20debfa7b0118598bcae6229b6b818e1dbbb6167"
            created = subprocess.run(
                [
                    sys.executable,
                    "scripts/create_evidence_index.py",
                    "--baseline-sha",
                    commit,
                    "--source-sha",
                    commit,
                    "--output",
                    str(index),
                ],
                cwd=ROOT,
                check=False,
            )
            bound = subprocess.run(
                [
                    sys.executable,
                    "scripts/audit_course_evidence.py",
                    "--evidence-index",
                    str(index),
                    "--bind-task-commit",
                    "1",
                    "--commit",
                    commit,
                    "--attempt-dir",
                    temporary,
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=False,
            )
            data = json.loads(index.read_text(encoding="utf-8"))
            self.assertEqual((created.returncode, bound.returncode), (0, 0))
            self.assertEqual(data["tasks"][0]["commit"], commit)

    def test_manifest_and_nav_resolve_exactly_31_unique_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "course.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_course_docs.py",
                    "--manifest",
                    "docs/course-manifest.yaml",
                    "--site-config",
                    "mkdocs.yml",
                    "--expect-routes",
                    "31",
                    "--evidence",
                    str(evidence),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(report["course_counts"], {"advanced": 7, "beginner": 12, "intermediate": 12})
            self.assertEqual(report["duplicate_routes"], [])
            self.assertEqual(report["unresolved_routes"], [])

    def test_duplicate_manifest_route_is_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_course_docs.py",
                    "--manifest",
                    "scripts/fixtures/course_docs/duplicate-route.yaml",
                    "--site-config",
                    "mkdocs.yml",
                    "--evidence",
                    str(Path(temporary) / "duplicate.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 64)

    def test_matrix_dispatches_selected_course_scenarios_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "matrix"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_course_matrix.py",
                    "--course",
                    "beginner,intermediate",
                    "--scenarios",
                    "diff-drive,launch",
                    "--modes",
                    "nominal,fault",
                    "--dry-run",
                    "--evidence",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((output / "matrix.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["dispatches"]), 4)
            self.assertEqual({item["course"] for item in report["dispatches"]}, {"beginner", "intermediate"})

    def test_evidence_auditor_rejects_stale_source_sha(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/audit_course_evidence.py",
                "--evidence-index",
                "scripts/fixtures/evidence/stale-sha/index.json",
                "--fixture",
                "scripts/fixtures/evidence/stale-sha",
                "--output",
                "/tmp/task-1-stale-sha.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("stale_sha", completed.stdout)


if __name__ == "__main__":
    unittest.main()
