"""GPU 없이 검사할 수 있는 명령 경계, 재현성, 평가 판정, 출력 보존 규칙."""

import argparse
import importlib.util
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tutorial_common.runtime import output_directory, positive_float


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "src" / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


motion = load("motion", "01_mobile_robot_sandbox/motion.py")
command = load("command", "02_ros2_sensor_navigation/command.py")
randomization = load(
    "randomization", "04_robot_synthetic_data/core/robot_sdg/randomization.py"
)
metrics = load("metrics", "05_parallel_policy_evaluation/metrics.py")


class LearningLogicTests(unittest.TestCase):
    def test_square_turns_after_one_meter_and_repeats(self):
        self.assertEqual(motion.motion_command(9.9, "square", 0.1, 1.0), (0.1, 0.0))
        self.assertEqual(
            motion.motion_command(10.0, "square", 0.1, 1.0), (0.0, math.pi / 4)
        )
        self.assertEqual(motion.motion_command(12.0, "square", 0.1, 1.0), (0.1, 0.0))

    def test_watchdog_stops_and_new_command_resumes(self):
        state = command.VelocityCommand(timeout_s=0.5)
        self.assertEqual(state.current(10.0), (0.0, 0.0))
        state.receive(0.1, -0.2, now=10.0)
        self.assertEqual(state.current(10.4), (0.1, -0.2))
        self.assertEqual(state.current(10.6), (0.0, 0.0))
        state.receive(0.05, 0.0, now=11.0)
        self.assertEqual(state.current(11.1), (0.05, 0.0))

    def test_command_limits_and_nonfinite_input(self):
        state = command.VelocityCommand()
        state.receive(100.0, -100.0, 0.0)
        self.assertEqual(state.current(0.1), (0.2, -1.0))
        state.receive(math.nan, 0.0, 1.0)
        self.assertEqual(state.current(1.1), (0.0, 0.0))

    def test_seed_reproducibility_and_free_driving_corridor(self):
        first = randomization.sample_episode(7, 0)
        self.assertEqual(first, randomization.sample_episode(7, 0))
        self.assertNotEqual(first, randomization.sample_episode(7, 1))
        for seed in range(20):
            for box in randomization.sample_episode(seed, 0)["objects"]:
                self.assertGreaterEqual(abs(box["position"][1]), 0.45)
                self.assertEqual(len(box["color"]), 3)

    def test_fallen_robot_cannot_succeed_by_sliding(self):
        self.assertTrue(metrics.episode_success(0.6, 2.0, 0.3, False))
        self.assertFalse(metrics.episode_success(0.6, 2.0, 0.3, True))
        self.assertFalse(metrics.episode_success(0.01, 2.0, 0.3, False))
        self.assertAlmostEqual(metrics.upright([1, 0, 0, 0]), 1.0)
        self.assertAlmostEqual(metrics.upright([0, 1, 0, 0]), -1.0)
        self.assertEqual(metrics.upright([0, 0, 0, 0]), -1.0)

    def test_output_does_not_overwrite_an_experiment(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "experiment"
            output_directory("test", path)
            marker = path / "keep.txt"
            marker.write_text("keep")
            with self.assertRaises(FileExistsError):
                output_directory("test", path)
            self.assertEqual(marker.read_text(), "keep")

    def test_dt_rejects_zero_and_nonfinite_values(self):
        for value in ("0", "-1", "nan", "inf"):
            with self.assertRaises(argparse.ArgumentTypeError):
                positive_float(value)

    def test_standalone_help_does_not_start_kit(self):
        for path in (
            "01_mobile_robot_sandbox/run.py",
            "01_mobile_robot_sandbox/import_urdf.py",
            "02_ros2_sensor_navigation/run.py",
            "03_manipulator_pick_place/run.py",
            "04_robot_synthetic_data/standalone/generate.py",
            "05_parallel_policy_evaluation/evaluate.py",
        ):
            with self.subTest(path=path):
                result = subprocess.run(
                    [sys.executable, str(ROOT / "src" / path), "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--headless", result.stdout)


if __name__ == "__main__":
    unittest.main()
