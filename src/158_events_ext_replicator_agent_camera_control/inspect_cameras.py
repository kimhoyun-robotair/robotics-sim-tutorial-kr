"""Run in Script Editor after IRA Set Up Simulation; reports real world camera poses."""
import omni.usd
from pxr import Usd, UsdGeom

stage = omni.usd.get_context().get_stage()
cache = UsdGeom.XformCache(Usd.TimeCode.Default())
for prim in stage.Traverse():
    if prim.IsA(UsdGeom.Camera) and str(prim.GetPath()).startswith("/World/Cameras/"):
        camera = UsdGeom.Camera(prim)
        transform = cache.GetLocalToWorldTransform(prim)
        print(str(prim.GetPath()), "world position", transform.ExtractTranslation(),
              "focalLength", camera.GetFocalLengthAttr().Get(),
              "view direction", transform.TransformDir((0, 0, -1)))
