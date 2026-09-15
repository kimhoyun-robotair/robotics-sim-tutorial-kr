"""UR10e와 Robotiq 조립 결과의 articulation·joint 연결 검사 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='UR10e와 Robotiq 조립 결과의 articulation·joint 연결 검사')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Kit update limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--frames", type=int, default=1200, help="Legacy headless update limit when --steps is omitted; does not close the GUI")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--asset", help="Assembled UR10e+Robotiq USD, otherwise official prebuilt sample")
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 1:
        parser.error("--frames must be positive")
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        from pxr import Usd, UsdGeom, UsdPhysics
        from isaacsim.core.api import World
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.storage.native import get_assets_root_path
        world = World(stage_units_in_meters=1.0)
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac 5.1 asset root unavailable; pass --asset /absolute/path/ur_gripper.usd")
        asset = args.asset or asset_root + "/Isaac/Samples/Rigging/Manipulator/import_manipulator/ur10e/ur/ur_gripper.usd"
        root = add_reference_to_stage(usd_path=asset, prim_path="/ur")
        if not root.GetChildren():
            raise RuntimeError(f"Robot asset did not resolve: {asset}")

        roots = [str(prim.GetPath()) for prim in Usd.PrimRange(root) if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
        joints = []
        for prim in Usd.PrimRange(root):
            if prim.IsA(UsdPhysics.Joint):
                joint = UsdPhysics.Joint(prim)
                joints.append({"path": str(prim.GetPath()), "type": prim.GetTypeName(),
                               "body0": [str(path) for path in joint.GetBody0Rel().GetTargets()],
                               "body1": [str(path) for path in joint.GetBody1Rel().GetTargets()]})
        report = {"asset": asset, "articulation_roots": roots, "single_articulation": len(roots) == 1,
                  "variant_sets": {name: root.GetVariantSet(name).GetVariantNames() for name in root.GetVariantSets().GetNames()},
                  "joints": joints}
        (output / "assembly_report.json").write_text(json.dumps(report, indent=2))
        world.stage.GetRootLayer().Export(str(output / "inspection_scene.usda"))
        print(json.dumps(report, indent=2), "output=", output)
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            app.update()
            frame += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
