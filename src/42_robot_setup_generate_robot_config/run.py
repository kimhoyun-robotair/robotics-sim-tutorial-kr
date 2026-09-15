"""Lula 편집을 위한 UR10e 인스턴스 해제와 관절 목록 준비 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Lula 편집을 위한 UR10e 인스턴스 해제와 관절 목록 준비')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Kit update limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--frames", type=int, default=1200, help="Legacy headless update limit when --steps is omitted; does not close the GUI")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--asset", help="Configured UR10e+Robotiq USD override")
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
        asset = args.asset or asset_root + "/Isaac/Samples/Rigging/Manipulator/configure_manipulator/ur10e/ur/ur_gripper.usd"
        root = add_reference_to_stage(usd_path=asset, prim_path="/ur")
        if not root.GetChildren():
            raise RuntimeError(f"Robot asset did not resolve: {asset}")

        changed = []
        while True:
            instances = [prim for prim in Usd.PrimRange(root) if prim.IsInstance()]
            if not instances:
                break
            for prim in instances:
                changed.append(str(prim.GetPath()))
                prim.SetInstanceable(False)
        joints = [{"name": prim.GetName(), "path": str(prim.GetPath()), "type": prim.GetTypeName()}
                  for prim in Usd.PrimRange(root) if prim.IsA(UsdPhysics.Joint)]
        report = {"asset": asset, "uninstanced_prims": changed, "joints": joints,
                  "active_arm_joints": ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]}
        world.stage.GetRootLayer().Export(str(output / "lula_ready.usda"))
        (output / "preparation_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), "output=", output)
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            app.update()
            frame += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
