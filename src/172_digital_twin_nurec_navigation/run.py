"""Load a real local NuRec scene and run the official Nova Carter navigation graph."""
import argparse
from itertools import count
import json
from pathlib import Path


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--scenario", choices=["cafe", "galileo", "wormhole", "lounge"], default="cafe")
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 500")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output", type=Path, default=package / "output")
    parser.add_argument("--check", action="store_true", help="Check dataset paths without starting Kit")
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 500
    config = json.loads((package / "scenarios.json").read_text())[args.scenario]
    scene = args.dataset.expanduser().resolve() / config["stage"]
    if not scene.is_file():
        parser.error(f"NuRec dataset scene is missing: {scene}")
    if args.steps is not None and args.steps < 1:
        parser.error("steps must be positive")
    if args.check:
        print(json.dumps({"scene": str(scene), **config}, indent=2))
        print("Local root scene exists; referenced resources, GPU rendering, and navigation are not verified")
        return
    output = args.output.expanduser().resolve()
    if output.exists():
        parser.error(f"Output exists; use another path: {output}")
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import carb
        import omni.kit.commands
        import omni.timeline
        import omni.usd
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        from pxr import PhysxSchema, UsdGeom, UsdPhysics
        context = omni.usd.get_context()
        if not context.open_stage(str(scene)):
            raise RuntimeError(f"Failed to open NuRec scene: {scene}")
        app.update()
        stage = context.get_stage()
        for prim in stage.Traverse():
            if prim.IsA(UsdPhysics.Scene):
                PhysxSchema.PhysxSceneAPI.Apply(prim).GetUpdateTypeAttr().Set("Synchronous")
                break
        else:
            physics = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
            PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim()).CreateUpdateTypeAttr("Synchronous")
        assets = get_assets_root_path()
        if not assets:
            raise RuntimeError("Isaac Sim asset root unavailable")
        carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)
        robot_path = "/World/NovaCarterNav"
        robot = add_reference_to_stage(assets + "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd", robot_path)
        app.update()
        target = stage.GetPrimAtPath(robot_path + "/targetXform")
        chassis = stage.GetPrimAtPath(robot_path + "/chassis_link")
        if not target.IsValid() or not chassis.IsValid():
            raise RuntimeError("Carter target/chassis is missing from the referenced navigation asset")
        for prim, position in [(robot, config["start"]), (target, config["relative_target"])]:
            attr = prim.GetAttribute("xformOp:translate")
            if not attr:
                attr = UsdGeom.Xformable(prim).AddTranslateOp().GetAttr()
            attr.Set(tuple(position))
        if config["collision_ground"]:
            path = "/World/CollisionPlane"
            omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_path=path, prim_type="Plane")
            plane = stage.GetPrimAtPath(path)
            plane.GetAttribute("xformOp:scale").Set((10, 10, 1))
            plane.GetAttribute("xformOp:translate").Set(tuple(config["start"]))
            plane.GetAttribute("visibility").Set("invisible")
            UsdPhysics.CollisionAPI.Apply(plane).CreateCollisionEnabledAttr(True)
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        records = []
        for step in count():
            if args.steps is not None and step >= args.steps:
                break
            if not app.is_running():
                break
            app.update()
            if not app.is_running():
                break
            if step % 10 == 0 or (args.steps is not None and step == args.steps - 1):
                position = UsdGeom.Xformable(chassis).ComputeLocalToWorldTransform(0).ExtractTranslation()
                records.append({"step": step, "timeline_seconds": timeline.get_current_time(),
                                "chassis_world_position": list(position)})
        if app.is_running():
            timeline.pause()
        output.mkdir(parents=True, exist_ok=False)
        (output / "trajectory.json").write_text(json.dumps(records, indent=2) + "\n")
        print(f"Recorded {len(records)} observed chassis positions at {output}; assess goal reach from trajectory")
    finally:
        app.close()


if __name__ == "__main__":
    main()
