import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Working with USD")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )

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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.viewports import set_camera_view
        # set_camera_view는 뷰포트 카메라를 eye 위치에 두고 target 지점을 바라보도록 설정한다.
        from pxr import Gf, Usd, UsdGeom, UsdLux, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.

        # 새 USD 파일에 연결된 Stage를 만든다. Kit에서 현재 열어 둔 Stage와 별도로 구성할 수 있다.
        asset = Usd.Stage.CreateNew(str(output / "robot.usda"))
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(asset, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        robot = UsdGeom.Xform.Define(asset, "/mock_robot")
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        body = UsdGeom.Cube.Define(asset, "/mock_robot/body")
        body.CreateSizeAttr(0.6)
        body.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
        for name, y in (("wheel_left", 0.4), ("wheel_right", -0.4)):
            wheel = UsdGeom.Cylinder.Define(asset, "/mock_robot/" + name)
            wheel.CreateRadiusAttr(0.2)
            wheel.CreateHeightAttr(0.1)
            wheel.CreateAxisAttr("Y")
            wheel.AddTranslateOp().Set(Gf.Vec3d(0, y, 0.2))
        UsdGeom.Xform.Define(asset, "/World")
        # 중력 등 물리 시뮬레이션의 공통 설정을 저장할 PhysicsScene을 정의한다.
        UsdPhysics.Scene.Define(asset, "/World/PhysicsScene")
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(asset, "/World/Light").CreateIntensityAttr(1500)
        asset.SetDefaultPrim(robot.GetPrim())
        asset.GetRootLayer().Save()
        assembly = Usd.Stage.CreateNew(str(output / "assembly.usda"))
        UsdGeom.SetStageMetersPerUnit(assembly, 1.0)
        UsdGeom.SetStageUpAxis(assembly, UsdGeom.Tokens.z)
        root = UsdGeom.Xform.Define(assembly, "/World")
        assembly.SetDefaultPrim(root.GetPrim())
        UsdLux.DistantLight.Define(assembly, "/World/Light").CreateIntensityAttr(1500)
        UsdPhysics.Scene.Define(assembly, "/World/PhysicsScene")
        for name, x in (("RobotA", -1.0), ("RobotB", 1.0)):
            prim = UsdGeom.Xform.Define(assembly, "/World/" + name)
            prim.GetPrim().GetReferences().AddReference("robot.usda")
            prim.AddTranslateOp().Set(Gf.Vec3d(x, 0, 0))
        UsdGeom.Cube.Get(assembly, "/World/RobotB/body").CreateDisplayColorAttr(
            [Gf.Vec3f(0.2, 0.5, 1.0)]
        )
        assembly.GetRootLayer().Save()
        assembly.Export(str(output / "flattened.usda"))
        if assembly.GetPrimAtPath("/World/RobotA/PhysicsScene").IsValid():
            raise RuntimeError("Environment unexpectedly leaked through defaultPrim")
        # USD 파일을 읽어 Stage 객체를 얻는다. Kit 화면에 여는 open_stage와 구분된다.
        flattened = Usd.Stage.Open(str(output / "flattened.usda"))
        report = {
            "asset_default_prim": str(asset.GetDefaultPrim().GetPath()),
            "asset_prims": [str(p.GetPath()) for p in asset.Traverse()],
            "assembly_prims": [str(p.GetPath()) for p in assembly.Traverse()],
            "flattened_prims": [str(p.GetPath()) for p in flattened.Traverse()],
        }
        (output / "composition.json").write_text(json.dumps(report, indent=2))
        # USD 파일을 Kit의 현재 Stage로 연다.
        omni.usd.get_context().open_stage(str(output / "assembly.usda"))
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0.4])
        for step in count():
            if not app.is_running() or (args.steps is not None and step >= args.steps):
                break
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
        print(json.dumps(report, indent=2))
        print(f"Outputs: {output.resolve()}")
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
