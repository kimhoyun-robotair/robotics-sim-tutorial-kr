"""Measure the step response of a real PhysX prismatic drive and expose it to Gain Tuner."""
import argparse
import csv
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stiffness", type=float, default=100.0, help="Linear drive stiffness, N/m")
    parser.add_argument("--damping", type=float, default=20.0, help="Linear drive damping, N s/m")
    parser.add_argument("--mass", type=float, default=1.0, help="Slider mass, kg")
    parser.add_argument("--target", type=float, default=0.5, help="Target position, m")
    parser.add_argument("--velocity", type=float, default=0.0, help="Target velocity, m/s; use stiffness 0 for velocity control")
    parser.add_argument("--steps", type=int, default=None, help="240 Hz physics step limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 720 if args.headless else 0
    if args.mass <= 0 or min(args.stiffness, args.damping, args.steps) < 0 or not 0 <= args.target <= 1:
        parser.error("mass>0, nonnegative gains/steps, target within [0,1] are required")
    if args.headless and args.steps == 0:
        parser.error("Headless execution needs positive --steps")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        import numpy as np
        from pxr import Gf, UsdGeom, UsdLux, UsdPhysics
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleArticulation
        from isaacsim.core.utils.types import ArticulationAction
        import usd.schema.isaac.robot_schema as rs
        world = World(stage_units_in_meters=1, physics_dt=1 / 240, rendering_dt=1 / 60)
        stage = omni.usd.get_context().get_stage()
        robot = UsdGeom.Xform.Define(stage, "/GainRig").GetPrim()
        stage.SetDefaultPrim(robot)
        for name in ["base", "slider"]:
            prim = UsdGeom.Xform.Define(stage, f"/GainRig/{name}").GetPrim()
            UsdPhysics.RigidBodyAPI.Apply(prim)
            UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(args.mass if name == "slider" else 1.0)
            geom = UsdGeom.Cube.Define(stage, str(prim.GetPath()) + "/visual")
            geom.CreateSizeAttr(0.1)
            geom.AddTranslateOp().Set(Gf.Vec3d(-0.15 if name == "base" else 0, 0, 1))
            geom.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.6, 0.9) if name == "slider" else Gf.Vec3f(0.5)])
        fixed = UsdPhysics.FixedJoint.Define(stage, "/GainRig/fixed_joint")
        fixed.CreateBody1Rel().SetTargets(["/GainRig/base"])
        UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
        joint = UsdPhysics.PrismaticJoint.Define(stage, "/GainRig/slider_joint")
        joint.CreateBody0Rel().SetTargets(["/GainRig/base"])
        joint.CreateBody1Rel().SetTargets(["/GainRig/slider"])
        joint.CreateAxisAttr("X")
        joint.CreateLowerLimitAttr(0)
        joint.CreateUpperLimitAttr(1)
        drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "linear")
        drive.CreateStiffnessAttr(args.stiffness)
        drive.CreateDampingAttr(args.damping)
        drive.CreateMaxForceAttr(200.0)
        drive.CreateTargetPositionAttr(args.target)
        drive.CreateTargetVelocityAttr(args.velocity)
        rs.ApplyRobotAPI(robot)
        for name in ["base", "slider"]:
            prim = stage.GetPrimAtPath(f"/GainRig/{name}")
            rs.ApplyLinkAPI(prim)
            robot.GetRelationship(rs.Relations.ROBOT_LINKS.name).AddTarget(prim.GetPath())
        rs.ApplyJointAPI(joint.GetPrim())
        robot.GetRelationship(rs.Relations.ROBOT_JOINTS.name).AddTarget(joint.GetPath())
        UsdLux.DomeLight.Define(stage, "/World/Light").CreateIntensityAttr(800)
        stage.GetRootLayer().Export(str(output / "gain_rig.usda"))
        articulation = world.scene.add(SingleArticulation(prim_path="/GainRig", name="gain_rig"))
        world.reset()
        articulation.apply_action(ArticulationAction(joint_positions=np.array([args.target]), joint_velocities=np.array([args.velocity])))
        index = articulation.get_dof_index("slider_joint")
        last_sample = None
        peak_position = float("-inf")
        step = 0
        with (output / "response.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["time_s", "position_m", "velocity_m_s", "target_position_m", "target_velocity_m_s"])
            while app.is_running() and (args.steps == 0 or step < args.steps):
                world.step(render=not args.headless)
                if not app.is_running():
                    break
                if not world.is_playing():
                    continue
                position = float(articulation.get_joint_positions()[index])
                velocity = float(articulation.get_joint_velocities()[index])
                row = [(step + 1) / 240, position, velocity, args.target, args.velocity]
                writer.writerow(row)
                last_sample = row
                peak_position = max(peak_position, position)
                step += 1
        if last_sample is not None:
            metrics = {"samples": step, "final_position_m": last_sample[1],
                       "final_velocity_m_s": last_sample[2], "final_position_error_m": args.target - last_sample[1],
                       "overshoot_m": max(0.0, peak_position - args.target)}
            (output / "metrics.json").write_text(json.dumps(metrics, indent=2))
            print(json.dumps(metrics, indent=2))
    finally:
        app.close()


if __name__ == "__main__":
    main()
