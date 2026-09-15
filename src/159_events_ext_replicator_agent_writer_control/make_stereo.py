"""Script Editor: make_stereo('/World/Cameras/Camera', 0.12)."""
import omni.usd
import omni.kit.commands
from pxr import Gf, Usd, UsdGeom


def make_stereo(left_path, baseline_m=0.12):
    stage = omni.usd.get_context().get_stage()
    left = stage.GetPrimAtPath(left_path)
    right_path = left_path + "_R"
    if not left or not left.IsA(UsdGeom.Camera):
        raise ValueError(f"Not a camera: {left_path}")
    if stage.GetPrimAtPath(right_path):
        raise ValueError(f"Right camera already exists: {right_path}")
    if baseline_m <= 0:
        raise ValueError("Baseline must be positive")
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    left_world = cache.GetLocalToWorldTransform(left)
    world_offset = left_world.TransformDir(Gf.Vec3d(1, 0, 0)).GetNormalized()
    right_world = Gf.Matrix4d(left_world)
    right_world.SetTranslateOnly(left_world.ExtractTranslation() + world_offset * (baseline_m / UsdGeom.GetStageMetersPerUnit(stage)))
    parent_world = cache.GetLocalToWorldTransform(left.GetParent())
    omni.kit.commands.execute("CopyPrim", path_from=left_path, path_to=right_path)
    right = UsdGeom.Xformable(stage.GetPrimAtPath(right_path))
    right.ClearXformOpOrder()
    right.AddTransformOp(opSuffix="stereo").Set(right_world * parent_world.GetInverse())
    print("Stereo pair:", left_path, right_path, "baseline meters:", baseline_m)
