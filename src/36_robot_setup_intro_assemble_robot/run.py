"""Prepare this lesson's editable USD stage and keep Isaac Sim open for the GUI lab."""
import argparse
import json
from pathlib import Path


def build_fixture(stage):

    from pxr import Gf, UsdGeom, UsdLux, UsdPhysics, PhysxSchema, PhysicsSchemaTools
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
    # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
    # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
    # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
    # PhysxSchema는 PhysX 전용 물리 설정을 USD Prim에 기록하는 스키마를 다룬다.
    # PhysicsSchemaTools는 바닥 등 기본 물리 장면을 구성하는 보조 함수를 다룬다.
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    # USD 장면에서 위쪽으로 사용할 축을 지정한다.
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    # 중력 등 물리 시뮬레이션의 공통 설정을 저장할 PhysicsScene을 정의한다.
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(9.8)
    physics = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    physics.CreateEnableGPUDynamicsAttr(False)
    physics.CreateBroadphaseTypeAttr("MBP")
    PhysicsSchemaTools.addGroundPlane(stage, "/World/Ground", "Z", 25.0, Gf.Vec3f(0), Gf.Vec3f(0.35))
    # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
    ambient = UsdLux.DistantLight.Define(stage, "/World/DefaultLight")
    ambient.CreateIntensityAttr(300)
    light = UsdLux.SphereLight.Define(stage, "/World/SpotLight")
    light.AddTranslateOp().Set(Gf.Vec3d(0, 0, 7))
    light.CreateColorAttr(Gf.Vec3f(0.5, 1.0, 0.5))
    light.CreateIntensityAttr(1e6)
    light.CreateRadiusAttr(0.05)
    shape = UsdLux.ShapingAPI.Apply(light.GetPrim())
    shape.CreateShapingConeAngleAttr(45)
    shape.CreateShapingConeSoftnessAttr(0.05)

    from pxr import UsdShade
    # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
    # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
    material = UsdShade.Material.Define(stage, "/World/Looks/WheelPhysics")
    physics_material = UsdPhysics.MaterialAPI.Apply(material.GetPrim())
    physics_material.CreateStaticFrictionAttr(0.8)
    physics_material.CreateDynamicFrictionAttr(0.6)
    physics_material.CreateRestitutionAttr(0.0)
    body = UsdGeom.Xform.Define(stage, "/World/body")
    body.AddTranslateOp().Set(Gf.Vec3d(0, 0, 1))
    # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
    cube = UsdGeom.Cube.Define(stage, "/World/body/body")
    cube.CreateSizeAttr(1.0)
    cube.AddScaleOp().Set(Gf.Vec3f(1, 2, 0.5))
    cube.CreateDisplayColorAttr([Gf.Vec3f(0.15, 0.4, 0.9)])
    for prim in [cube.GetPrim()]:
        # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
        UsdPhysics.RigidBodyAPI.Apply(prim)
        # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
        UsdPhysics.CollisionAPI.Apply(prim)
    for name, x in [("wheel_left", 1.5), ("wheel_right", -1.5)]:
        wheel = UsdGeom.Xform.Define(stage, "/World/" + name)
        wheel.AddTranslateOp().Set(Gf.Vec3d(x, 0, 1))
        wheel.AddRotateXYZOp().Set(Gf.Vec3f(90, 0, 0))
        cylinder = UsdGeom.Cylinder.Define(stage, f"/World/{name}/{name}")
        cylinder.CreateRadiusAttr(0.5)
        cylinder.CreateHeightAttr(1.0)
        cylinder.CreateDisplayColorAttr([Gf.Vec3f(0.12)])
        prim = cylinder.GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.CollisionAPI.Apply(prim)
        # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
        UsdShade.MaterialBindingAPI.Apply(prim).Bind(material, materialPurpose="physics")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", default='', help="Official asset-root-relative path, absolute local USD, or URL")
    parser.add_argument("--stage", type=Path, help="Open your saved result instead of creating a fresh lesson stage")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("output"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="UI update limit; omitted or 0 keeps the GUI open; headless requires a positive value")
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("headless requires positive --steps; GUI stays open when --steps is omitted")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from pxr import Sdf, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        context = omni.usd.get_context()
        if args.stage:
            path = args.stage.expanduser().resolve(strict=True)
            if not context.open_stage(str(path)):
                raise RuntimeError(f"Cannot open {path}")
            stage = context.get_stage()
            # Author changes into a new local layer even when inspecting an earlier result.
            source = str(path)
        else:
            source = args.asset
        layer = Sdf.Layer.CreateNew(str(output / "stage.usda"))
        if source:
            if source.startswith("/Isaac/"):
                root = get_assets_root_path()
                if not root:
                    raise RuntimeError("Isaac Sim 5.1 assets root is unavailable")
                source = root + source
            if not Sdf.Layer.FindOrOpen(source):
                raise RuntimeError(f"Cannot resolve source USD: {source}")
            layer.subLayerPaths = [source]
        layer.Save()
        if not context.open_stage(str(output / "stage.usda")):
            raise RuntimeError("Failed to open the local lesson layer")
        stage = context.get_stage()
        if not source:
            build_fixture(stage)
        for _ in range(1200):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            if not context.is_stage_loading():
                break
        if context.is_stage_loading():
            raise RuntimeError("Stage loading did not finish after 1200 updates")
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        report = {"source": source or "local procedural fixture", "meters_per_unit": UsdGeom.GetStageMetersPerUnit(stage),
                  "up_axis": str(UsdGeom.GetStageUpAxis(stage)),
                  "rigid_bodies": [str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)],
                  "joints": [str(p.GetPath()) for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)],
                  "articulation_roots": [str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.ArticulationRootAPI)]}
        if len(list(stage.Traverse())) < 2:
            raise RuntimeError("The lesson stage has no usable content")
        # 현재 루트 레이어의 변경을 원래 연결된 USD 파일에 저장한다.
        stage.GetRootLayer().Save()
        (output / "initial_inventory.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        print("Follow TUTORIAL.md, save your edits to the local root layer, then close the window.")
        updates = 0
        while app.is_running() and (args.steps == 0 or updates < args.steps):
            app.update()
            updates += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
