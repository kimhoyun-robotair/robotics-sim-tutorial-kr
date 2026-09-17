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
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({"headless": args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.viewports import set_camera_view
        # set_camera_view는 뷰포트 카메라를 eye 위치에 두고 target 지점을 바라보도록 설정한다.
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdLux
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdShade는 셰이더·재질과 형상에 대한 재질 연결을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.

        if not 0 < args.radius < 10:
            raise ValueError("--radius must be between 0 and 10")
        # 새 USD 파일에 연결된 Stage를 만든다. Kit에서 현재 열어 둔 Stage와 별도로 구성할 수 있다.
        stage = Usd.Stage.CreateNew(str(output / "hello.usda"))
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
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
        # Prim에 재질 연결 API를 적용한다. 이어지는 Bind에서 실제 사용할 재질을 지정한다.
        UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(mat)
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(stage, "/Light").CreateIntensityAttr(1500)
        layer = Sdf.Layer.CreateNew(str(output / "details.usda"))
        stage.GetRootLayer().subLayerPaths.append("details.usda")
        # with 블록 안에서 수행하는 USD 편집이 기록될 대상 레이어를 지정한다.
        with Usd.EditContext(stage, layer):
            sphere.GetPrim().CreateAttribute(
                "tutorial:label", Sdf.ValueTypeNames.String
            ).Set("layer-authored")
        layer.Save()
        # 현재 루트 레이어의 변경을 원래 연결된 USD 파일에 저장한다.
        stage.GetRootLayer().Save()
        properties = sphere.GetPrim().GetPropertyNames()
        # USD 변환을 누적 계산하는 캐시를 만든다. 부모 변환을 포함한 월드 변환을 얻을 수 있다.
        world_position = (
            UsdGeom.XformCache()
            .GetLocalToWorldTransform(sphere.GetPrim())
            .ExtractTranslation()
        )
        with Usd.EditContext(stage, stage.GetSessionLayer()):
            sphere.GetRadiusAttr().Set(args.radius * 2)
        session_radius = sphere.GetRadiusAttr().Get()
        stage.GetRootLayer().Save()
        # USD 파일을 읽어 Stage 객체를 얻는다. Kit 화면에 여는 open_stage와 구분된다.
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
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
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
        # USD 파일을 Kit의 현재 Stage로 연다.
        omni.usd.get_context().open_stage(str(output / "hello.usda"))
        set_camera_view(eye=[4, 4, 3], target=[1, 0, 1])
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
