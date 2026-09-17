"""Run genuine Isaac asset rules on authored defects, then verify focused repairs."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keep-defects', action='store_true', help='Leave the defective stage open for native GUI validation')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=120, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 0 or args.output.exists():
        parser.error('Use a new output directory and finite headless frame limit')
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
        enable_extension('isaacsim.asset.validation')
        from omni.asset_validator.core import ValidationEngine
        # ValidationEngine은 등록한 검사 규칙을 USD 자산에 적용하고 발견한 문제를 보고한다.
        from isaacsim.asset.validation.physics_rules import RigidBodyHasMassAPI, InvisibleCollisionMeshHasPurposeGuide
        # RigidBodyHasMassAPI는 강체에 질량 속성 API가 있는지 검사하는 자산 검증 규칙이다.
        # InvisibleCollisionMeshHasPurposeGuide는 보이지 않는 충돌 메시의 purpose 설정을 검사하는 규칙이다.
        from pxr import Gf, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        stage = omni.usd.get_context().get_stage()
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        root = UsdGeom.Xform.Define(stage, '/World')
        stage.SetDefaultPrim(root.GetPrim())
        # USD Stage에 Cube 형상을 직접 정의한다. 물리 동작이 필요하면 강체·충돌 API를 별도로 적용한다.
        cube = UsdGeom.Cube.Define(stage, '/World/DefectiveBody')
        cube.CreateSizeAttr(0.1)
        # Prim에 강체 API를 적용하여 물리 시뮬레이션이 자세와 속도를 계산할 수 있게 한다.
        UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
        # 형상 Prim에 충돌 API를 적용하여 접촉 계산에 참여하게 한다.
        UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        mass = UsdPhysics.MassAPI.Apply(cube.GetPrim())
        mass.CreateMassAttr(0.0)
        mass.CreateDiagonalInertiaAttr(Gf.Vec3f(0, 0, 0))
        mass.CreatePrincipalAxesAttr(Gf.Quatf(2.0))
        cube.CreateVisibilityAttr(UsdGeom.Tokens.invisible)
        engine = ValidationEngine(init_rules=False)
        engine.enable_rule(RigidBodyHasMassAPI)
        engine.enable_rule(InvisibleCollisionMeshHasPurposeGuide)
        before = [str(issue) for issue in engine.validate(stage).issues()]
        if not before:
            raise RuntimeError('The real validator did not report the intentionally authored defects')
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(args.output / 'before.usda'))
        report = {'enabled_rules': ['RigidBodyHasMassAPI', 'InvisibleCollisionMeshHasPurposeGuide'], 'before': before}
        if not args.keep_defects:
            mass.GetMassAttr().Set(1.0)
            mass.GetDiagonalInertiaAttr().Set(Gf.Vec3f(1/600, 1/600, 1/600))
            mass.GetPrincipalAxesAttr().Set(Gf.Quatf(1.0))
            cube.CreatePurposeAttr(UsdGeom.Tokens.guide)
            after = [str(issue) for issue in engine.validate(stage).issues()]
            report['after'] = after
            if after:
                raise RuntimeError(f'Focused repairs still fail the enabled rules: {after}')
            stage.GetRootLayer().Export(str(args.output / 'after.usda'))
        (args.output / 'validation.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
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
