"""Measure a real imported joint's step/sine response or open it in the native Gain Tuner."""
import argparse
import csv
import math
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kp', type=float, default=20.0)
    parser.add_argument('--kd', type=float, default=1.0)
    parser.add_argument('--wave', choices=('step', 'sine'), default='step')
    parser.add_argument('--steps', type=int, default=None, help='Execution limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--interactive', action='store_true', help='Native GUI controls the robot; --steps still limits execution')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 600 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if args.kp <= 0 or args.kd < 0 or args.output.exists() or (args.interactive and args.headless):
        parser.error('Require positive kp, nonnegative kd, new output, and visible interactive mode')
    args.output.mkdir(parents=True)
    from isaacsim import SimulationApp
    # SimulationApp은 Python에서 Isaac Sim의 Kit 애플리케이션을 시작하고 갱신·종료하는 클래스이다.
    # headless=True는 창 없이 실행한다는 뜻이며, omni와 Isaac Sim 확장 모듈은 앱 생성 후 import한다.

    app = SimulationApp({'headless': args.headless})
    try:
        import numpy as np
        import omni.kit.commands
        # omni.kit.commands는 이름으로 등록된 Kit 명령을 실행하는 모듈이다.
        # execute에 명령 이름과 인자를 전달해 Prim 생성·가져오기 등의 작업을 수행한다.
        from isaacsim.core.api import World
        # World는 Stage의 객체와 작업을 관리하고 물리·렌더링 시간 간격, 초기화, 시뮬레이션 진행을 제어한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.core.utils.extensions import enable_extension
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        enable_extension('isaacsim.asset.importer.urdf')
        enable_extension('isaacsim.robot_setup.gain_tuner')
        from isaacsim.asset.importer.urdf import _urdf
        # _urdf는 URDF 가져오기 설정과 인터페이스를 제공하는 Isaac Sim 바인딩이다.
        world = World(stage_units_in_meters=1.0, physics_dt=1/120, rendering_dt=1/60)
        # URDF 가져오기 옵션을 만든다. fix_base는 베이스 고정, self_collision은 로봇 내부 충돌 여부를 지정한다.
        config = _urdf.ImportConfig()
        config.fix_base = True
        config.default_drive_type = _urdf.UrdfJointTargetType.JOINT_DRIVE_POSITION
        source = str((Path(__file__).parent / 'arm.urdf').resolve())
        # URDF 파일을 파싱해 링크·관절 모델을 얻는다. 이 단계에서 얻은 모델의 drive 설정을 수정할 수 있다.
        ok, model = omni.kit.commands.execute('URDFParseFile', urdf_path=source, import_config=config)
        if not ok or not model:
            raise RuntimeError('Could not parse local arm')
        model.joints['shoulder'].drive.strength = args.kp
        model.joints['shoulder'].drive.damping = args.kd
        # 파싱한 URDF 모델과 가져오기 설정으로 Stage에 로봇을 생성하고 로봇 Prim 경로를 받는다.
        ok, robot_path = omni.kit.commands.execute('URDFImportRobot', urdf_path=source, urdf_robot=model, import_config=config)
        if not ok:
            raise RuntimeError('Could not import local arm')
        # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
        robot = world.scene.add(SingleArticulation(prim_path=robot_path, name='arm'))
        # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
        world.reset()
        if args.interactive:
            step = 0
            while app.is_running() and (args.steps == 0 or step < args.steps):
                # Kit의 한 프레임을 갱신하여 렌더링·이벤트·비동기 작업을 처리한다.
                # 물리 진행 여부는 현재 타임라인의 재생 상태와 설정에 따라 달라진다.
                app.update()
                step += 1
        else:
            with (args.output / 'response.csv').open('x', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['time_s', 'target_rad', 'actual_rad', 'velocity_rad_s', 'error_rad'])
                step = 0
                while app.is_running() and (args.steps == 0 or step < args.steps):
                    t = step / 120
                    target = (0.5 if t >= 0.5 else 0.0) if args.wave == 'step' else 0.3 * math.sin(2*math.pi*0.5*t)
                    # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                    robot.apply_action(ArticulationAction(joint_positions=np.array([target]), joint_velocities=np.array([0.0])))
                    # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
                    world.step(render=not args.headless)
                    if not app.is_running():
                        break
                    # 현재 관절 위치를 읽는다. 회전 관절은 라디안, 직선 관절은 장면 길이 단위를 사용한다.
                    actual = float(robot.get_joint_positions()[0])
                    # 현재 관절 속도를 읽는다. 배열 순서는 로봇의 관절 순서에 대응한다.
                    velocity = float(robot.get_joint_velocities()[0])
                    writer.writerow([t, target, actual, velocity, target-actual])
                    step += 1
            print('Measured response:', args.output / 'response.csv')
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
