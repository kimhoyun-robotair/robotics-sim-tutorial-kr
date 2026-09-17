"""Import a local URDF, or import the bundled Franka and run its RMPflow target task."""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--franka', action='store_true')
    parser.add_argument('--urdf', type=Path, default=Path(__file__).parent / 'arm.urdf')
    parser.add_argument('--steps', type=int, default=None, help='Execution limit; omitted or 0 keeps the GUI open')
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--output', type=Path, default=Path(__file__).parent / 'output')
    args = parser.parse_args()
    if args.steps is None:
        args.steps = 360 if args.headless else 0
    if args.steps < 0 or (args.headless and args.steps == 0):
        parser.error("--steps must be nonnegative; headless requires a positive limit")
    if not args.urdf.is_file():
        parser.error('an existing URDF is required')
    if args.output.exists():
        parser.error('Choose a new --output directory')
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
        from isaacsim.core.utils.extensions import enable_extension, get_extension_path_from_name
        # enable_extension은 이름으로 지정한 Kit 확장을 활성화하여 해당 기능과 명령을 사용할 수 있게 한다.
        # get_extension_path_from_name은 확장의 설치 경로를 찾아 내부 설정·예제 파일에 접근할 때 사용한다.
        from isaacsim.core.utils.stage import get_current_stage
        # get_current_stage는 현재 Isaac Sim에서 열려 있는 USD Stage를 반환한다.
        from isaacsim.core.utils.types import ArticulationAction
        # ArticulationAction은 관절 위치·속도·힘 명령과 적용할 관절 인덱스를 담는 자료형이다.
        # 이 값을 apply_action에 전달하면 관절 제어기가 해당 명령을 적용한다.
        from isaacsim.core.prims import SingleArticulation
        # SingleArticulation은 하나의 관절 구조를 감싸 관절 위치·속도·힘을 읽고 제어한다.
        enable_extension('isaacsim.asset.importer.urdf')
        from isaacsim.asset.importer.urdf import _urdf
        # _urdf는 URDF 가져오기 설정과 인터페이스를 제공하는 Isaac Sim 바인딩이다.
        world = World(stage_units_in_meters=1.0)
        # 기본 바닥을 Scene에 추가한다. 이 바닥은 강체가 떨어졌을 때 충돌할 표면이다.
        world.scene.add_default_ground_plane()
        source = args.urdf.resolve()
        if args.franka:
            source = Path(get_extension_path_from_name('isaacsim.asset.importer.urdf')) / 'data/urdf/robots/franka_description/robots/panda_arm_hand.urdf'
        # URDF 가져오기 옵션을 만든다. fix_base는 베이스 고정, self_collision은 로봇 내부 충돌 여부를 지정한다.
        config = _urdf.ImportConfig()
        config.fix_base = True
        config.make_default_prim = False
        config.self_collision = False
        config.distance_scale = 1.0
        config.density = 0.0
        # URDF 파일을 파싱해 링크·관절 모델을 얻는다. 이 단계에서 얻은 모델의 drive 설정을 수정할 수 있다.
        ok, model = omni.kit.commands.execute('URDFParseFile', urdf_path=str(source), import_config=config)
        if not ok or not model:
            raise RuntimeError(f'URDF parsing failed: {source}')
        for name in model.joints:
            model.joints[name].drive.strength = 1047.19751 if args.franka else 20.0
            model.joints[name].drive.damping = 52.35988 if args.franka else 1.0
        # 파싱한 URDF 모델과 가져오기 설정으로 Stage에 로봇을 생성하고 로봇 Prim 경로를 받는다.
        ok, robot_path = omni.kit.commands.execute(
            'URDFImportRobot', urdf_path=str(source), urdf_robot=model, import_config=config,
        )
        if not ok or not robot_path:
            raise RuntimeError('URDF import failed')
        if args.franka:
            from isaacsim.robot.manipulators.examples.franka.tasks import FollowTarget
            # FollowTarget은 로봇 팔이 따라갈 목표 Prim과 로봇을 구성하는 예제 Task이다.
            from isaacsim.robot.manipulators.examples.franka.controllers.rmpflow_controller import RMPFlowController
            # RMPFlowController는 목표 말단 자세를 추종하도록 RMPflow 기반 관절 명령을 계산하는 예제 제어기이다.
            # 작업을 World에 등록하여 장면 구성과 관측값·초기화를 World와 함께 관리한다.
            world.add_task(FollowTarget(name='follow', franka_prim_path=robot_path, franka_robot_name='arm', target_name='target'))
            # World를 초기화하고 등록된 객체의 물리 핸들을 준비한다. 관절·강체 상태를 읽기 전에 호출한다.
            world.reset()
            robot = world.scene.get_object('arm')
            controller = RMPFlowController(name='follow_controller', robot_articulation=robot)
        else:
            # 생성한 객체를 World의 Scene에 등록하여 이름으로 찾고 초기화할 수 있게 한다.
            robot = world.scene.add(SingleArticulation(prim_path=robot_path, name='arm'))
            controller = None
        get_current_stage().GetRootLayer().Export(str(args.output / 'imported.usda'))
        world.reset()
        joint_names = robot.dof_names
        # 현재 관절 위치를 읽는다. 회전 관절은 라디안, 직선 관절은 장면 길이 단위를 사용한다.
        joint_positions = robot.get_joint_positions().tolist()
        step = 0
        while app.is_running() and (args.steps == 0 or step < args.steps):
            if controller:
                # 등록된 작업이 제공하는 로봇·물체·목표의 관측값을 읽어 제어기에 전달한다.
                observations = world.get_observations()
                # 관절 제어기에 명령을 전달한다. 실제 관절의 움직임은 이후 물리 step에서 계산된다.
                robot.apply_action(controller.forward(
                    target_end_effector_position=observations['target']['position'],
                    target_end_effector_orientation=observations['target']['orientation'],
                ))
            else:
                robot.apply_action(ArticulationAction(joint_positions=np.array([0.5])))
            # 물리 시뮬레이션을 한 step 진행한다. render는 이 호출에서 렌더링도 수행할지 지정한다.
            world.step(render=not args.headless)
            if not app.is_running():
                break
            joint_positions = robot.get_joint_positions().tolist()
            step += 1
        report = {'source': str(source), 'prim_path': robot_path, 'joint_names': joint_names,
                  'joint_positions': joint_positions}
        (args.output / 'report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        # Isaac Sim 앱을 종료하고 Kit·렌더링 자원을 정리한다.
        app.close()


if __name__ == '__main__':
    main()
