"""Rubik 에셋의 강체·충돌체·질량·반발 재질 실험 — Isaac Sim 5.1 standalone lesson."""
import argparse
import json
from pathlib import Path
import time


def main():
    parser = argparse.ArgumentParser(description='Rubik 에셋의 강체·충돌체·질량·반발 재질 실험')
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="Positive physics step limit; omitted: GUI stays open (headless: 360)")
    parser.add_argument("--output", type=Path, help="New output directory; existing paths are rejected")
    parser.add_argument("--physics", choices=["visual", "rigid", "mesh", "sphere"], default="sphere")
    parser.add_argument("--asset", help="Rubik USD override; default official Props/Rubiks_Cube/rubiks_cube.usd")
    parser.add_argument("--mass", type=float, default=0.1, help="Mass in kg")
    parser.add_argument("--restitution", type=float, default=0.8)
    parser.add_argument("--slope", type=float, default=10.0, help="Ground rotation around X in degrees")
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 360
    output = args.output or Path(__file__).resolve().parent / "output" / str(time.time_ns())
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    app = SimulationApp({"headless": args.headless})
    try:
        import numpy as np
        from pxr import Usd, UsdGeom, UsdPhysics, UsdShade
        from isaacsim.core.api import World
        from isaacsim.core.prims import SingleRigidPrim, SingleXFormPrim
        from isaacsim.core.utils.stage import add_reference_to_stage
        from isaacsim.core.utils.nucleus import get_assets_root_path
        from isaacsim.core.utils.rotations import euler_angles_to_quat
        if args.mass <= 0 or not 0 <= args.restitution <= 1:
            raise ValueError("--mass must be positive and --restitution must be in [0, 1]")
        world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/60)
        ground = world.scene.add_default_ground_plane()
        ground.set_world_pose(orientation=euler_angles_to_quat(np.array([args.slope, 0.0, 0.0]), degrees=True))
        asset_root = get_assets_root_path() if not args.asset else None
        if not args.asset and not asset_root:
            raise RuntimeError("Isaac asset root unavailable; supply --asset rubiks_cube.usd")
        asset = args.asset or asset_root + "/Isaac/Props/Rubiks_Cube/rubiks_cube.usd"
        root = add_reference_to_stage(usd_path=asset, prim_path="/World/Rubik")
        for prim in list(Usd.PrimRange(root)):
            if prim.IsInstance():
                prim.SetInstanceable(False)
        meshes = [prim for prim in Usd.PrimRange(root) if prim.IsA(UsdGeom.Mesh)]
        if not meshes:
            raise RuntimeError(f"No Rubik meshes resolved from {asset}; check the 5.1 asset installation")
        # 비교 실험의 시작 조건을 명시한다. 참고 에셋에 있던 물리 스키마를 제거한다.
        for prim in Usd.PrimRange(root):
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
            if prim.HasAPI(UsdPhysics.CollisionAPI):
                prim.RemoveAPI(UsdPhysics.CollisionAPI)
            if prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                prim.RemoveAPI(UsdPhysics.MeshCollisionAPI)
        material = UsdShade.Material.Define(world.stage, "/World/RubikPhysicsMaterial")
        physics_material = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        physics_material.CreateStaticFrictionAttr(0.5)
        physics_material.CreateDynamicFrictionAttr(0.4)
        physics_material.CreateRestitutionAttr(args.restitution)
        colliders = []
        if args.physics == "mesh":
            for mesh in meshes:
                UsdPhysics.CollisionAPI.Apply(mesh)
                UsdPhysics.MeshCollisionAPI.Apply(mesh).CreateApproximationAttr("convexHull")
                colliders.append(mesh)
        elif args.physics == "sphere":
            sphere = UsdGeom.Sphere.Define(world.stage, "/World/Rubik/PhysicsSphere")
            sphere.CreateRadiusAttr(0.07)
            sphere.MakeInvisible()
            UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
            colliders.append(sphere.GetPrim())
        for collider in colliders:
            UsdShade.MaterialBindingAPI.Apply(collider).Bind(material, materialPurpose="physics")
        if args.physics == "visual":
            prop = world.scene.add(SingleXFormPrim(prim_path="/World/Rubik", name="rubik", position=np.array([0.0, 0.0, 1.0])))
        else:
            UsdPhysics.RigidBodyAPI.Apply(root)
            UsdPhysics.MassAPI.Apply(root).CreateMassAttr(args.mass)
            prop = world.scene.add(SingleRigidPrim(prim_path="/World/Rubik", name="rubik", position=np.array([0.0, 0.0, 1.0])))
        world.reset()
        world.stage.GetRootLayer().Export(str(output / "configured_scene.usda"))
        samples = []
        for step in range(sample_steps):
            if not app.is_running():
                return
            world.step(render=not args.headless)
            if not app.is_running():
                return
            if step % 15 == 0:
                samples.append({"step": step, "position_m": prop.get_world_pose()[0].tolist()})
                if step % 60 == 0:
                    print(samples[-1])
        if not app.is_running():
            return
        result = {"physics": args.physics, "asset": asset, "colliders": [str(prim.GetPath()) for prim in colliders],
                  "mass_kg": args.mass, "restitution": args.restitution, "slope_deg": args.slope, "samples": samples}
        (output / "result.json").write_text(json.dumps(result, indent=2))
        print("output=", output)
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        app.close()


if __name__ == "__main__":
    main()
