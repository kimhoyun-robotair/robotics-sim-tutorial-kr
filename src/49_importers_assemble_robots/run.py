"""Assemble the installed UR10e and Allegro assets using the native 5.1 RobotAssembler."""
import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true', help='Prepare both references for the GUI workflow')
    parser.add_argument('--cancel', action='store_true', help='Begin and then cancel the session-layer assembly')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--steps', type=int, default=None, help='Kit update limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--frames', type=int, default=240, help='Legacy headless update limit when --steps is omitted; does not close the GUI')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = args.frames if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.frames < 0 or args.output.exists():
        parser.error('Require a new output directory and finite headless frame limit')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True)
    os.chdir(args.output)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        import omni.usd
        # omni.usd는 현재 Kit 애플리케이션의 USD 문맥에 접근하는 모듈이다.
        # get_context().get_stage()로 객체·조명 등이 들어 있는 현재 Stage를 얻는다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        from isaacsim.core.utils.stage import add_reference_to_stage, get_current_stage
        # add_reference_to_stage는 외부 USD 자산을 현재 Stage의 지정한 Prim 경로에 참조로 연결한다.
        # get_current_stage는 현재 Isaac Sim에서 열려 있는 USD Stage를 반환한다.
        from isaacsim.storage.native import get_assets_root_path
        # get_assets_root_path는 Isaac Sim 기본 자산의 루트 경로를 찾는다.
        # 반환 경로에 로봇·환경 USD의 상대 경로를 붙여 사용할 수 있다.
        from pxr import Gf, UsdGeom, UsdPhysics
        # pxr은 USD 장면을 직접 다루는 OpenUSD의 Python 바인딩이다.
        # Gf는 벡터·행렬·쿼터니언 등 위치와 회전을 계산하는 수학 자료형을 다룬다.
        # UsdGeom은 형상, 변환, 카메라와 장면 단위·축 설정을 다룬다.
        # UsdPhysics는 강체·충돌·관절·물리 재질의 USD 스키마를 다룬다.
        enable_extension('isaacsim.robot_setup.assembler')
        from isaacsim.robot_setup.assembler import RobotAssembler
        # RobotAssembler는 두 로봇 자산의 부착 프레임을 연결해 조립된 로봇을 구성한다.
        world = World(stage_units_in_meters=1.0)
        stage = get_current_stage()
        # 지정한 경로에 변환용 Xform Prim을 정의한다. 자식 객체를 묶어 함께 이동·회전시킬 때 사용할 수 있다.
        root = UsdGeom.Xform.Define(stage, '/World')
        stage.SetDefaultPrim(root.GetPrim())
        assets = get_assets_root_path()
        if assets is None:
            raise RuntimeError('Isaac 5.1 asset root unavailable')
        add_reference_to_stage(assets + '/Isaac/Robots/UniversalRobots/ur10e/ur10e.usd', '/World/ur10e')
        add_reference_to_stage(assets + '/Isaac/Robots/WonikRobotics/AllegroHand/allegro_hand_instanceable.usd', '/World/allegro_hand')
        base_mount = '/World/ur10e/ee_link'
        hand_mount = '/World/allegro_hand/allegro_mount'
        for path in (base_mount, hand_mount):
            if not stage.GetPrimAtPath(path).IsValid():
                raise RuntimeError(f'Missing 5.1 mounting frame: {path}')
        # 로봇 조립기를 만들어 베이스와 부착할 로봇의 프레임을 연결할 준비를 한다.
        assembler = RobotAssembler()
        if not args.prepare_only:
            assembler.begin_assembly(stage, '/World/ur10e', base_mount, '/World/allegro_hand', hand_mount, 'Gripper', 'allegro_hand')
            if args.cancel:
                assembler.cancel_assembly()
            else:
                # Prim의 변환 연산에 접근한다. AddTranslateOp·AddRotateXYZOp·AddScaleOp로 이동·회전·스케일을 기록할 수 있다.
                hand = UsdGeom.Xformable(stage.GetPrimAtPath('/World/allegro_hand'))
                matrix = hand.GetLocalTransformation()
                for axis in (Gf.Vec3d(0, 0, 1), Gf.Vec3d(0, 1, 0)):
                    matrix = Gf.Matrix4d().SetRotate(Gf.Rotation(axis, -90)) * matrix
                hand.MakeMatrixXform().Set(matrix)
                assembler.assemble()
                # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
                world.reset()
        preview_steps = args.steps or 240
        frame = 0
        while app.is_running() and frame < preview_steps:
            if not args.prepare_only and not args.cancel:
                # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                world.step(render=not args.headless)
            else:
                # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
                # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
                app.update()
            frame += 1
        if not app.is_running():
            return
        if not args.prepare_only and not args.cancel:
            base_transform = omni.usd.get_world_transform_matrix(stage.GetPrimAtPath(base_mount))
            attach_transform = omni.usd.get_world_transform_matrix(stage.GetPrimAtPath(hand_mount))
            distance = (base_transform.ExtractTranslation() - attach_transform.ExtractTranslation()).GetLength()
            print('Measured mounting-frame separation, meters:', distance)
            world.stop()
            assembler.finish_assemble()
        # Stage의 Prim 계층을 순회하여 형상·관절·스키마 정보를 검사한다.
        joints = [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdPhysics.FixedJoint)]
        # Stage의 루트 레이어를 USD 파일로 내보낸다. 참조 자산 자체를 모두 복사하는 것은 아니다.
        stage.GetRootLayer().Export(str(args.output / 'assembled.usda'))
        (args.output / 'report.json').write_text(json.dumps({'fixed_joint_paths': joints, 'cancelled': args.cancel}, indent=2))
        print('Authored fixed joints:', joints)
        if args.steps == 0:
            while app.is_running():
                app.update()
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
