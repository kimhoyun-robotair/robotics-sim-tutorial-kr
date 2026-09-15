"""Exercise tutorial CLI and lifetime code with SDK boundaries replaced by fakes.

These tests verify Python control flow, cleanup and saved counters. They do not
claim that a real Kit window, renderer or physics engine ran.
"""
import contextlib
import asyncio
from collections.abc import Callable
import io
import json
import runpy
import sys
import tempfile
import types
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch


SRC = Path(__file__).resolve().parents[1] / "src"
LESSONS = (
    ("01_core_core_hello_world", 300),
    ("06_python_usd_manual_standalone_python", 120),
    ("18_sensors_simulation_fundamentals", 240),
    ("92_tools_advanced_python_debugging", 240),
)


class SDKFailure(RuntimeError):
    pass


class Vector(list[float]):
    def tolist(self):
        return list(self)


@dataclass
class SDKState:
    close_after: int = 1001
    use_world: bool = True
    fail_at: int | None = None
    physics_steps: int = 0
    app_updates: int = 0
    close_calls: int = 0
    user_closed: bool = False
    config: dict[str, object] = field(default_factory=dict)
    renders: list[bool] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    callbacks: dict[str, Callable[[float], None]] = field(default_factory=dict)
    on_update: Callable[[], None] | None = None

    @property
    def ticks(self):
        return self.physics_steps if self.use_world else self.app_updates

    def guard_tick(self):
        if self.ticks >= 5000 or self.app_updates >= 5000:
            raise AssertionError("Tutorial ignored user-close or explicit step limit")
        if self.fail_at is not None and self.ticks + 1 == self.fail_at:
            raise SDKFailure("Injected SDK update failure")


def fake_sdk(state):
    """Model only external SDK calls; production parsers and loops run unchanged."""
    modules = {}

    def module(name, **exports):
        if name in modules:
            result = modules[name]
        else:
            result = modules[name] = types.ModuleType(name)
            if "." in name:
                parent, child = name.rsplit(".", 1)
                setattr(module(parent), child, result)
        result.__dict__.update(exports)
        return result

    class App:
        def __init__(self, config):
            state.config = config

        def is_running(self):
            if state.ticks >= state.close_after:
                state.user_closed = True
                return False
            return True

        def update(self):
            state.guard_tick()
            state.app_updates += 1
            if state.on_update is not None:
                state.on_update()

        def close(self):
            state.close_calls += 1

    class Cube:
        def __init__(self, *args, **kwargs):
            self.position = kwargs.get("position", Vector([0, 0, 1]))
            self.prim = object()

        def get_world_pose(self):
            return self.position, Vector([1, 0, 0, 0])

        def get_linear_velocity(self):
            return Vector([0, 0, 0])

    class Scene:
        def add_default_ground_plane(self):
            pass

        def add(self, obj):
            return obj

    class World:
        current = None

        def __init__(self, **kwargs):
            World.current = self
            self.scene = Scene()
            self.current_time = 0.0
            self.dt = kwargs["physics_dt"]

        @classmethod
        def instance(cls):
            return cls.current

        def reset(self):
            pass

        def add_physics_callback(self, name, callback_fn):
            state.callbacks[name] = callback_fn

        def remove_physics_callback(self, name):
            del state.callbacks[name]

        def step(self, *, render):
            state.guard_tick()
            state.physics_steps += 1
            state.renders.append(render)
            self.current_time += self.dt
            for callback in state.callbacks.values():
                callback(self.dt)

    class Layer:
        def Export(self, path):
            state.exports.append(path)
            Path(path).write_text("#usda 1.0\n", encoding="utf-8")
            return True

    stage = types.SimpleNamespace(GetRootLayer=lambda: Layer())
    context = types.SimpleNamespace(get_stage=lambda: stage, open_stage=lambda _: True)

    class DebugCube:
        @classmethod
        def Define(cls, stage, path):
            return cls()

        def CreateSizeAttr(self, size):
            pass

        def AddTranslateOp(self):
            return types.SimpleNamespace(Set=lambda position: None)

    module("numpy", array=Vector)
    module("isaacsim", SimulationApp=App)
    module("isaacsim.core.api", World=World)
    module("isaacsim.core.api.objects", DynamicCuboid=Cube, FixedCuboid=Cube, VisualCuboid=Cube)
    module("isaacsim.core.utils.extensions", enable_extension=lambda _: None)
    module("omni.usd", get_context=lambda: context)
    module("pxr.Gf", Vec3d=lambda *values: values)
    module("pxr.UsdGeom", Cube=DebugCube)
    module("pxr.UsdLux", DomeLight=types.SimpleNamespace(
        Define=lambda stage, path: types.SimpleNamespace(CreateIntensityAttr=lambda value: None)))
    module("pxr.UsdPhysics", CollisionAPI=lambda prim: types.SimpleNamespace(
        GetCollisionEnabledAttr=lambda: types.SimpleNamespace(Set=lambda value: None)))
    module("pxr.PhysxSchema")
    return modules


