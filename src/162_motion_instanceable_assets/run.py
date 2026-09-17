"""Xform 참조 계층으로 동일 geometry를 USD instance로 공유합니다."""
import argparse
from itertools import count
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--steps", type=int, default=None, help="GUI: omitted keeps the window open; headless default: 600")
    parser.add_argument("--output", type=Path, help="새 결과 디렉터리; 기존 경로는 거부")
    parser.add_argument('--count', type=int, default=4)
    parser.add_argument('--no-instancing', action='store_true')
    args = parser.parse_args()
    if args.steps is None and args.headless:
        args.steps = 600
    if args.steps is not None and args.steps < 1:
        parser.error("--steps must be positive")
    if args.output is None:
        parent = Path(__file__).resolve().parent / "output"
        parent.mkdir(exist_ok=True)
        output = Path(tempfile.mkdtemp(prefix="run_", dir=parent))
    else:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=False)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.
    app = SimulationApp({"headless": args.headless})
    try:
        from pxr import Usd, UsdGeom, Gf
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Usd는 Stage, Prim, 참조·variant 등의 USD 장면 구성 API를 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        if args.count < 1:
            raise ValueError('--count must be positive')
        # 두 파일을 함께 이동하면 상대 참조가 유지된다.
        mesh_stage = Usd.Stage.CreateNew(str(output / 'meshes.usda'))
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(mesh_stage, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(mesh_stage, UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        root = UsdGeom.Xform.Define(mesh_stage, '/Geometry')
        mesh_stage.SetDefaultPrim(root.GetPrim())
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        UsdGeom.Cube.Define(mesh_stage, '/Geometry/Cube').GetSizeAttr().Set(0.5)
        mesh_stage.GetRootLayer().Save()
        stage = Usd.Stage.CreateNew(str(output / 'instances.usda'))
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        world = UsdGeom.Xform.Define(stage, '/World')
        stage.SetDefaultPrim(world.GetPrim())
        rows = []
        for i in range(args.count):
            link = UsdGeom.Xform.Define(stage, f'/World/Robot_{i}/Link')
            link.AddTranslateOp().Set(Gf.Vec3d(i * 0.8, 0., 0.25))
            geometry = UsdGeom.Xform.Define(stage, f'/World/Robot_{i}/Link/Geometry').GetPrim()
            geometry.GetReferences().AddReference('./meshes.usda', '/Geometry')
            geometry.SetInstanceable(not args.no_instancing)
            rows.append({'path': str(geometry.GetPath()), 'is_instance': geometry.IsInstance(),
                         'prototype': str(geometry.GetPrototype().GetPath()) if geometry.IsInstance() else None,
                         'child_is_instance_proxy': stage.GetPrimAtPath(str(geometry.GetPath()) + '/Cube').IsInstanceProxy()})
        # 현재 루트 레이어의 변경을 원래 연결된 USD 파일에 저장한다.
        stage.GetRootLayer().Save()
        # USD 파일을 Kit의 현재 Stage로 연다.
        omni.usd.get_context().open_stage(str(output / 'instances.usda'))
        for step in count():
            if args.steps is not None and step >= args.steps:
                break
            if not app.is_running():
                break
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
        (output / 'instances.json').write_text(json.dumps(rows, indent=2))
        print(json.dumps(rows, indent=2))
        print('Output:', output)
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == "__main__":
    main()
