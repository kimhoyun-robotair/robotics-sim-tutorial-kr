import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenUSD Fundamentals")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--radius", type=float, default=0.5)
    args = parser.parse_args()
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.steps is None and args.headless:
        args.steps = 120
    output = args.output or Path(__file__).parent / "output" / datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp

    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        from isaacsim.core.utils.viewports import set_camera_view
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdLux

        if not 0 < args.radius < 10:
            raise ValueError("--radius must be between 0 and 10")
        stage = Usd.Stage.CreateNew(str(output / "hello.usda"))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        parent = UsdGeom.Xform.Define(stage, "/hello")
        stage.SetDefaultPrim(parent.GetPrim())
        sphere = UsdGeom.Sphere.Define(stage, "/hello/world")
        sphere.CreateRadiusAttr(args.radius)
        parent.AddTranslateOp().Set(Gf.Vec3d(0, 0, 1))
        sphere.AddTranslateOp().Set(Gf.Vec3d(1, 0, 0))
        mat = UsdShade.Material.Define(stage, "/hello/Looks/Red")
        shader = UsdShade.Shader.Define(stage, "/hello/Looks/Red/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(1, 0, 0)
        )
        mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(mat)
        UsdLux.DistantLight.Define(stage, "/Light").CreateIntensityAttr(1500)
        layer = Sdf.Layer.CreateNew(str(output / "details.usda"))
        stage.GetRootLayer().subLayerPaths.append("details.usda")
        with Usd.EditContext(stage, layer):
            sphere.GetPrim().CreateAttribute(
                "tutorial:label", Sdf.ValueTypeNames.String
            ).Set("layer-authored")
        layer.Save()
        stage.GetRootLayer().Save()
        properties = sphere.GetPrim().GetPropertyNames()
        world_position = (
            UsdGeom.XformCache()
            .GetLocalToWorldTransform(sphere.GetPrim())
            .ExtractTranslation()
        )
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            sphere.GetRadiusAttr().Set(args.radius * 2)
        session_radius = sphere.GetRadiusAttr().Get()
        stage.GetRootLayer().Save()
        reopened = Usd.Stage.Open(stage.GetRootLayer(), Sdf.Layer.CreateAnonymous())
        saved_radius = (
            UsdGeom.Sphere.Get(reopened, "/hello/world").GetRadiusAttr().Get()
        )
        if saved_radius != args.radius:
            raise RuntimeError("Session-only radius leaked into the saved root layer")
        transform = Gf.Transform()
        transform.SetTranslation(Gf.Vec3d(2, 3, 4))
        transform.SetRotation(Gf.Rotation(Gf.Vec3d(0, 0, 1), 30))
        transform.SetScale(Gf.Vec3d(2, 2, 2))
        prim = UsdGeom.Xform.Define(stage, "/hello/MatrixExample")
        prim.AddTransformOp().Set(transform.GetMatrix())
        before = prim.GetLocalTransformation()
        decomposed = Gf.Transform(before)
        prim.ClearXformOpOrder()
        prim.AddTranslateOp().Set(decomposed.GetTranslation())
        prim.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(
            decomposed.GetRotation().GetQuat()
        )
        prim.AddScaleOp().Set(Gf.Vec3f(*decomposed.GetScale()))
        after = prim.GetLocalTransformation()
        error = max(abs(before[i][j] - after[i][j]) for i in range(4) for j in range(4))
        if error > 1e-6:
            raise RuntimeError(f"Transform decomposition changed the pose: {error}")
        stage.GetRootLayer().Save()
        report = {
            "property_names": properties,
            "world_position": list(world_position),
            "session_radius": session_radius,
            "saved_radius": saved_radius,
            "traversal": [str(p.GetPath()) for p in stage.Traverse()],
            "default_prim_subtree": [
                str(p.GetPath()) for p in Usd.PrimRange(stage.GetDefaultPrim())
            ],
            "transform_max_error": error,
        }
        (output / "inspection.json").write_text(json.dumps(report, indent=2))
        omni.usd.get_context().open_stage(str(output / "hello.usda"))
        set_camera_view(eye=[4, 4, 3], target=[1, 0, 1])
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            app.update()
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        app.close()


if __name__ == "__main__":
    main()
