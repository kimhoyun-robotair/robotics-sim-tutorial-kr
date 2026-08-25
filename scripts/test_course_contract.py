from __future__ import annotations

import importlib.util
import json
import os
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
            self.assertEqual(
                report["course_counts"],
                {"advanced": 7, "beginner": 12, "intermediate": 12},
            )
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

    def test_forbidden_advanced_scope_fixture_names_every_forbidden_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary) / "forbidden.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_course_docs.py",
                    "--manifest",
                    "scripts/fixtures/course_docs/forbidden-advanced-scope.yaml",
                    "--site-config",
                    "mkdocs.yml",
                    "--expect-routes",
                    "31",
                    "--forbid-advanced-scope",
                    "custom_ros2_control,custom_nav2,slam",
                    "--evidence",
                    str(evidence),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            report = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(completed.returncode, 64)
            self.assertEqual(report["route_count"], 31)
            for token in ("custom_ros2_control", "custom_nav2", "slam"):
                self.assertIn(f"forbidden advanced scope: {token}", report["errors"])

    def test_course_docs_rejects_manifest_asset_that_does_not_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/check_course_docs.py",
                    "--manifest",
                    "scripts/fixtures/course_docs/intermediate-broken-asset.yaml",
                    "--site-config",
                    "mkdocs.yml",
                    "--evidence",
                    str(Path(temporary) / "broken-asset.json"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 64)
            self.assertIn("missing-intermediate-architecture.svg", completed.stdout)

    def test_matrix_dispatches_selected_course_scenarios_without_execution(
        self,
    ) -> None:
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
            self.assertEqual(
                {item["course"] for item in report["dispatches"]},
                {"beginner", "intermediate"},
            )

    def test_intermediate_matrix_uses_specific_fault_contracts_and_one_shared_build(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "matrix"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_course_matrix.py",
                    "--course",
                    "intermediate",
                    "--scenarios",
                    "launch,sensors,control_tf,multi_robot,nav2",
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
            report = json.loads((output / "matrix.json").read_text(encoding="utf-8"))
            commands = {
                (item["scenario"], item["mode"]): item["command"]
                for item in report["dispatches"]
            }

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(report["shared_build"]["count"], 1)
            self.assertEqual(
                commands[("launch", "fault")][-3:],
                ["--world", "missing-world", "--expect-failure"],
            )
            self.assertEqual(
                commands[("sensors", "fault")][-2:],
                ["--expected-width", "1"],
            )
            self.assertEqual(
                commands[("control_tf", "fault")][-2:],
                ["--expect-missing-frame", "missing_link"],
            )
            self.assertEqual(
                commands[("multi_robot", "fault")][-2:],
                ["--robot2-name", "robot1"],
            )
            self.assertEqual(
                commands[("nav2", "fault")][-4:],
                ["--goal-name", "unreachable_goal.yaml", "--expect-status", "6"],
            )
            self.assertNotIn("--expect-failure", commands[("sensors", "fault")])
            self.assertTrue(
                all(item["observable_contract"] for item in report["dispatches"])
            )

    def test_full_intermediate_matrix_has_a_270_second_timing_budget(self) -> None:
        from scripts.run_course_matrix import timing_budget

        scenarios = {"launch", "sensors", "control_tf", "multi_robot", "nav2"}

        self.assertEqual(
            timing_budget(
                {"intermediate"}, scenarios, {"nominal", "fault"}, execute=True
            ),
            270.0,
        )
        self.assertIsNone(
            timing_budget(
                {"intermediate"}, scenarios - {"nav2"}, {"nominal", "fault"}, True
            )
        )

    def test_intermediate_checkers_reject_missing_install_through_public_cli(
        self,
    ) -> None:
        checkers = (
            "check_intermediate_launch.sh",
            "check_intermediate_sensors.sh",
            "check_intermediate_control_tf.sh",
            "check_intermediate_multi_robot.sh",
            "check_intermediate_nav2.sh",
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            environment = {
                **os.environ,
                "TUTORIAL_INSTALL_BASE": str(root / "missing-install"),
            }
            for checker in checkers:
                completed = subprocess.run(
                    (
                        "bash",
                        str(ROOT / "scripts" / checker),
                        "--evidence",
                        str(root / checker),
                    ),
                    env=environment,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=10,
                )
                self.assertNotEqual(completed.returncode, 0, checker)

    def test_localization_transition_recovers_after_delayed_service_response(
        self,
    ) -> None:
        transition_module = (
            ROOT
            / "examples/ros2_ws/src/tutorial_bot_bringup/scripts/localization_transition.py"
        )
        spec = importlib.util.spec_from_file_location(
            "localization_transition_test", transition_module
        )
        if spec is None or spec.loader is None:
            self.fail("localization transition module could not be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class DelayedBoundary:
            def __init__(self) -> None:
                self.state = 1
                self.requests = 0
                self.elapsed = 0.0

            def current_state(self, _: str) -> int:
                return self.state

            def request_transition(self, _: str, transition_id: int) -> None:
                self.requests += 1
                self.state = {1: 2, 3: 3}[transition_id]

            def idle(self, seconds: float) -> None:
                self.elapsed += seconds

        boundary = DelayedBoundary()
        reached = module.reach_state(
            boundary,
            "map_server",
            1,
            2,
            10.0,
            clock=lambda: boundary.elapsed,
        )
        self.assertTrue(reached)
        self.assertEqual(boundary.requests, 1)
        self.assertEqual(boundary.state, 2)

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
