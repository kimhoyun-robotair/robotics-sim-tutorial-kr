import argparse
from itertools import count
from datetime import datetime
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="USD Tools")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--steps", type=int, default=None, help="Positive step limit; omitted: keep GUI open (headless: 120 steps)"
    )
    parser.add_argument(
        "--output", type=Path, help="New output directory; existing paths are rejected"
    )
    parser.add_argument("--variant", choices=["red", "blue"], default="red")
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
        from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdUtils
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # Sdf는 USD 경로, 레이어, 속성 값의 자료형을 다룬다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdLux는 조명 Prim과 빛의 속성을 다룬다.
        # UsdUtils는 USD 파일의 의존성 처리와 패키징 등의 보조 도구를 다룬다.

        assets = output / "moved_assets"
        assets.mkdir()
        # 새 USD 파일에 연결된 Stage를 만든다. Kit에서 현재 열어 둔 Stage와 별도로 구성할 수 있다.
        asset = Usd.Stage.CreateNew(str(assets / "body.usda"))
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(asset, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(asset, UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        robot = UsdGeom.Xform.Define(asset, "/Robot")
        asset.SetDefaultPrim(robot.GetPrim())
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        cube = UsdGeom.Cube.Define(asset, "/Robot/Body")
        cube.CreateSizeAttr(0.5)
        variants = robot.GetPrim().GetVariantSets().AddVariantSet("finish")
        for name, color in (("red", Gf.Vec3f(1, 0, 0)), ("blue", Gf.Vec3f(0, 0, 1))):
            variants.AddVariant(name)
            variants.SetVariantSelection(name)
            with variants.GetVariantEditContext():
                cube.CreateDisplayColorAttr([color])
        variants.SetVariantSelection(args.variant)
        asset.GetRootLayer().Save()
        assembly = Usd.Stage.CreateNew(str(output / "broken.usda"))
        UsdGeom.SetStageMetersPerUnit(assembly, 1.0)
        UsdGeom.SetStageUpAxis(assembly, UsdGeom.Tokens.z)
        # 평행한 방향의 빛을 내는 DistantLight를 생성하고 강도를 설정한다.
        UsdLux.DistantLight.Define(assembly, "/World/Light").CreateIntensityAttr(1500)
        root = UsdGeom.Xform.Define(assembly, "/World")
        assembly.SetDefaultPrim(root.GetPrim())
        instance = UsdGeom.Xform.Define(assembly, "/World/Robot")
        instance.GetPrim().GetReferences().AddReference("old_assets/body.usda")
        assembly.GetRootLayer().Save()
        broken_has_body = assembly.GetPrimAtPath("/World/Robot/Body").IsValid()
        fixed_layer = Sdf.Layer.CreateNew(str(output / "repaired.usda"))
        fixed_layer.TransferContent(assembly.GetRootLayer())
        path_changes = []

        def repair(path):
            new = (
                path.replace("old_assets/", "moved_assets/", 1)
                if path.startswith("old_assets/")
                else path
            )
            if new != path:
                path_changes.append([path, new])
            return new

        UsdUtils.ModifyAssetPaths(fixed_layer, repair)
        fixed_layer.Save()
        # USD 파일을 읽어 Stage 객체를 얻는다. Kit 화면에 여는 open_stage와 구분된다.
        fixed = Usd.Stage.Open(fixed_layer)
        selection = fixed.GetPrimAtPath("/World/Robot").GetVariantSet("finish")
        selection.SetVariantSelection(args.variant)
        fixed.GetRootLayer().Save()
        if not fixed.GetPrimAtPath("/World/Robot/Body").IsValid():
            raise RuntimeError("Asset path repair failed")
        report = {
            "broken_has_body": broken_has_body,
            "repaired_has_body": fixed.GetPrimAtPath("/World/Robot/Body").IsValid(),
            "path_changes": path_changes,
            "variants": selection.GetVariantNames(),
            "selection": selection.GetVariantSelection(),
            "color": list(
                UsdGeom.Cube.Get(fixed, "/World/Robot/Body")
                .GetDisplayColorAttr()
                .Get()[0]
            ),
        }
        (output / "tools_report.json").write_text(json.dumps(report, indent=2))
        # USD 파일을 Kit의 현재 Stage로 연다.
        omni.usd.get_context().open_stage(str(output / "repaired.usda"))
        set_camera_view(eye=[4, 4, 3], target=[0, 0, 0])
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
