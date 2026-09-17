"""Export one local robot in visual-only, visual+collision, and collision-only variants."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=120, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 1 or args.output.exists():
        parser.error('positive frames and a new output directory are required')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from pxr import Gf, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        enable_extension('isaacsim.asset.exporter.urdf')
        from nvidia.srl.from_usd.to_urdf import UsdToUrdf
        stage = omni.usd.get_context().get_stage()
        # USD 좌표 한 단위가 몇 미터인지 지정하여 장면의 길이 단위를 맞춘다.
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        # USD 장면에서 위쪽으로 사용할 축을 지정한다.
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        root = UsdGeom.Xform.Define(stage, '/Robot')
        stage.SetDefaultPrim(root.GetPrim())
        for name, position, mass, diagonal in [
            ('base', (0, 0, 0), 1.0, (0.0067, 0.0067, 0.0067)),
            ('link', (0, 0, 0.2), 0.5, (0.0034, 0.0034, 0.0034)),
        ]:
            body = UsdGeom.Xform.Define(stage, f'/Robot/{name}')
            body.AddTranslateOp().Set(Gf.Vec3d(*position))
            # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
            UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
            mass_api = UsdPhysics.MassAPI.Apply(body.GetPrim())
            mass_api.CreateMassAttr(mass)
            mass_api.CreateDiagonalInertiaAttr(Gf.Vec3f(*diagonal))
            mass_api.CreatePrincipalAxesAttr(Gf.Quatf(1.0))
            # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
            mesh = UsdGeom.Cube.Define(stage, f'/Robot/{name}/shape')
            mesh.CreateSizeAttr(0.2)
            # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
            UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        # 두 몸체 사이의 회전 관절을 정의한다. 연결 대상과 관절 축·제한을 이어서 지정한다.
        joint = UsdPhysics.RevoluteJoint.Define(stage, '/Robot/hinge')
        joint.CreateBody0Rel().SetTargets(['/Robot/base'])
        joint.CreateBody1Rel().SetTargets(['/Robot/link'])
        joint.CreateAxisAttr('Y')
        joint.CreateLocalPos0Attr(Gf.Vec3f(0, 0, 0.2))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0, 0, 0))
        joint.CreateLowerLimitAttr(-60.0)
        joint.CreateUpperLimitAttr(60.0)
        sphere = UsdGeom.Sphere.Define(stage, '/Robot/link/experiment_sphere')
        sphere.CreateRadiusAttr(0.03)
        sphere.AddTranslateOp().Set(Gf.Vec3d(0.13, 0, 0))
        summary = {}
        for mode in ('visual', 'both', 'collision'):
            if mode != 'visual':
                UsdPhysics.CollisionAPI.Apply(sphere.GetPrim())
            sphere.CreateVisibilityAttr(UsdGeom.Tokens.invisible if mode == 'collision' else UsdGeom.Tokens.inherited)
            destination = args.output / mode
            destination.mkdir()
            # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
            stage.GetRootLayer().Export(str(destination / 'source.usda'))
            target = destination / 'robot.urdf'
            UsdToUrdf(stage, root='/Robot').save_to_file(
                str(target), mesh_dir='meshes', mesh_path_prefix='./', use_uri_file_prefix=False,
            )
            tree = ElementTree.parse(target)
            summary[mode] = {key: len(tree.findall(f'.//{key}')) for key in ('link', 'joint', 'visual', 'collision')}
        (args.output / 'counts.json').write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        frame = 0
        while app.is_running() and (args.steps == 0 or frame < args.steps):
            # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
            # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
            app.update()
            frame += 1
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