class TutorialLifetimeTests(unittest.TestCase):
    def execute(self, package, state, arguments=()):
        script = SRC / package / "run.py"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            argv = [str(script), *arguments]
            if package != "92_tools_advanced_python_debugging":
                argv.extend(["--output", str(output)])
            with (
                patch.dict(sys.modules, fake_sdk(state)),
                patch.object(sys, "argv", argv),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                runpy.run_path(str(script), run_name="__main__")
            artifacts = {
                path.name: path.read_text(encoding="utf-8")
                for path in output.glob("*") if path.is_file()
            }
        return artifacts

    def assert_saved_steps(self, package, artifacts, steps):
        if package == "01_core_core_hello_world":
            self.assertEqual(json.loads(artifacts["result.json"])["samples"], steps)
            self.assertEqual(len(artifacts["fall.csv"].splitlines()), steps + 1)
        elif package == "06_python_usd_manual_standalone_python":
            self.assertEqual(json.loads(artifacts["environment.json"])["physics_callbacks"], steps)

    def test_default_gui_runs_past_old_limit_until_user_close(self):
        for package, old_limit in LESSONS:
            with self.subTest(package=package):
                state = SDKState(use_world=not package.startswith("92_"))
                artifacts = self.execute(package, state)
                self.assertGreater(state.ticks, old_limit)
                self.assertEqual(state.ticks, state.close_after)
                self.assertTrue(state.user_closed)
                self.assertFalse(state.config["headless"])
                self.assertEqual(state.close_calls, 1)
                self.assert_saved_steps(package, artifacts, state.close_after)
                if package.startswith("18_"):
                    self.assertEqual(len(json.loads(artifacts["fall.json"])), 240)

    def test_explicit_steps_exit_after_requested_count(self):
        for package, _ in LESSONS:
            with self.subTest(package=package):
                state = SDKState(use_world=not package.startswith("92_"))
                artifacts = self.execute(package, state, ["--steps", "7"])
                self.assertEqual(state.ticks, 7)
                self.assertFalse(state.user_closed)
                self.assertEqual(state.close_calls, 1)
                self.assert_saved_steps(package, artifacts, 7)

    def test_user_close_interrupts_even_an_explicit_budget(self):
        for package, _ in LESSONS:
            with self.subTest(package=package):
                state = SDKState(close_after=3, use_world=not package.startswith("92_"))
                self.execute(package, state, ["--steps", "7"])
                self.assertEqual(state.ticks, 3)
                self.assertTrue(state.user_closed)
                self.assertEqual(state.close_calls, 1)

    def test_omitted_headless_steps_preserve_finite_default(self):
        for package, old_limit in LESSONS:
            with self.subTest(package=package):
                state = SDKState(use_world=not package.startswith("92_"))
                artifacts = self.execute(package, state, ["--headless"])
                self.assertEqual(state.ticks, old_limit)
                self.assertTrue(state.config["headless"])
                self.assertFalse(state.user_closed)
                self.assertEqual(state.close_calls, 1)
                self.assert_saved_steps(package, artifacts, old_limit)

    def test_sdk_failure_closes_app_and_propagates_without_gui_hold(self):
        for package, _ in LESSONS:
            with self.subTest(package=package):
                state = SDKState(fail_at=3, use_world=not package.startswith("92_"))
                with self.assertRaisesRegex(SDKFailure, "Injected SDK update failure"):
                    self.execute(package, state)
                self.assertEqual(state.ticks, 2)
                self.assertFalse(state.user_closed)
                self.assertEqual(state.close_calls, 1)
                setup_updates = 1 if package.startswith("06_") else 0
                self.assertEqual(state.app_updates, setup_updates if state.use_world else 2)

    def test_negative_steps_rejected_before_app_creation(self):
        for package, _ in LESSONS:
            with self.subTest(package=package):
                state = SDKState(use_world=not package.startswith("92_"))
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    self.execute(package, state, ["--steps", "-1"])
                self.assertEqual(error.exception.code, 2)
                self.assertEqual(state.config, {})
                self.assertEqual(state.close_calls, 0)

    def test_explicit_steps_override_legacy_interactive_flag(self):
        state = SDKState()
        artifacts = self.execute(
            "18_sensors_simulation_fundamentals", state,
            ["--interactive", "--steps", "7"],
        )
        self.assertEqual(state.physics_steps, 7)
        self.assertEqual(len(json.loads(artifacts["fall.json"])), 7)
        self.assertFalse(state.user_closed)
        self.assertEqual(state.close_calls, 1)


class ConverterLifetimeTests(unittest.TestCase):
    conversion_cancelled = False

    def execute(self, state, *, conversion="success", arguments=()):
        script = SRC / "16_python_usd_environment_setup" / "convert.py"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        state.on_update = lambda: loop.run_until_complete(asyncio.sleep(0))
        self.conversion_cancelled = False
        try:
            with tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "converted.usda"

                async def finish():
                    if conversion == "pending":
                        try:
                            await loop.create_future()
                        except asyncio.CancelledError:
                            self.conversion_cancelled = True
                            raise
                    if conversion == "failure":
                        return False
                    output.write_text("#usda 1.0\n", encoding="utf-8")
                    return True

                job = types.SimpleNamespace(
                    wait_until_finished=finish,
                    get_detailed_error=lambda: "Converter rejected input mesh",
                )
                modules = fake_sdk(state)
                converter = types.ModuleType("omni.kit.asset_converter")
                setattr(converter, "AssetConverterContext", types.SimpleNamespace)
                setattr(converter, "get_instance", lambda: types.SimpleNamespace(
                    create_converter_task=lambda *args: job))
                kit = types.ModuleType("omni.kit")
                setattr(kit, "asset_converter", converter)
                modules["omni"].kit = kit
                modules.update({"omni.kit": kit, "omni.kit.asset_converter": converter})
                with (
                    patch.dict(sys.modules, modules),
                    patch.object(sys, "argv", [str(script), "--output", str(output), *arguments]),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    runpy.run_path(str(script), run_name="__main__")
                return output.is_file()
        finally:
            loop.run_until_complete(asyncio.sleep(0))
            for task in asyncio.all_tasks(loop):
                task.cancel()
            loop.run_until_complete(asyncio.sleep(0))
            loop.close()
            asyncio.set_event_loop(None)

    def test_completed_conversion_keeps_default_gui_alive(self):
        state = SDKState(close_after=12, use_world=False)
        self.assertTrue(self.execute(state))
        self.assertEqual(state.app_updates, 12)
        self.assertTrue(state.user_closed)
        self.assertEqual(state.close_calls, 1)

    def test_explicit_steps_skip_post_conversion_gui_hold(self):
        state = SDKState(close_after=12, use_world=False)
        self.assertTrue(self.execute(state, arguments=["--steps", "7"]))
        self.assertLessEqual(state.app_updates, 7)
        self.assertFalse(state.user_closed)
        self.assertEqual(state.close_calls, 1)

    def test_close_during_pending_conversion_cancels_without_timeout(self):
        state = SDKState(close_after=4, use_world=False)
        self.assertFalse(self.execute(state, conversion="pending"))
        self.assertEqual(state.app_updates, 4)
        self.assertTrue(state.user_closed)
        self.assertTrue(self.conversion_cancelled)
        self.assertEqual(state.close_calls, 1)

    def test_converter_error_propagates_without_gui_hold(self):
        state = SDKState(close_after=12, use_world=False)
        with self.assertRaisesRegex(RuntimeError, "Converter rejected input mesh"):
            self.execute(state, conversion="failure")
        self.assertLess(state.app_updates, 12)
        self.assertFalse(state.user_closed)
        self.assertEqual(state.close_calls, 1)

    def test_explicit_budget_still_times_out_pending_conversion(self):
        state = SDKState(close_after=12, use_world=False)
        with self.assertRaises(TimeoutError):
            self.execute(state, conversion="pending", arguments=["--steps", "3"])
        self.assertEqual(state.app_updates, 4)  # One extension setup update, then the three-step budget.
        self.assertTrue(self.conversion_cancelled)
        self.assertFalse(state.user_closed)
        self.assertEqual(state.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
