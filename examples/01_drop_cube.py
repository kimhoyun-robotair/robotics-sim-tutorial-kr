#!/usr/bin/env python3
"""Isaac Sim 6.0.1: an asset-free PhysX drop experiment with measured checks.

Run with Isaac Sim's python.sh, not the system Python. --help needs no simulator.
The JSON records this particular run; source review is not a GPU runtime test.
"""

import argparse
import json
import math
from pathlib import Path
import sys
import time
import traceback


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Do not open an application window")
    parser.add_argument("--output", type=Path, default=Path("artifacts/drop_cube.json"))
    parser.add_argument("--physics-hz", type=int, choices=(60, 120, 240), default=120)
    parser.add_argument("--steps", type=int, default=600, help="Number of physics samples, at least two seconds")
    parser.add_argument("--timeout", type=float, default=180.0, help="Wall-clock timeout after scene creation")
    args = parser.parse_args()
    if args.steps < 2 * args.physics_hz or args.steps > 100000:
        parser.error("--steps must cover at least two simulation seconds and be <= 100000")
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be a finite positive number")
    return args


def run_experiment(args, report):
    # Import Kit-dependent modules only after SimulationApp exists.
    import carb
    import numpy as np
    import omni.timeline
    import omni.usd
    from isaacsim.core.experimental.prims import RigidPrim
    from isaacsim.core.simulation_manager import PhysxScene, SimulationEvent, SimulationManager
    from pxr import Gf, PhysxSchema, UsdGeom, UsdLux, UsdPhysics, UsdShade

    app = report.pop("_app")
    context = omni.usd.get_context()
    context.new_stage()
    stage = context.get_stage()
    if stage is None:
        raise RuntimeError("A USD stage was not created")
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    stage.SetTimeCodesPerSecond(60.0)
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    if SimulationManager.get_active_physics_engine() != "physx":
        if not SimulationManager.switch_physics_engine("physx"):
            raise RuntimeError("The PhysX physics engine could not be enabled")
    SimulationManager.set_device("cpu")
    physics = PhysxScene("/World/PhysicsScene")
    physics.set_gravity((0.0, 0.0, -9.81))
    physics.set_steps_per_second(args.physics_hz)
    physics.set_enabled_gpu_dynamics(False)
    physics.set_broadphase_type("MBP")
    physics.set_solver_type("TGS")
    physics.set_enabled_ccd(True)
    physics.set_enabled_stabilization(True)
    carb.settings.get_settings().set_bool("/app/player/useFixedTimeStepping", True)

    material = UsdShade.Material.Define(stage, "/World/ContactMaterial")
    contact = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    contact.CreateStaticFrictionAttr(0.8)
    contact.CreateDynamicFrictionAttr(0.6)
    contact.CreateRestitutionAttr(0.0)

    def make_box(path, size, position, color, scale=None):
        box = UsdGeom.Cube.Define(stage, path)
        box.CreateSizeAttr(size)
        box.AddTranslateOp().Set(Gf.Vec3d(*position))
        if scale is not None:
            box.AddScaleOp().Set(Gf.Vec3f(*scale))
        box.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        UsdPhysics.CollisionAPI.Apply(box.GetPrim())
        UsdShade.MaterialBindingAPI.Apply(box.GetPrim()).Bind(material, materialPurpose="physics")
        return box

    # A thick static floor: top surface is exactly z = 0 m.
    make_box("/World/Floor", 1.0, (0.0, 0.0, -0.1), (0.25, 0.25, 0.25), (10.0, 10.0, 0.2))
    shape = make_box("/World/Cube", 0.4, (0.0, 0.0, 2.0), (0.05, 0.3, 0.9))
    UsdPhysics.RigidBodyAPI.Apply(shape.GetPrim())
    UsdPhysics.MassAPI.Apply(shape.GetPrim()).CreateMassAttr(1.0)
    rigid_api = PhysxSchema.PhysxRigidBodyAPI.Apply(shape.GetPrim())
    rigid_api.CreateEnableCCDAttr(True)
    rigid_api.CreateSolverPositionIterationCountAttr(8)
    rigid_api.CreateSolverVelocityIterationCountAttr(2)
    cube = RigidPrim(paths="/World/Cube")

    light = UsdLux.DomeLight.Define(stage, "/World/DomeLight")
    light.CreateIntensityAttr(700.0)
    camera = UsdGeom.Camera.Define(stage, "/World/OverviewCamera")
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.1, 100.0))
    view = Gf.Matrix4d().SetLookAt(Gf.Vec3d(4.0, -6.0, 3.5), Gf.Vec3d(0.0, 0.0, 0.8), Gf.Vec3d(0.0, 0.0, 1.0))
    camera.AddTransformOp().Set(view.GetInverse())
    if not args.headless:
        from omni.kit.viewport.utility import get_active_viewport

        viewport = get_active_viewport()
        if viewport is not None:
            viewport.camera_path = "/World/OverviewCamera"

    samples = report["samples"]
    callback_errors = []
    elapsed = 0.0
    timeline = omni.timeline.get_timeline_interface()

    def collect(dt, context):
        nonlocal elapsed
        if len(samples) >= args.steps or callback_errors:
            return
        try:
            dt = float(dt)
            if not math.isfinite(dt) or dt <= 0:
                raise RuntimeError(f"Invalid physics dt: {dt}")
            positions, orientations = cube.get_world_poses()
            linear, angular = cube.get_velocities()
            position = positions.numpy()[0].astype(float)
            orientation = orientations.numpy()[0].astype(float)
            velocity = linear.numpy()[0].astype(float)
            angular_velocity = angular.numpy()[0].astype(float)
            if not all(np.isfinite(value).all() for value in (position, orientation, velocity, angular_velocity)):
                raise RuntimeError("Non-finite rigid-body state")
            if position[2] < 0.15 or position[2] > 2.1:
                raise RuntimeError(f"Cube escaped the expected height interval: {position[2]}")
            if np.linalg.norm(position[:2]) > 0.05 or np.linalg.norm(velocity) > 10.0:
                raise RuntimeError("Excessive lateral drift or speed")
            elapsed += dt
            samples.append({
                "step": len(samples) + 1,
                "time_s": elapsed,
                "dt_s": dt,
                "position_m": position.tolist(),
                "orientation_wxyz": orientation.tolist(),
                "linear_velocity_m_s": velocity.tolist(),
                "angular_velocity_rad_s": angular_velocity.tolist(),
            })
        except Exception as exc:
            # Exceptions inside event handlers may be swallowed by Kit: propagate outside.
            callback_errors.append(f"{type(exc).__name__}: {exc}")

    callback_id = SimulationManager.register_callback(collect, event=SimulationEvent.PHYSICS_POST_STEP, order=100)
    started = time.monotonic()
    updates = 0
    try:
        timeline.play()
        while len(samples) < args.steps and not callback_errors:
            if not app.is_running():
                raise RuntimeError("Application closed before collecting all samples")
            if time.monotonic() - started > args.timeout:
                raise TimeoutError("Physics sample collection timed out; inspect Kit and PhysX logs")
            app.update()
            updates += 1
        if callback_errors:
            raise RuntimeError(callback_errors[0])
    finally:
        SimulationManager.deregister_callback(callback_id)
        timeline.stop()

    # Evaluate the recorded final state, before stop resets the live USD scene.
    tail = samples[-max(1, args.physics_hz // 2):]
    tail_z = [sample["position_m"][2] for sample in tail]
    max_tail_speed = max(float(np.linalg.norm(sample["linear_velocity_m_s"])) for sample in tail)
    max_tail_spin = max(float(np.linalg.norm(sample["angular_velocity_rad_s"])) for sample in tail)
    checks = {
        "sample_count": len(samples) == args.steps,
        "physics_dt": all(abs(sample["dt_s"] - 1.0 / args.physics_hz) < 1e-6 for sample in samples),
        "fell_at_least_one_metre": samples[0]["position_m"][2] - samples[-1]["position_m"][2] > 1.0,
        "final_height": all(abs(z - 0.2) <= 0.02 for z in tail_z),
        "settled_height": max(tail_z) - min(tail_z) <= 0.01,
        "settled_linear_speed": max_tail_speed <= 0.05,
        "settled_angular_speed": max_tail_spin <= 0.1,
    }
    report.update({
        "checks": checks,
        "passed": all(checks.values()),
        "app_updates": updates,
        "physics_samples": len(samples),
        "simulation_duration_s": elapsed,
        "wall_duration_s": time.monotonic() - started,
        "final_position_m": samples[-1]["position_m"],
        "maximum_final_half_second_speed_m_s": max_tail_speed,
        "render_validation": "not_measured; inspect GUI and use the later camera validation lesson",
    })


def main():
    args = parse_args()
    report = {
        "schema_version": 1,
        "target_isaac_sim": "6.0.1",
        "physics_engine": "physx",
        "physics_device": "cpu",
        "physics_hz": args.physics_hz,
        "requested_steps": args.steps,
        "headless": args.headless,
        "passed": False,
        "samples": [],
    }
    app = None
    exit_code = 1
    try:
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
        report["_app"] = app
        run_experiment(args, report)
        exit_code = 0 if report["passed"] else 1
    except Exception as exc:
        report.pop("_app", None)
        report["error"] = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    finally:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
            print(f"{'PASS' if report['passed'] else 'FAIL'}: {args.output.resolve()}", flush=True)
        except Exception:
            exit_code = 1
            raise
        finally:
            if app is not None:
                app.close(exit_code=exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
