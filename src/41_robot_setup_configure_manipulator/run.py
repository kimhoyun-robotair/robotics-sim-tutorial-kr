"""UR10e solver·Robotiq 마찰·finger effort를 로컬 layer에 설정 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='UR10e solver·Robotiq 마찰·finger effort를 로컬 layer에 설정')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Kit update limit; omitted or 0 keeps the GUI open")
    parser.add_argument("--frames", type=int, default=1200, help="Legacy headless update limit when --steps is omitted; does not close the GUI")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--asset", help="UR10e+Robotiq USD override")
    parser.add_argument("--friction", type=float, default=1.0)
    parser.add_argument("--max-force", type=float, default=200.0)
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

        from pxr import PhysxSchema, UsdShade
        if args.friction < 0 or args.max_force <= 0:
            raise ValueError("Friction must be nonnegative and max force positive")
        # 인스턴스 내부의 collider를 편집할 수 있도록 현재 layer에서만 해제한다.
        for prim in list(Usd.PrimRange(root)):
            if prim.IsInstance():
                prim.SetInstanceable(False)
        roots = [prim for prim in Usd.PrimRange(root) if prim.HasAPI(UsdPhysics.ArticulationRootAPI)]
        if len(roots) != 1:
            raise RuntimeError(f"Expected one articulation, found {len(roots)}")
        articulation = PhysxSchema.PhysxArticulationAPI.Apply(roots[0])
        articulation.CreateArticulationEnabledAttr(True)
        articulation.CreateSolverPositionIterationCountAttr(64)
        articulation.CreateSolverVelocityIterationCountAttr(4)
        articulation.CreateSleepThresholdAttr(0.00005)
        articulation.CreateStabilizationThresholdAttr(0.00001)
        fingers = [prim for prim in Usd.PrimRange(root) if prim.GetName() == "finger_joint" and prim.IsA(UsdPhysics.Joint)]
        if len(fingers) != 1:
            raise RuntimeError(f"Expected one finger_joint, found {len(fingers)}")
        drive = UsdPhysics.DriveAPI.Get(fingers[0], "angular")
        if not drive:
            raise RuntimeError("finger_joint has no angular drive")
        drive.CreateMaxForceAttr(args.max_force)
        material = UsdShade.Material.Define(world.stage, "/ur/Looks/FingerPhysics")
        physics = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        physics.CreateStaticFrictionAttr(args.friction)
        physics.CreateDynamicFrictionAttr(args.friction)
        colliders = [prim for prim in Usd.PrimRange(root) if prim.HasAPI(UsdPhysics.CollisionAPI)
                     and any(name in str(prim.GetPath()) for name in ["left_inner_finger", "right_inner_finger"])]
        if len(colliders) < 2:
            raise RuntimeError("Both finger tip colliders must be present; inspect your asset hierarchy")
        for collider in colliders:
            UsdShade.MaterialBindingAPI.Apply(collider).Bind(material, materialPurpose="physics")
        report = {"articulation": str(roots[0].GetPath()), "solver_position_iterations": articulation.GetSolverPositionIterationCountAttr().Get(),
                  "solver_velocity_iterations": articulation.GetSolverVelocityIterationCountAttr().Get(),
                  "finger_joint": str(fingers[0].GetPath()), "max_force": drive.GetMaxForceAttr().Get(),
                  "friction": physics.GetStaticFrictionAttr().Get(), "material_bound_colliders": [str(p.GetPath()) for p in colliders]}
        world.stage.GetRootLayer().Export(str(output / "configured.usda"))
        (output / "configuration_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2), "output=", output)
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            app.update()
            frame += 1
    finally:
        app.close()


if __name__ == "__main__":
    main()
