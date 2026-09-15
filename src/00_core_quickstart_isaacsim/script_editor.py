"""Run this whole file in Isaac Sim's Script Editor on a new, stopped stage."""

import numpy as np
import omni.usd
from isaacsim.core.api.objects import DynamicCuboid, VisualCuboid
from isaacsim.core.api.objects.ground_plane import GroundPlane
from isaacsim.core.prims import GeometryPrim, RigidPrim
from pxr import Gf, UsdGeom, UsdLux

stage = omni.usd.get_context().get_stage()
if stage.GetPrimAtPath("/World/Quickstart").IsValid():
    raise RuntimeError("This exercise already exists. Use File > New before rerunning.")
UsdGeom.Xform.Define(stage, "/World/Quickstart")
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
GroundPlane(prim_path="/World/Quickstart/Ground", z_position=0)
UsdLux.DistantLight.Define(stage, "/World/Quickstart/Light").CreateIntensityAttr(1000)
VisualCuboid(
    prim_path="/World/Quickstart/Visual",
    name="visual",
    position=np.array([-0.5, 0.0, 1.5]),
    size=0.3,
    color=np.array([1.0, 1.0, 0.0]),
)
VisualCuboid(
    prim_path="/World/Quickstart/Converted",
    name="converted",
    position=np.array([0.5, 0.0, 1.5]),
    size=0.3,
    color=np.array([0.0, 1.0, 1.0]),
)
RigidPrim("/World/Quickstart/Converted")
GeometryPrim("/World/Quickstart/Converted").apply_collision_apis()
DynamicCuboid(
    prim_path="/World/Quickstart/Dynamic",
    name="dynamic",
    position=np.array([1.5, 0.0, 1.5]),
    size=0.3,
    color=np.array([0.2, 0.3, 1.0]),
)
cube = UsdGeom.Cube.Define(stage, "/World/Quickstart/RawUsd")
cube.CreateSizeAttr(0.3)
cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 1.0, 1.0))
cube.AddRotateXYZOp().Set(Gf.Vec3f(0.0, 0.0, 45.0))
cube.AddScaleOp().Set(Gf.Vec3f(1.0, 1.5, 0.5))
print("Press Play: the cyan and blue cubes fall; visual cubes remain suspended.")
