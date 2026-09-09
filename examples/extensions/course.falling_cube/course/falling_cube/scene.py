"""USD 장면 생성만 담당한다. 앱, 타임라인, World singleton을 소유하지 않는다."""

from pxr import Gf, PhysxSchema, UsdGeom, UsdLux, UsdPhysics

ROOT = "/World/WorkflowDemo"


def build_scene(stage):
    if stage is None or not stage.GetRootLayer().anonymous:
        raise RuntimeError("기존 작업을 저장한 뒤 File > New로 빈 장면을 만든다.")
    foreign_paths = [
        str(prim.GetPath())
        for prim in stage.Traverse()
        if str(prim.GetPath()) != "/World"
        and not str(prim.GetPath()).startswith("/OmniverseKit_")
    ]
    if foreign_paths:
        raise RuntimeError(f"빈 장면이 필요하다. 기존 prim: {foreign_paths[:5]}")

    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.Xform.Define(stage, ROOT)
    scene = UsdPhysics.Scene.Define(stage, ROOT + "/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr(9.81)
    PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateTimeStepsPerSecondAttr(60)

    ground = UsdGeom.Cube.Define(stage, ROOT + "/Ground")
    ground.CreateSizeAttr(1.0)
    ground.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, -0.05))
    ground.AddScaleOp().Set(Gf.Vec3f(10.0, 10.0, 0.1))
    ground.CreateDisplayColorAttr([Gf.Vec3f(0.35, 0.35, 0.35)])
    UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

    cube = UsdGeom.Cube.Define(stage, ROOT + "/Cube")
    cube.CreateSizeAttr(0.2)
    cube.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 1.0))
    cube.CreateDisplayColorAttr([Gf.Vec3f(0.2, 0.7, 1.0)])
    UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
    UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(1.0)

    light = UsdLux.DomeLight.Define(stage, ROOT + "/Light")
    light.CreateIntensityAttr(700.0)
