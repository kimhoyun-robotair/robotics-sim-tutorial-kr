import argparse
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Scene Setup Snippets")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None,
        help="Positive physics step limit; omitted: GUI stays open (headless: 240)",
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--mass", type=float, default=1.0)
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    sample_steps = args.steps if args.steps is not None else 240
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import carb
        import numpy as np
        import omni.usd
        from isaacsim.core.api import World
        from isaacsim.core.api.objects import DynamicCuboid
        from isaacsim.core.api.materials import PhysicsMaterial
        from isaacsim.core.prims import RigidPrim
        from isaacsim.core.utils.semantics import add_labels
        from omni.physx import get_physx_scene_query_interface
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdPhysics, UsdLux, PhysxSchema

        if not 0.01 <= args.mass <= 100:
            raise ValueError("--mass must be between 0.01 and 100 kg")
        world = World(stage_units_in_meters=1.0, physics_dt=1 / 60, rendering_dt=1 / 60)
        world.scene.add_default_ground_plane()
        stage = omni.usd.get_context().get_stage()
        UsdLux.DistantLight.Define(stage, "/World/Light").CreateIntensityAttr(1500)
        physics = UsdPhysics.Scene.Get(stage, world.get_physics_context().prim_path)
        physics.CreateGravityMagnitudeAttr(9.81)
        physx = PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
        physx.CreateEnableCCDAttr(True)
        physx.CreateEnableStabilizationAttr(True)
        material = PhysicsMaterial(
            prim_path="/World/Looks/Friction", static_friction=0.5, dynamic_friction=0.5
        )
        for i, x in enumerate((-1.0, 0.0, 1.0)):
            bottom = DynamicCuboid(
                prim_path=f"/World/Bottom_{i}",
                name=f"bottom_{i}",
                position=np.array([x, 0, 0.25]),
                size=0.5,
                mass=args.mass,
                color=np.array([0.6, 0.1, 0.1]),
            )
            top = DynamicCuboid(
                prim_path=f"/World/Top_{i}",
                name=f"top_{i}",
                position=np.array([x, 0, 1.0]),
                size=0.5,
                mass=args.mass,
                color=np.array([0.1, 0.1, 0.6]),
            )
            bottom.apply_physics_material(material)
            top.apply_physics_material(material)
        bottoms = world.scene.add(
            RigidPrim(
                "/World/Bottom_[0-2]",
                name="bottom_view",
                track_contact_forces=True,
                contact_filter_prim_paths_expr=["/World/Top_.*"],
                max_contact_count=60,
            )
        )
        tops = world.scene.add(RigidPrim("/World/Top_[0-2]", name="top_view"))
        mesh = UsdGeom.Mesh.Define(stage, "/World/Mesh")
        mesh.CreatePointsAttr(
            [(-0.2, -0.2, 0), (0.2, -0.2, 0), (0, 0.2, 0), (0, 0, 0.4)]
        )
        mesh.CreateFaceVertexCountsAttr([3, 3, 3, 3])
        mesh.CreateFaceVertexIndicesAttr([0, 2, 1, 0, 1, 3, 1, 2, 3, 2, 0, 3])
        mesh.CreateSubdivisionSchemeAttr("none")
        mesh.AddTranslateOp().Set(Gf.Vec3d(0, 2, 0.1))
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr(
            "convexHull"
        )
        UsdPhysics.MassAPI.Apply(mesh.GetPrim()).CreateMassAttr(2.0)
        UsdPhysics.RigidBodyAPI.Apply(mesh.GetPrim())
        for prim in Usd.PrimRange(stage.GetPrimAtPath("/World")):
            if prim.IsA(UsdGeom.Mesh):
                add_labels(prim, labels=[prim.GetName()], instance_name="class")
        preview = UsdShade.Material.Define(stage, "/World/Looks/Green")
        shader = UsdShade.Shader.Define(stage, "/World/Looks/Green/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0, 0.7, 0.2)
        )
        preview.CreateSurfaceOutput().ConnectToSource(
            shader.ConnectableAPI(), "surface"
        )
        UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(preview)
        marker = UsdGeom.Xform.Define(stage, "/World/AlignedMarker")
        pose = UsdGeom.XformCache().GetLocalToWorldTransform(mesh.GetPrim())
        marker.AddTransformOp().Set(pose)
        selection = omni.usd.get_context().get_selection()
        selection.set_selected_prim_paths([str(mesh.GetPath())], True)
        initial_size = (
            UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
            .ComputeWorldBound(mesh.GetPrim())
            .ComputeAlignedRange()
            .GetSize()
        )
        stage.GetRootLayer().Export(str(output / "initial_scene.usda"))
        world.reset()
        for i in range(sample_steps):
            if not app.is_running():
                return
            if i == sample_steps // 2:
                tops.apply_forces(np.array([[1.0, 0, 0]] * 3))
            world.step(render=not args.headless)
        if not app.is_running():
            return
        query = get_physx_scene_query_interface()
        ray = query.raycast_closest(carb.Float3(0, 0, 3), carb.Float3(0, 0, -1), 5.0)
        overlap_paths = []

        def collect(hit):
            overlap_paths.append(str(hit.rigid_body))
            return True

        query.overlap_box(
            carb.Float3(2, 0.4, 0.6),
            carb.Float3(0, 0, 0.5),
            carb.Float4(0, 0, 0, 1),
            collect,
            False,
        )
        contact = bottoms.get_contact_force_data(dt=1 / 60)
        friction = bottoms.get_friction_data(dt=1 / 60)
        report = {
            "mesh_world_size_m": list(initial_size),
            "selected_prims": selection.get_selected_prim_paths(),
            "mesh_world_position": list(pose.ExtractTranslation()),
            "bottom_positions": bottoms.get_world_poses()[0].tolist(),
            "top_positions": tops.get_world_poses()[0].tolist(),
            "net_contact_forces_N": bottoms.get_net_contact_forces(dt=1 / 60).tolist(),
            "top_bottom_contact_matrix_N": bottoms.get_contact_force_matrix(
                dt=1 / 60
            ).tolist(),
            "contact_data": [x.tolist() for x in contact],
            "friction_data": [x.tolist() for x in friction],
            "raycast": {
                "hit": bool(ray["hit"]),
                "distance_m": float(ray["distance"]) if ray["hit"] else None,
                "rigid_body": str(ray.get("rigidBody", "")),
            },
            "overlap_bodies": overlap_paths,
        }
        (output / "scene_queries.json").write_text(json.dumps(report, indent=2))
        print(
            json.dumps(
                {
                    k: v
                    for k, v in report.items()
                    if k not in ("contact_data", "friction_data")
                },
                indent=2,
            )
        )
        print(f"Outputs: {output.resolve()}")
        while args.steps is None and not args.headless and app.is_running():
            world.step(render=True)
    finally:
        app.close()


if __name__ == "__main__":
    main()
