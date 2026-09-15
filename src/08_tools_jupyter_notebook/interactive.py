"""Run inside Isaac Sim Script Editor or the VS Code interactive connection."""
import omni.usd
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()
path = "/World/EditorCube"
if stage.GetPrimAtPath(path):
    raise RuntimeError(f"{path} already exists; use a new stage or change path")
cube = UsdGeom.Cube.Define(stage, path)
cube.CreateSizeAttr(0.5)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.5))
cube.CreateDisplayColorAttr().Set([Gf.Vec3f(0.15, 0.65, 0.95)])
print("created", cube.GetPath(), "size", cube.GetSizeAttr().Get())
