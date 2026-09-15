"""Author the H1 policy's initial state and drive properties with explicit unit conversion."""
import argparse
import json
import math
from pathlib import Path
import re


def matching_value(pattern_values, name):
    matches = [value for pattern, value in pattern_values.items() if re.fullmatch(pattern, name)]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one configuration for {name}: {matches}")
    return float(matches[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("h1_policy.json"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="UI update limit; omitted or 0 keeps the stage open without policy inference; headless requires a positive value")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("headless requires positive --steps")
    cfg = json.loads(args.config.read_text())
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        from pxr import Gf, Sdf, UsdGeom, UsdPhysics, PhysxSchema
        from isaacsim.storage.native import get_assets_root_path
        root = get_assets_root_path()
        if not root:
            raise RuntimeError("Isaac Sim 5.1 asset root not available")
        source = root + "/Isaac/Robots/Unitree/H1/h1.usd"
        if not Sdf.Layer.FindOrOpen(source):
            raise RuntimeError(f"Cannot read {source}")
        layer = Sdf.Layer.CreateNew(str(output / "h1_policy.usda"))
        layer.subLayerPaths = [source]
        layer.Save()
        context = omni.usd.get_context()
        if not context.open_stage(layer.identifier):
            raise RuntimeError("Cannot open the H1 override stage")
        stage = context.get_stage()
        for _ in range(1200):
            app.update()
            if not context.is_stage_loading():
                break
        if context.is_stage_loading():
            raise RuntimeError("H1 loading timed out after 1200 updates")
        robot_prim = stage.GetPrimAtPath("/h1")
        if not robot_prim:
            raise RuntimeError("H1 asset does not contain /h1")
        transform = UsdGeom.Xformable(robot_prim)
        transform.ClearXformOpOrder()
        transform.AddTranslateOp(opSuffix="policy").Set(Gf.Vec3d(*cfg["base_position_m"]))
        transform.AddOrientOp(opSuffix="policy").Set(Gf.Quatf(1, Gf.Vec3f(0)))
        reports = []
        for prim in stage.Traverse():
            if not prim.IsA(UsdPhysics.RevoluteJoint):
                continue
            name = prim.GetName()
            groups = [g for g in cfg["actuators"].values() if any(re.fullmatch(p, name) for p in g["joint_names_expr"])]
            if len(groups) != 1:
                raise ValueError(f"Missing or ambiguous actuator group for {name}")
            group = groups[0]
            position = matching_value(cfg["joint_positions_rad"], name)
            stiffness = matching_value(group["stiffness"], name)
            damping = matching_value(group["damping"], name)
            drive = UsdPhysics.DriveAPI.Apply(prim, "angular")
            drive.CreateTypeAttr("force")
            drive.CreateTargetPositionAttr(math.degrees(position))
            drive.CreateTargetVelocityAttr(0)
            drive.CreateStiffnessAttr(stiffness * math.pi / 180)
            drive.CreateDampingAttr(damping * math.pi / 180)
            drive.CreateMaxForceAttr(group["effort_limit"])
            state = PhysxSchema.JointStateAPI.Apply(prim, "angular")
            state.CreatePositionAttr(math.degrees(position))
            state.CreateVelocityAttr(0)
            joint = PhysxSchema.PhysxJointAPI.Apply(prim)
            joint.CreateMaxJointVelocityAttr(math.degrees(group["velocity_limit"]))
            reports.append({"joint": name, "initial_position_rad": position, "usd_position_deg": math.degrees(position),
                            "stiffness_rad": stiffness, "usd_stiffness_per_deg": stiffness * math.pi / 180,
                            "damping_rad": damping, "usd_damping_per_deg": damping * math.pi / 180,
                            "max_effort_nm": group["effort_limit"], "max_velocity_rad_s": group["velocity_limit"]})
        if len(reports) != 19:
            raise RuntimeError(f"Expected the H1 policy's 19 controlled joints; found {len(reports)}")
        stage.GetRootLayer().Save()
        (output / "joint_configuration.json").write_text(json.dumps(reports, indent=2))
        print(json.dumps(reports, indent=2))
        print("Configuration authored. This script does not run a locomotion policy.")
        count = 0
        while app.is_running() and (args.steps == 0 or count < args.steps):
            app.update()
            count += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
