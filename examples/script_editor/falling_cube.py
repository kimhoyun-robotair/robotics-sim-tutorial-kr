"""Isaac Sim 5.1 Script Editor용. File > New로 만든 빈 장면에서 실행한다."""

import omni.timeline
import omni.usd
from pxr import Gf, PhysxSchema, UsdGeom, UsdLux, UsdPhysics

timeline = omni.timeline.get_timeline_interface()
stage = omni.usd.get_context().get_stage()
if stage is None or not stage.GetRootLayer().anonymous:
    raise RuntimeError("기존 작업을 저장한 뒤 File > New로 빈 장면을 만든다.")
if not timeline.is_stopped():
    raise RuntimeError("먼저 Stop을 누른다. Pause 상태에서는 장면을 재구성하지 않는다.")
foreign_paths = [
    str(prim.GetPath())
    for prim in stage.Traverse()
    if str(prim.GetPath()) != "/World"
    and not str(prim.GetPath()).startswith("/OmniverseKit_")
]
if foreign_paths:
    raise RuntimeError(f"빈 장면이 필요하다. 이미 존재하는 prim: {foreign_paths[:5]}")

UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)
world = UsdGeom.Xform.Define(stage, "/World")
stage.SetDefaultPrim(world.GetPrim())
root = "/World/WorkflowDemo"
UsdGeom.Xform.Define(stage, root)

scene = UsdPhysics.Scene.Define(stage, root + "/PhysicsScene")
scene.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
scene.CreateGravityMagnitudeAttr(9.81)
PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateTimeStepsPerSecondAttr(60)

ground = UsdGeom.Cube.Define(stage, root + "/Ground")
ground.CreateSizeAttr(1.0)
ground.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.05))
ground.AddScaleOp().Set(Gf.Vec3f(10.0, 10.0, 0.1))
ground.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.35, 0.35)])
UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

cube = UsdGeom.Cube.Define(stage, root + "/Cube")
cube.CreateSizeAttr(0.2)
cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 1.0))
cube.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.7, 1.0)])
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(1.0)

light = UsdLux.DomeLight.Define(stage, root + "/Light")
light.CreateIntensityAttr(700.0)

print("[course] Cube를 선택하고 F로 화면을 맞춘 뒤 Play를 누른다.")
print("[course] 정착 높이는 약 0.10 m이다. 정확한 값은 standalone 검사로 확인한다.")
